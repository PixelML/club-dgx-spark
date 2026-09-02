#!/usr/bin/env python3
"""Regenerate the GLM-5.3-Flash NVFP4 dual-Spark throughput chart.

Reads decode-matrix-mtp.json (both measured passes) and writes PNG + SVG to
../../assets/charts/ relative to this file. No network, no GPU.

    python3 make_chart.py
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RECEIPT = os.path.join(HERE, "decode-matrix-mtp.json")
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "assets", "charts"))
STEM = "2026-08-27-glm-5.3-flash-nvfp4-2node-tp2-vllm-throughput"


def main():
    with open(RECEIPT) as f:
        receipt = json.load(f)

    series = []
    for key, label, color in (
        ("validation_2026_08_27", "Validation pass (3-run medians)", "#1f77b4"),
        ("revalidation_2026_08_27", "Fresh revalidation pass (3-run medians)", "#d62728"),
    ):
        rows = receipt["passes"][key]["rows"]
        x = [r["concurrency"] for r in rows]
        y = [r["median_agg_tok_s"] for r in rows]
        lo = [r["range"][0] for r in rows]
        hi = [r["range"][1] for r in rows]
        series.append((x, y, lo, hi, label, color))

    fig, ax = plt.subplots(figsize=(8.0, 4.8), dpi=150)
    for x, y, lo, hi, label, color in series:
        ax.plot(x, y, marker="o", color=color, label=label)
        ax.fill_between(x, lo, hi, color=color, alpha=0.15, linewidth=0)

    best = max(
        (r["median_agg_tok_s"], r["concurrency"], name)
        for name, p in receipt["passes"].items()
        for r in p["rows"]
    )
    ax.annotate(
        f"{best[0]:.2f} tok/s @ x{best[1]} ({'validation' if 'validation' in best[2] else 'fresh'} pass)",
        xy=(best[1], best[0]),
        xytext=(best[1] - 3.4, best[0] + 2.5),
        fontsize=9,
        arrowprops={"arrowstyle": "->", "color": "0.35"},
    )

    ax.set_title(
        "GLM-5.3-Flash NVFP4 on 2x DGX Spark (vLLM, Ray TP=2, MTP-4)\n"
        "client-observed aggregate output throughput, fixed 256-token decode, temp 0",
        fontsize=11,
    )
    ax.set_xlabel("Concurrency (simultaneous fixed-256-token streams)")
    ax.set_ylabel("Aggregate output throughput (tok/s)")
    ax.set_xticks(series[0][0])
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()

    os.makedirs(OUT_DIR, exist_ok=True)
    for ext in ("png", "svg"):
        out = os.path.join(OUT_DIR, f"{STEM}.{ext}")
        fig.savefig(out)
        print("wrote", out)


if __name__ == "__main__":
    main()
