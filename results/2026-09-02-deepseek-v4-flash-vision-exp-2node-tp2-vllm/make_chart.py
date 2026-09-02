#!/usr/bin/env python3
"""Build the tok/s vs concurrency chart from evidence-repo numbers
(canonical merged main + normalized PR-pending row). Not executed by the
notebook; run once to produce the committed PNG/SVG."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

canonical_c = [1, 6]
canonical_y = [36.9, 112.7]

normalized_c = [1, 2, 4, 8, 16]
normalized_y = [48.71, 70.98, 71.50, 94.93, 106.79]

fig, ax = plt.subplots(figsize=(7.5, 4.8))
ax.plot(canonical_c, canonical_y, marker="o", label="Canonical (merged main)")
ax.plot(normalized_c, normalized_y, marker="s", label="Normalized protocol (PR pending)")
ax.set_xlabel("Concurrency (number of simultaneous requests)")
ax.set_ylabel("Aggregate decode throughput (tokens/second, sum across requests)")
ax.set_title("DeepSeek-V4-Flash-Vision-Exp, 2x DGX Spark, vLLM TP=2\nAggregate decode tok/s vs. concurrency (evidence repo)")
ax.set_xscale("log", base=2)
ax.set_xticks(canonical_c + normalized_c)
ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
ax.grid(True, alpha=0.3)
ax.legend()
fig.tight_layout()

import os
REPO_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
out_png = os.path.join(REPO_ROOT, "assets/charts/2026-09-02-deepseek-v4-flash-vision-exp-2node-tp2-throughput.png")
out_svg = os.path.join(REPO_ROOT, "assets/charts/2026-09-02-deepseek-v4-flash-vision-exp-2node-tp2-throughput.svg")
fig.savefig(out_png, dpi=150)
fig.savefig(out_svg)
print("wrote", out_png)
print("wrote", out_svg)
