#!/usr/bin/env python3
"""Serve-side benchmark harness for one speculative-decoding arm.

This is the published, sanitized form of the protocol used for every arm in
this notebook: one frozen 100-prompt fixture, concurrency 1, greedy, fixed
256-token outputs, counted from the engine's final usage object.

It is deliberately engine-agnostic: point it at any OpenAI-compatible
endpoint. The endpoint base URL comes from SPARK_ENDPOINT; never hardcode an
address here.

One arm = one server boot with one speculative configuration. vLLM resolves
the speculative config once in VllmConfig at boot; there is no per-request
override, so arms cannot be interleaved against one server.

Usage:
    SPARK_ENDPOINT=http://<your-host>:8000/v1 \
    python run_served_eval.py --fixture eval100.jsonl --arm dflash-b5 \
        --out DFLASH_B5/run1.json --repeats 2
"""
from __future__ import annotations

import argparse
import json
import os
import time

import requests


def load_fixture(path):
    """Fixture rows: {"id": str, "workload": "code"|"math"|"chat", "prompt": str}."""
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def one_request(endpoint, model, prompt, max_tokens, timeout=600):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "seed": 42,
        "max_tokens": max_tokens,
        # Fixed-length outputs make every arm decode exactly the same number of
        # tokens. It also means these numbers say nothing about natural
        # response latency or useful-token throughput.
        "ignore_eos": True,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    t0 = time.perf_counter()
    r = requests.post(f"{endpoint}/chat/completions", json=payload, timeout=timeout)
    r.raise_for_status()
    body = r.json()
    wall = time.perf_counter() - t0
    # Always count from the final usage object, never from stream-event count.
    completion = body["usage"]["completion_tokens"]
    return {
        "wall_s": wall,
        "completion_tokens": completion,
        "tok_per_s": completion / wall,
        "finish_reason": body["choices"][0].get("finish_reason"),
    }


def spec_counters(endpoint):
    """Accepted length from the engine's own acceptance counters.

    Scraped from /metrics so accepted length is the engine's number, not a
    client-side inference. Returns None when the endpoint exposes no
    speculative counters (for example the spec-off arm).
    """
    try:
        text = requests.get(f"{endpoint.rsplit('/v1', 1)[0]}/metrics", timeout=30).text
    except requests.RequestException:
        return None
    wanted = ("spec_decode_num_accepted_tokens", "spec_decode_num_drafts",
              "spec_decode_num_draft_tokens")
    out = {}
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        for key in wanted:
            if line.startswith(key):
                out[key] = float(line.rsplit(" ", 1)[-1])
    return out or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--arm", required=True, help="label only; the arm is decided by how the server was booted")
    ap.add_argument("--model", default=os.environ.get("SPARK_MODEL", "qwen3.8-flash-next"))
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--repeats", type=int, default=2, help="whole-fixture repeats within one boot")
    ap.add_argument("--warmup", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    endpoint = os.environ.get("SPARK_ENDPOINT", "").rstrip("/")
    if not endpoint:
        raise SystemExit("Set SPARK_ENDPOINT to your own OpenAI-compatible base URL.")

    fixture = load_fixture(args.fixture)
    for row in fixture[: args.warmup]:
        one_request(endpoint, args.model, row["prompt"], args.max_tokens)

    before = spec_counters(endpoint)
    records = []
    for rep in range(args.repeats):
        for row in fixture:
            m = one_request(endpoint, args.model, row["prompt"], args.max_tokens)
            m.update(id=row["id"], workload=row["workload"], repeat=rep)
            records.append(m)
    after = spec_counters(endpoint)

    total_tokens = sum(r["completion_tokens"] for r in records)
    total_wall = sum(r["wall_s"] for r in records)
    accepted_length = None
    if before and after:
        drafts = after.get("spec_decode_num_drafts", 0) - before.get("spec_decode_num_drafts", 0)
        accepted = after.get("spec_decode_num_accepted_tokens", 0) - before.get("spec_decode_num_accepted_tokens", 0)
        if drafts:
            # +1 for the bonus token emitted by every verified pass.
            accepted_length = accepted / drafts + 1.0

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump({
            "arm": args.arm,
            "protocol": {
                "concurrency": 1, "temperature": 0, "seed": 42,
                "max_tokens": args.max_tokens, "ignore_eos": True,
                "thinking": False, "repeats": args.repeats,
                "fixture": os.path.basename(args.fixture), "n_prompts": len(fixture),
            },
            "aggregate_tok_s": total_tokens / total_wall,
            "accepted_length": accepted_length,
            "records": records,
        }, fh, indent=2)
    print(f"{args.arm}: aggregate {total_tokens / total_wall:.3f} tok/s over {len(records)} requests")


if __name__ == "__main__":
    main()
