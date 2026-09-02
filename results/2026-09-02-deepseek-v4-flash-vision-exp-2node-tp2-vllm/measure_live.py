#!/usr/bin/env python3
"""LIVE measurement harness for the DeepSeek-V4-Flash-Vision-Exp DGX Spark
notebook. Run once against the private endpoint (VISION_ENDPOINT env var)
to produce the JSON receipts committed under this results directory. Not
imported by the notebook itself; the notebook reads the receipts back.
"""
import json
import os
import sys
import time

import requests

BASE = os.environ["VISION_ENDPOINT"].rstrip("/")
MODEL = os.environ.get("MODEL_ID", "apollo-deepseek-v4-flash-vision-exp")
HERE = os.path.dirname(os.path.abspath(__file__))
TS = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def post(payload, timeout=180):
    t0 = time.time()
    r = requests.post(f"{BASE}/chat/completions", json=payload, timeout=timeout)
    dt = time.time() - t0
    r.raise_for_status()
    return r.json(), dt


def save(name, obj):
    path = os.path.join(HERE, name)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
    print("wrote", path)


# 1. /v1/models --------------------------------------------------------
r = requests.get(f"{BASE}/models", timeout=30)
r.raise_for_status()
models = r.json()
save("live_models.json", {"captured_utc": TS, "response": models})

# 2. Deterministic text --------------------------------------------------
det_payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "Reply with exactly one word: the color of a clear daytime sky."}],
    "temperature": 0,
    "max_tokens": 200,
}
det_resp, det_dt = post(det_payload)
save("live_deterministic_text.json", {
    "captured_utc": TS,
    "request": det_payload,
    "response": det_resp,
    "wall_time_s": round(det_dt, 3),
})

# 3. Golden image fixtures (regenerated corpus) -------------------------
fixtures = json.load(open(os.path.join(HERE, "images", "image_fixtures.json")))
image_results = []
for fx in fixtures:
    payload = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": fx["question"]},
                {"type": "image_url", "image_url": {"url": fx["data_url"]}},
            ],
        }],
        "temperature": 0,
        "max_tokens": 200,
    }
    resp, dt = post(payload)
    text = resp["choices"][0]["message"].get("content") or ""
    reasoning = resp["choices"][0]["message"].get("reasoning") or ""
    full_text = (text + " " + reasoning).lower()
    keyword_pass = any(kw.lower() in full_text for kw in fx["expected_keywords"])
    image_results.append({
        "id": fx["id"],
        "question": fx["question"],
        "expected_keywords": fx["expected_keywords"],
        "file": fx["file"],
        "response_text": text,
        "response_reasoning": reasoning,
        "finish_reason": resp["choices"][0].get("finish_reason"),
        "usage": resp.get("usage"),
        "wall_time_s": round(dt, 3),
        "keyword_pass": keyword_pass,
    })
    print(fx["id"], "PASS" if keyword_pass else "FAIL", text[:60])
save("live_golden_images.json", {"captured_utc": TS, "results": image_results})

# 4. Negative control: same questions, no image --------------------------
neg_payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": fixtures[0]["question"]}],
    "temperature": 0,
    "max_tokens": 200,
}
neg_resp, neg_dt = post(neg_payload)
save("live_negative_control.json", {
    "captured_utc": TS,
    "note": "same color question as img01_solid_red, no image attached",
    "request": neg_payload,
    "response": neg_resp,
    "wall_time_s": round(neg_dt, 3),
})

# 5. Wrong-image control: ask the img01 (red) question but attach the blue image
wrong_payload = {
    "model": MODEL,
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": fixtures[0]["question"]},
            {"type": "image_url", "image_url": {"url": fixtures[1]["data_url"]}},
        ],
    }],
    "temperature": 0,
    "max_tokens": 200,
}
wrong_resp, wrong_dt = post(wrong_payload)
wrong_text = (wrong_resp["choices"][0]["message"].get("content") or "").lower()
save("live_wrong_image_control.json", {
    "captured_utc": TS,
    "note": "img01 question (expects red) sent with img02 (blue) attached; model should answer blue, not red",
    "request": wrong_payload,
    "response": wrong_resp,
    "wall_time_s": round(wrong_dt, 3),
    "answered_blue_not_red": "blue" in wrong_text and "red" not in wrong_text,
})

# 6. C1 x3 greedy 400-token measurement -----------------------------------
c1_prompt = "Write a detailed technical explanation of how speculative decoding works in large language model inference, covering the draft model, verification, and acceptance rate."
c1_runs = []
for rep in range(3):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": c1_prompt}],
        "temperature": 0,
        "max_tokens": 400,
        "ignore_eos": True,
    }
    resp, dt = post(payload)
    usage = resp.get("usage", {})
    ctoks = usage.get("completion_tokens", 0)
    c1_runs.append({
        "rep": rep,
        "latency_s": round(dt, 3),
        "completion_tokens": ctoks,
        "finish_reason": resp["choices"][0].get("finish_reason"),
        "tok_per_s": round(ctoks / dt, 2) if dt > 0 else None,
    })
    print("c1 rep", rep, c1_runs[-1])
lat_sorted = sorted(r["latency_s"] for r in c1_runs)
tok_sorted = sorted(r["tok_per_s"] for r in c1_runs)
save("live_c1_x3.json", {
    "captured_utc": TS,
    "prompt": c1_prompt,
    "max_tokens": 400,
    "runs": c1_runs,
    "median_latency_s": lat_sorted[1],
    "median_tok_per_s": tok_sorted[1],
})

# 7. Warm TTFT x3 (streaming) ---------------------------------------------
ttft_runs = []
for rep in range(3):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "In one sentence, what is a DGX Spark?"}],
        "temperature": 0,
        "max_tokens": 100,
        "stream": True,
    }
    t0 = time.time()
    ttft = None
    with requests.post(f"{BASE}/chat/completions", json=payload, stream=True, timeout=60) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            if ttft is None:
                ttft = time.time() - t0
            if line.strip() == b"data: [DONE]":
                break
    ttft_runs.append({"rep": rep, "ttft_s": round(ttft, 3) if ttft else None})
    print("ttft rep", rep, ttft_runs[-1])
ttft_sorted = sorted(r["ttft_s"] for r in ttft_runs)
save("live_ttft_x3.json", {
    "captured_utc": TS,
    "runs": ttft_runs,
    "median_ttft_s": ttft_sorted[1],
})

print("DONE", TS)
