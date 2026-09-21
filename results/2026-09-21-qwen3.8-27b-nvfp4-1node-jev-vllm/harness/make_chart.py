#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Chart for the Qwen3.8-27B NVFP4 Jev-endpoint experiment on DGX Spark.

Reads only committed receipts under ../receipts and writes the figure to
assets/charts/ as PNG and SVG:

  left   annotations per minute across the production run (the pilot's own
         pacing), with the 94 s engine sample window marked
  right  the same Jev contract on one GB10 (NVFP4) vs one CMP 170HX
         (W4A16 GPTQ): mean answer per engine request, with prefill rate,
         steady annotations/min and mean power annotated

  python make_chart.py
"""

import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
RECEIPTS = HERE.parent / "receipts"
CHARTS = HERE.parents[2] / "assets" / "charts"
STEM = "2026-09-21-qwen3.8-27b-nvfp4-1node-jev-vllm"

# committed receipts of the CMP 170HX W4A16 run of the same contract
CMP = {
    "e2e_mean_ms": 12032.5, "tok_s": 1952.1, "ann_per_min": 76.6,
    "power_w": 178.4, "src": "club-170hx results/2026-09-20-qwen3.8-27b-w4a16-jev-1card-vllm",
}


def receipt(rel):
    with open(RECEIPTS / rel) as f:
        return json.load(f)


def main():
    summary = receipt("load/load-summary.json")
    delta = receipt("load/metrics-delta.json")
    minutes = receipt("load/load-ledger-minutes.json")["minutes"]
    led = summary["ledger"]
    win = summary["engine_window"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.0),
                                   gridspec_kw={"width_ratios": [1.35, 1.0]})

    # --- left: annotations per minute ---------------------------------------
    def minute_index(m):
        h, mm = m["minute_utc"].split(":")
        return int(h) * 60 + int(mm)

    base = minute_index(minutes[0])
    xs = [minute_index(m) - base for m in minutes]
    ys = [m["reads"] for m in minutes]
    ax1.plot(xs, ys, color="#0ca678", lw=1.4)
    ax1.fill_between(xs, 0, ys, color="#0ca678", alpha=0.15)
    mean_rate = led["annotations_per_h_avg"] / 60
    ax1.axhline(mean_rate, color="#e8590c", lw=1.2, ls="--",
                label=f"run average {mean_rate:.0f}/min")
    steady = led["steady_last30_annotations_per_min"]
    ax1.axhline(steady, color="#1f6feb", lw=1.2, ls=":",
                label=f"steady state {steady:.0f}/min (last 30 min)")
    end_min = led["end_utc"][11:16]
    h, mm = end_min.split(":")
    win_end = int(h) * 60 + int(mm) - base
    ax1.axvspan(win_end - win["window_s"] / 60, win_end, color="#9c36b5",
                alpha=0.18, label=f"engine sample window ({win['window_s']:.0f} s)")
    ax1.set_xlabel("Minute of the run (UTC minutes since first annotation, 2026-09-21)")
    ax1.set_ylabel("Annotations completed per minute")
    ax1.set_title(f"{led['annotations']:,} annotations in "
                  f"{led['span_h']*60:.0f} min, {led['failed']} failures\n"
                  f"engine prefill {win['prompt_tok_s']:.0f} tok/s in the "
                  f"sample window at {summary['gpu_window']['power_w_mean']:.0f} W")
    ax1.grid(alpha=0.3)
    ax1.legend(fontsize=8, loc="lower right")
    ax1.set_ylim(bottom=0)

    # --- right: same contract, one GB10 vs one CMP 170HX ---------------------
    bars = [
        ("GB10 NVFP4\n(this notebook)", delta["e2e_mean_ms"] / 1000.0, "#0ca678",
         f"{win['prompt_tok_s']:.0f} tok/s · {summary['gpu_window']['power_w_mean']:.0f} W · "
         f"{led['steady_last30_annotations_per_min']:.0f} ann/min"),
        ("CMP 170HX W4A16\n(same contract, same pool)", CMP["e2e_mean_ms"] / 1000.0,
         "#5c8dff", f"{CMP['tok_s']:.0f} tok/s · {CMP['power_w']:.0f} W · "
                    f"{CMP['ann_per_min']:.0f} ann/min"),
    ]
    ax2.bar(range(len(bars)), [b[1] for b in bars],
            color=[b[2] for b in bars], width=0.55)
    for i, (_, v, _, note) in enumerate(bars):
        ax2.annotate(f"{v:.1f} s", xy=(i, v), xytext=(0, 4),
                     textcoords="offset points", ha="center",
                     fontsize=11, fontweight="bold")
        ax2.annotate(note, xy=(i, v), xytext=(0, -18),
                     textcoords="offset points", ha="center", fontsize=8,
                     color="white")
    ax2.set_xticks(range(len(bars)))
    ax2.set_xticklabels([b[0] for b in bars], fontsize=8.5)
    ax2.set_ylabel("Mean answer per engine request (s)")
    ax2.set_title("Same Jev contract, one card each\n"
                  "every GB10 window read ≤ 10 s")
    ax2.grid(alpha=0.3, axis="y")
    ax2.set_ylim(0, max(b[1] for b in bars) * 1.22)

    fig.suptitle("Qwen3.8-27B NVFP4 no-train Jev endpoint on 1× DGX Spark (GB10), vLLM",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    for ext in ("png", "svg"):
        fig.savefig(CHARTS / f"{STEM}.{ext}", dpi=150)
    print("wrote", CHARTS / f"{STEM}.png")
    print("wrote", CHARTS / f"{STEM}.svg")


if __name__ == "__main__":
    main()
