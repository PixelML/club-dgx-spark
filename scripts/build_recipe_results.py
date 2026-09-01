#!/usr/bin/env python3
"""Build and validate a club recipe summary from benchmark JSON evidence."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any


SUMMARY_FIELDS = (
    "metric",
    "x",
    "request_count",
    "sample_count",
    "prompt_tokens",
    "completion_tokens",
    "duration_seconds",
    "tok_s",
    "range_low_tok_s",
    "range_high_tok_s",
    "token_basis",
)
EXPECTED_CONCURRENCY = (1, 4, 8, 16)
EXPECTED_PREFILL_TARGETS = (1024, 4096, 16384)


def _positive_number(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be numeric") from error
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{field} must be finite and positive")
    return number


def _close(actual: float, expected: float, *, tolerance: float = 0.002) -> bool:
    return math.isclose(actual, expected, rel_tol=tolerance, abs_tol=0.02)


def validate_run(run: dict[str, Any]) -> None:
    if run.get("schema_version") != 1:
        raise ValueError("run schema_version must be 1")
    if run.get("evidence_class") != "MEASURED":
        raise ValueError("run evidence_class must be MEASURED")

    decode = run.get("decode")
    if not isinstance(decode, list):
        raise ValueError("decode evidence must be a list")
    concurrencies = tuple(int(item.get("concurrency", 0)) for item in decode)
    if concurrencies != EXPECTED_CONCURRENCY:
        raise ValueError(f"decode concurrency must be {EXPECTED_CONCURRENCY}")
    for item in decode:
        concurrency = int(item["concurrency"])
        request_count = int(item.get("request_count", concurrency))
        completion_tokens = int(item.get("completion_tokens", 0))
        wall_seconds = _positive_number(item.get("wall_seconds"), "wall_seconds")
        aggregate_tps = _positive_number(item.get("aggregate_tps"), "aggregate_tps")
        if request_count != concurrency or completion_tokens <= 0:
            raise ValueError("decode request/token accounting is incomplete")
        if not _close(aggregate_tps, completion_tokens / wall_seconds, tolerance=0.006):
            raise ValueError("decode tok/s does not match usage.completion_tokens / wall time")

    prefill = run.get("prefill")
    if not isinstance(prefill, list):
        raise ValueError("prefill evidence must be a list")
    targets = tuple(int(item.get("target_prompt_tokens", 0)) for item in prefill)
    if targets != EXPECTED_PREFILL_TARGETS:
        raise ValueError(f"prefill targets must be {EXPECTED_PREFILL_TARGETS}")
    for group in prefill:
        samples = group.get("samples")
        if not isinstance(samples, list) or len(samples) < 3:
            raise ValueError("each prefill target requires at least three samples")
        for sample in samples:
            prompt_tokens = int(sample.get("prompt_tokens", 0))
            ttft_seconds = _positive_number(sample.get("ttft_seconds"), "ttft_seconds")
            client_tps = _positive_number(
                sample.get("client_prefill_tps"), "client_prefill_tps"
            )
            if prompt_tokens <= 0:
                raise ValueError("prefill usage.prompt_tokens must be positive")
            # The pinned harness stores TTFT to four decimals after calculating
            # the rate from its unrounded timer. Permit only that rounding loss.
            if not _close(client_tps, prompt_tokens / ttft_seconds):
                raise ValueError(
                    "prefill tok/s does not match usage.prompt_tokens / client TTFT"
                )


def summary_rows(run: dict[str, Any]) -> list[dict[str, str]]:
    validate_run(run)
    rows: list[dict[str, str]] = []
    for item in run["decode"]:
        rows.append(
            {
                "metric": "decode",
                "x": str(int(item["concurrency"])),
                "request_count": str(int(item["request_count"])),
                "sample_count": "1",
                "prompt_tokens": "",
                "completion_tokens": str(int(item["completion_tokens"])),
                "duration_seconds": f'{float(item["wall_seconds"]):.4f}'.rstrip("0").rstrip("."),
                "tok_s": f'{float(item["aggregate_tps"]):.2f}',
                "range_low_tok_s": "",
                "range_high_tok_s": "",
                "token_basis": "final usage.completion_tokens / level wall time",
            }
        )

    for group in run["prefill"]:
        samples = sorted(group["samples"], key=lambda sample: float(sample["client_prefill_tps"]))
        median_sample = samples[len(samples) // 2]
        rates = [float(sample["client_prefill_tps"]) for sample in samples]
        rows.append(
            {
                "metric": "prefill",
                "x": str(int(group["target_prompt_tokens"])),
                "request_count": "1",
                "sample_count": str(len(samples)),
                "prompt_tokens": str(int(median_sample["prompt_tokens"])),
                "completion_tokens": "1",
                "duration_seconds": f'{float(median_sample["ttft_seconds"]):.4f}',
                "tok_s": f'{float(median_sample["client_prefill_tps"]):.2f}',
                "range_low_tok_s": f"{min(rates):.2f}",
                "range_high_tok_s": f"{max(rates):.2f}",
                "token_basis": "final usage.prompt_tokens / client TTFT (median-rate sample)",
            }
        )
    return rows


def _json_lines(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{path}:{line_number}: expected one JSON object per line") from error
        if not isinstance(record, dict):
            raise ValueError(f"{path}:{line_number}: JSON line must be an object")
        records.append(record)
    return records


def run_from_jsonl(decode_path: Path, prefill_path: Path, evidence: str) -> dict[str, Any]:
    decode = []
    for record in _json_lines(decode_path):
        if "benchmark" not in record:
            continue
        item = dict(record["benchmark"])
        item["request_count"] = int(item["concurrency"])
        decode.append(item)

    prefill = []
    pending_samples: list[dict[str, Any]] | None = None
    for record in _json_lines(prefill_path):
        if "samples" in record:
            if pending_samples is not None:
                raise ValueError("prefill JSONL contains unpaired samples")
            pending_samples = record["samples"]
        elif "summary" in record:
            if pending_samples is None:
                raise ValueError("prefill JSONL summary is missing preceding samples")
            prefill.append(
                {
                    "target_prompt_tokens": int(record["summary"]["target_prompt_tokens"]),
                    "samples": pending_samples,
                }
            )
            pending_samples = None
    if pending_samples is not None:
        raise ValueError("prefill JSONL ends with unpaired samples")

    run = {
        "schema_version": 1,
        "evidence_class": "MEASURED",
        "evidence": evidence,
        "protocol": {
            "decode": (
                "identical coding prompt, 192 maximum output tokens, "
                "reasoning_effort=low"
            ),
            "prefill": (
                "unique randomized prefix, one output token, three measured "
                "samples per target"
            ),
            "runtime": (
                "SGLang TP=2 across two DGX Spark nodes with NEXTN/MTP"
            ),
        },
        "token_accounting": {
            "decode": "final API usage.completion_tokens",
            "prefill": "final streamed API usage.prompt_tokens",
        },
        "decode": decode,
        "prefill": prefill,
    }
    validate_run(run)
    return run


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_run(path: Path, run: dict[str, Any]) -> None:
    validate_run(run)
    _atomic_text(path, json.dumps(run, indent=2, sort_keys=True) + "\n")


def write_summary(path: Path, run: dict[str, Any]) -> None:
    rows = summary_rows(run)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=SUMMARY_FIELDS, lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> None:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--recorded-run", type=Path)
    source.add_argument("--decode-jsonl", type=Path)
    parser.add_argument("--prefill-jsonl", type=Path)
    parser.add_argument("--evidence", default="")
    parser.add_argument("--raw-output", type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()

    if args.recorded_run:
        run = json.loads(args.recorded_run.read_text(encoding="utf-8"))
        validate_run(run)
    else:
        if not args.prefill_jsonl or not args.raw_output or not args.evidence:
            parser.error(
                "live capture requires --prefill-jsonl, --raw-output, and --evidence"
            )
        run = run_from_jsonl(args.decode_jsonl, args.prefill_jsonl, args.evidence)
        write_run(args.raw_output, run)

    write_summary(args.summary, run)
    print(f"validated {len(run['decode'])} decode and {len(run['prefill'])} prefill levels")


if __name__ == "__main__":
    main()
