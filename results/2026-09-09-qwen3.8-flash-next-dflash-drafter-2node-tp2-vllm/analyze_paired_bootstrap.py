#!/usr/bin/env python3
"""Paired stratified bootstrap over prompts for two arms of run_served_eval.py.

Why this and not the obvious thing: an earlier analysis of this lane compared
POOLED PER-REQUEST MEDIANS and read the overlapping intervals as "no
distinguishable gain". That was wrong. The headline quantity is AGGREGATE
throughput, and overlap between two independently bootstrapped intervals is
not a paired difference test. Resample PROMPTS, keep both arms' records for
the resampled prompt together, average repeats within a prompt first, and
difference the aggregates.

The interval this produces is conditional on the boots that were run: it
excludes boot-to-boot variability and any selection over blocks. Run two
boots per arm and say so.

Usage:
    python analyze_paired_bootstrap.py --a MTP_K3/run1.json --b DFLASH_B5/run1.json \
        --workload all --resamples 4000
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict


def by_prompt(path, workload):
    with open(path) as fh:
        recs = json.load(fh)["records"]
    grouped = defaultdict(lambda: {"tokens": 0.0, "wall": 0.0, "workload": None})
    for r in recs:
        if workload != "all" and r["workload"] != workload:
            continue
        g = grouped[r["id"]]
        g["tokens"] += r["completion_tokens"]
        g["wall"] += r["wall_s"]
        g["workload"] = r["workload"]
    return grouped


def aggregate(groups, ids):
    tokens = sum(groups[i]["tokens"] for i in ids)
    wall = sum(groups[i]["wall"] for i in ids)
    return tokens / wall


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="baseline arm receipt")
    ap.add_argument("--b", required=True, help="candidate arm receipt")
    ap.add_argument("--workload", default="all", choices=["all", "code", "math", "chat"])
    ap.add_argument("--resamples", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    ga, gb = by_prompt(args.a, args.workload), by_prompt(args.b, args.workload)
    ids = sorted(set(ga) & set(gb))
    if len(ids) != len(ga) or len(ids) != len(gb):
        raise SystemExit("arms do not cover the same prompts; the fixture must be frozen across arms")

    point = (aggregate(gb, ids) / aggregate(ga, ids) - 1.0) * 100.0

    # Stratify by workload so every resample keeps the fixture's 33/33/34 mix.
    strata = defaultdict(list)
    for i in ids:
        strata[ga[i]["workload"]].append(i)

    rng = random.Random(args.seed)
    deltas = []
    for _ in range(args.resamples):
        draw = [rng.choice(members) for members in strata.values() for _ in members]
        deltas.append((aggregate(gb, draw) / aggregate(ga, draw) - 1.0) * 100.0)
    deltas.sort()
    lo = deltas[int(0.025 * len(deltas))]
    hi = deltas[int(0.975 * len(deltas)) - 1]
    print(f"workload={args.workload}  n_prompts={len(ids)}")
    print(f"aggregate throughput delta: {point:+.2f}%  conditional 95% CI [{lo:+.2f}%, {hi:+.2f}%]")


if __name__ == "__main__":
    main()
