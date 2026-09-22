#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build the DGX Spark Jev-endpoint notebook from a cell spec.

The notebook is generated rather than hand-edited so the receipts it reads and
the numbers it states stay in one place.

  python build_notebook.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / "notebooks" / "2026-09-21-qwen3.8-27b-nvfp4-1node-jev-vllm.ipynb"

CELLS = [
    ("md", r"""# Qwen3.8-27B (NVFP4) as a no-train Jev endpoint on 1× DGX Spark (GB10) — 1node, vLLM

| Metric (source) | Value |
|---|---|
| Decode at c=1 | untested here — judge reads generate no answer token; generation is the [CMP 170HX notebook](https://github.com/PixelML/club-170hx/blob/main/notebooks/2026-08-30-qwen3.8-27b-w4a16-dflash2-1card-vllm.ipynb)'s subject |
| Best aggregate (measured, this notebook) | 99.4 annotations/min steady — 12-client pilot, 5 engine reads per annotation |
| Prefill (measured, this notebook) | 2,573 tok/s in the 94 s engine window · 2,582 tok/s ledger average |
| Answer, e2e per engine request (measured) | 6.86 s mean under load · **every window read ≤ 10 s** · idle-c=1 not measurable (the pilot never stops) |

![production run and cross-platform answer time](../assets/charts/2026-09-21-qwen3.8-27b-nvfp4-1node-jev-vllm.png)

```
hf download nvidia/Qwen3.8-27B-NVFP4 --local-dir <weights>
```

Receipts: [`results/2026-09-21-qwen3.8-27b-nvfp4-1node-jev-vllm/`](../results/2026-09-21-qwen3.8-27b-nvfp4-1node-jev-vllm/) · Jev contract: [kishida's `jev` docs](https://github.com/kishida/llama.cpp/blob/jev/docs/jev.md) · sibling 170HX run: [club-170hx notebook](https://github.com/PixelML/club-170hx/blob/main/notebooks/2026-09-20-qwen3.8-27b-w4a16-jev-1card-vllm.ipynb)
"""),
    ("md", r"""This notebook shows that **Qwen3.8-27B (NVFP4) can serve as a no-train Jev
endpoint** on one DGX Spark (GB10, SM121, arm64): one prompt evaluation per
read returns the label distribution — the sampled token is discarded and the
answer is not generated. Nothing is trained: the stock NVFP4 checkpoint is
served read-only, everything that shapes the answer is read-time
(`allowed_token_ids`, option order, a temperature divisor applied after the
read).

The numbers are **not probes**: on 2026-09-21 the endpoint carried the first
production workload — the same LLM-as-judge annotation pilot that ran on the
CMP 170HX ([sibling notebook](https://github.com/PixelML/club-170hx/blob/main/notebooks/2026-09-20-qwen3.8-27b-w4a16-jev-1card-vllm.ipynb),
same pool, same contract, five permutation reads per annotation). In 43
minutes it completed **4,295 annotations with zero failures** at **2,582
tok/s ledger-average prefill** while drawing **83 W** — against the 170HX
card's 1,952 tok/s at 178 W for the identical job.

The Jev contract is documented in the
[`jev` branch of kishida's llama.cpp fork](https://github.com/kishida/llama.cpp/blob/jev/docs/jev.md);
the serving recipe lineage (`--logprobs-mode processed_logprobs`, prefix
caching, `--max-logprobs` ≥ label count) is the one established for this
checkpoint family on the CMP 170HX. What is ours here is the GB10 data point
and the production-load receipts.
"""),
    ("code", r"""# --- Status cell -------------------------------------------------------
# LIVE = False replays the committed receipts under results/<experiment>/.
# LIVE = True runs the same harness against a running endpoint whose URL
# comes from the environment. Never commit a notebook executed with LIVE = True.
import os

EXPERIMENT = "2026-09-21-qwen3.8-27b-nvfp4-1node-jev-vllm"
RESULTS_DIR = os.path.join("..", "results", EXPERIMENT)
RECEIPTS = os.path.join(RESULTS_DIR, "receipts")
LIVE = False
JEV_ENDPOINT_ENV_VAR = "JEV_UPSTREAM"  # the vLLM OpenAI server

print(f"experiment : {EXPERIMENT}")
print(f"receipts   : {RECEIPTS}")
print(f"LIVE       : {LIVE}")
if LIVE:
    if not os.environ.get(JEV_ENDPOINT_ENV_VAR):
        raise RuntimeError(f"LIVE=True but {JEV_ENDPOINT_ENV_VAR} is not set")
    print("endpoint   : from the environment (not printed)")
"""),
    ("code", r"""# --- Helpers ------------------------------------------------------------
import json
import os

def receipt(name):
    with open(os.path.join(RECEIPTS, name)) as f:
        return json.load(f)

from IPython.display import display, Markdown

def render_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    display(Markdown("\n".join(lines)))
"""),
    ("md", r"""## 1. TL;DR

**Verdict: the no-train classification contract runs at production rate on
one GB10, faster per card than the 170HX run of the same job.** 4,295
annotations in 43 minutes, zero failures, engine prefill 2,573 tok/s in the
sampled window at an 83 W mean. The mean answer per engine request under the
12-client pilot is 6.86 s and every sampled read finished within 10 s — the
wait is queue, not compute. No training anywhere: read-time choices only, and
the one quantity that could have been fitted (a temperature) already failed
leave-one-out on the 170HX receipts at n=42, so this stack ships at T=1 too.

Two findings a vLLM-on-GB10 host has to know, each with a receipt:

1. **`logprobs_mode` decides whether the label distribution exists.** The
   serve line runs `--logprobs-mode processed_logprobs` — vLLM's default
   computes logprobs before `allowed_token_ids`, so a label-masked read
   returns no usable label set. Same finding as the 170HX run; the flags
   transfer unchanged to GB10.
2. **The prefix cache hits 0.0% on this traffic.** The engine queried
   241,840 prompt tokens in the sample window and reused nothing: per-item
   judge prompts share no leading KV blocks, so every read pays its full
   prefill. Do not bank on prefix caching for judge workloads without
   checking the hit rate.

The scale comparison, stated with its caveat: this is NVFP4 on GB10 against
W4A16 GPTQ on the 170HX — quantization and platform change together, so read
it as *the same job on two club cards*, not a kernel-level A/B. Prefill
1.32×, steady annotations/min 1.30×, mean answer 1.75× faster, power 0.47×.

### Pins

From `receipts/env.json` (versions and the resolved engine configuration from
the serve log).

### Protocol

Every read is one `POST /v1/completions` with `max_tokens=1`: the prompt is
evaluated once and the logprobs of the first generated position are the label
distribution; the sampled token is discarded. Each annotation fires five
permutation reads (option rotations averaged per Jev's `permutations`
semantics), in flight together. The pilot ran from a private lane; its
per-annotation ledger stays outside this repository — the committed receipts
are aggregates (per-minute counts, engine `/metrics` deltas over a 94 s
window, `nvidia-smi` telemetry, one sequential single-client probe).
"""),
    ("code", r"""env = receipt("env.json")
pins = [
    ("Model (served)", f"{env['model']['checkpoint']} @ `{env['model']['revision'][:12]}…`"),
    ("Architecture", env["model"]["architecture"]),
    ("Quantization", f"{env['model']['quantization']} — {env['model']['quantization'].split()[0]} GEMM kernel: CutlassNvFp4LinearKernel"),
    ("vLLM / torch / CUDA", f"{env['runtime']['vllm']} / {env['runtime']['torch']}"),
    ("Driver", env["driver"]),
    ("Hardware", env["hardware"]),
    ("Topology", "1node, single GPU, no speculative decoding"),
    ("Serving shape", f"max_model_len {env['serve']['max_model_len']}, max_num_seqs {env['serve']['max_num_seqs']}, "
                      f"max_logprobs {env['serve']['max_logprobs']}, gpu_memory_utilization {env['serve']['gpu_memory_utilization']}, "
                      "prefix caching on"),
    ("Jev read mode", "`--logprobs-mode processed_logprobs` (not the default)"),
    ("Weights held by the engine", f"{env['model']['weights_resident_gib']} GiB (load {env['model']['model_load_s']} s)"),
]
render_table(["Pin", "Value"], pins)
"""),
    ("md", r"""## 2. Visible results

Every table and the chart are computed from the committed receipts.
"""),
    ("md", r"""### 2.1 The production run

The pilot samples the same 80,000-item pool the 170HX run used and speaks the
same contract. 12 client workers; five permutation reads per annotation; the
run was still going when the receipts were frozen — every number below is the
frozen aggregate.
"""),
    ("code", r"""load = receipt("load/load-summary.json")
led = load["ledger"]
rows = [
    ["Annotations", f"{led['annotations']:,}"],
    ["Failures", str(led['failed'])],
    ["Wall time (UTC)", f"{led['start_utc'][11:16]}-{led['end_utc'][11:16]} = {led['span_h']*60:.0f} min"],
    ["Prompt tokens", f"{led['input_tokens_total']:,} (mean {led['input_tokens_mean']:.0f}/annotation, "
                      f"p95 {led['input_tokens_p95']})"],
    ["Billed", f"${led['usd_billed']:.2f} (pilot-internal tariff, not a list price)"],
    ["Rate, run average", f"{led['annotations_per_h_avg']:,.0f} annotations/h"],
    ["Rate, steady (last 30 min)", f"{led['steady_last30_annotations_per_min']:.1f}/min, "
                                   f"{led['steady_last30_input_tokens_per_s']:.0f} tok/s prefill"],
]
render_table(["Production run, one GB10", "Value"], rows)

print("per UTC hour:")
rows = [[h["hour_utc"], f"{h['annotations']:,}", f"{h['mean_input_tokens']:.0f}"]
        for h in load["per_hour_utc"]]
render_table(["Hour", "Annotations", "Mean prompt tokens"], rows)
"""),
    ("code", r"""win = load["engine_window"]
d = win  # engine window block inside the summary
g = load["gpu_window"]
p = load["probe_single_client"]
rows = [
    ["Engine requests finished", f"{win['requests']:.0f} in {win['window_s']:.0f} s ({win['req_per_s']} req/s)"],
    ["Requests per annotation", f"{win['requests_per_annotation']} (the 5 permutation reads)"],
    ["Generated tokens per request", f"{win['gen_per_req']} (max_tokens=1; the sample is discarded)"],
    ["Prompt tokens processed", f"{win['prompt_tokens']:,.0f} -> {win['prompt_tok_s']} tok/s prefill"],
    ["Answer, mean e2e", f"{win['e2e_mean_ms']:,.0f} ms per request"],
    ["Answer bounds", ", ".join(f"{v:.0f} ≤ {k.replace('within_','').replace('_s',' s')}" for k, v in win['e2e_bounds'].items())
                      + " — no read exceeded 10 s"],
    ["Prefix cache hit rate", f"{win['prefix_hit_pct']}% on {win['prompt_tokens']:,.0f} queried tokens"],
    ["In flight at sample", f"{win['running_t1']:.0f} running / {win['waiting_t1']:.0f} waiting"],
    ["GPU over the telemetry window", f"{g['power_w_mean']} W mean ({g['power_w_min']}-{g['power_w_max']}), "
                                      f"SM {g['sm_util_pct_mean']:.0f}%, SM clock "
                                      f"{g['sm_clock_mhz_range'][0]:.0f}-{g['sm_clock_mhz_range'][1]:.0f} MHz"],
]
render_table(["Engine window under load", "Value"], rows)

littles = (win['running_t1'] + win['waiting_t1']) / win['req_per_s']
print(f"Little's law check: {win['running_t1'] + win['waiting_t1']:.0f} requests in flight / "
      f"{win['req_per_s']} req/s = {littles:.1f} s expected wait+compute; "
      f"measured mean {win['e2e_mean_ms']/1000:.2f} s")
print(f"single-client probe under load (synthetic ~1.5k-token prompt, sequential, n={len(p['latencies_ms'])}): "
      f"mean {p['mean_ms']:.0f} ms, min {p['min_ms']}, max {p['max_ms']}")
"""),
    ("md", r"""![production run and cross-platform answer time](../assets/charts/2026-09-21-qwen3.8-27b-nvfp4-1node-jev-vllm.png)

**The answer, and where the wait lives.** The mean engine request answers in
6.86 s and none of the 796 sampled reads exceeded 10 s — against 12.03 s mean
on the 170HX for the identical job. The card is not the bottleneck at this
queue depth: 49 requests in flight at 8.47 req/s predicts 5.8 s by Little's
law, close to the measured mean, and the engine prefill rate (2,573 tok/s) is
within 2% of the ledger-side steady rate — the pilot keeps the card fed. The
five permutation reads of one annotation are in flight together, so an
annotation's answer is one request's wait, not five.

**No-train, on native FP4 silicon.** The checkpoint is NVIDIA's NVFP4
quantization and the engine runs it on the Cutlass NVFP4 GEMM path — the FP4
format GB10 accelerates natively. Against the 170HX W4A16 run of the same
contract and pool: prefill 1.32×, steady annotations/min 1.30×, mean answer
1.75× faster, at 47% of the card power — roughly 50 J of card energy per
annotation vs ~140 J (computed from the two receipts' power and rate means).
Quantization and platform change together across this comparison; treat it as
the same job on two club cards, not a kernel A/B.

**Prefix cache: measured 0.0% here too.** Same result as the 170HX run, now
on different silicon and quantization: per-item judge prompts share no
leading KV blocks. Judge traffic does not get prefix caching for free.

## 3. Reproduce

**Hardware.** One NVIDIA DGX Spark (GB10, SM121, arm64, 128 GB unified
memory). No second node, no interconnect. The run drew 83 W at the wall of
the GPU package (mean over 46 samples at 2 s; GB10 does not expose GPU or
memory temperature through `nvidia-smi` — recorded as N/A in the telemetry).

**Weights.** NVIDIA's NVFP4 quantization, 19.95 GiB resident:

```bash
hf download nvidia/Qwen3.8-27B-NVFP4 --local-dir <weights>
```

**Serve.** vLLM 0.29.0 (arm64 build), torch 2.13.0+cu130, driver 580.173.02:

```bash
FLASHINFER_DISABLE_VERSION_CHECK=1 <venv>/bin/vllm serve <weights> \
  --served-model-name qwen3.8-27b-jev \
  --port <port> \
  --gpu-memory-utilization 0.35 \
  --max-model-len 8192 \
  --max-num-seqs 128 \
  --max-logprobs 128 \
  --logprobs-mode processed_logprobs \
  --enable-prefix-caching
```

`--logprobs-mode processed_logprobs` is required (finding 1). Boot: model
load 19.95 GiB in 163 s, engine init and startup about 2.9 minutes total.

**Measurements.** `harness/` carries the chart and notebook builders
(`make_chart.py`, `build_notebook.py`). The production receipts are frozen
aggregates of the pilot's ledger plus engine `/metrics` deltas over a 94 s
window and `nvidia-smi` telemetry; the collection recipe is the same as the
170HX bundle's (`collect_load_receipts.py` there), pointed at this endpoint.
Point `JEV_UPSTREAM` at your own endpoint and set `LIVE = True` to re-run the
harness against it.

A smoke run of the read path is one request:

```bash
curl -s http://127.0.0.1:<port>/v1/completions -H 'Content-Type: application/json' -d '{
  "model": "qwen3.8-27b-jev",
  "prompt": "Rate this support passage for urgency from 1 to 5. Passage: <text>",
  "max_tokens": 1, "temperature": 1.0, "top_p": 1.0, "logprobs": 5}'
```

## 4. Appendix

<details>
<summary>Failed attempts, hardware observations, safety notes, and limitations (click to expand)</summary>

### How the run came about

The pilot first ran this checkpoint family as W4A16 on the CMP 170HX; the
Spark lane then switched to NVIDIA's NVFP4 checkpoint for GB10's native FP4
path and restarted on `pool_v2`. The frozen receipts cover the first 43
minutes of that run; the run itself continued past the freeze.

### Hardware observations

- Power at the GPU package: 83.4 W mean (82.3–85.1 W) across 46 samples at
  100% SM utilization, SM clock 2,385–2,424 MHz. GB10 is far from a
  thermally-limited regime at this workload.
- `nvidia-smi --query-gpu` reports `[N/A]` for GPU and memory temperature on
  this driver/build — thermals are recorded as untested, not as "fine".
- `--gpu-memory-utilization 0.35` sizes the engine into the unified-memory
  budget alongside other node residents; weights are 19.95 GiB.
"""),

    ("md", r"""### Positioning vs TypeSafe Jev

[TypeSafe's Jev](https://docs.typesafe.ai/) (jev-1.13.0) is a hosted System
One model **trained with RLCD** — probabilities optimized against outcomes.
That calibration is their product. This bundle replicates the **contract and
the read mechanic** (kishida's `jev` contract on vLLM) and explicitly does
**not** claim the calibration:

| Claim | Status | Evidence |
|---|---|---|
| Contract shape (state + questions, choice/noul/score, probabilities, confidence, usage, 422s) | **measured** | 170HX bundle probe receipts (`negatives.json`, `mask-processed_logprobs.json`) |
| Read mechanic (one evaluation, no generation, bit-identical at c=1) | **measured** | 170HX `determinism.json`; this bundle's production run |
| No-train production operation on GB10 | **measured** | `receipts/load/` |
| Calibrated probabilities | **not claimed** — T=1 reads; 170HX n=42: acc 0.571, ECE 0.274 | 170HX `metrics.json` |
| Confidence numeric parity with jev-1.13 | **measured: no parity** — mean |Δ| 0.649, Pearson r −0.23 on the same 28 reads | 170HX bundle `positioning-bench/jev-leg.json` |
| >62 Choice options (Jev: 255), 64k context (deployed: 8k), multi-question single-call latency | **untested / not supported** | — |

**Measured alignment, self-hostable options** (n=42, the 170HX bundle's
labelled set; receipts in that bundle's `positioning-bench/`): our raw read
0.571 vs Laya (421M RLCD encoder, zero-shot) 0.643 vs GLiNER 2.5 Multi
0.476 — choice: 0.60 / **0.90** / 0.60, noul: 0.50 / 0.64 / 0.29. On the
classification judgment itself the trained-decision direction wins even
zero-shot; our raw read's edge is scale, context and zero training. Related
self-hosted judges: [Solomon](https://huggingface.co/DoccyHealth/Solomon)
(trained heads on the same base), [Laya](https://huggingface.co/convaiinnovations/laya),
[GLiNER 2.5](https://huggingface.co/fastino/gliner2.5-multi-v1) (schema
extraction).

**Measured vs jev-1.13.0** (n=42, the 170HX bundle's labelled set;
`positioning-bench/` in that bundle): jev-1.13.0 (live API) **0.881** —
choice 0.95, noul 0.93, score 0.63 — vs our raw read 0.571, Laya 0.643
(choice 0.90), GLiNER 0.476. Jev agrees with our read on only 61.9% of
reads, diverges from our choice distributions (JS 0.254), and its
confidence is unrelated to our entropy confidence (mean |Δ| 0.649, r
−0.23): the RLCD calibration is the product, and we do not claim it.
Closing the gap (temperature fit, trained heads, task fine-tune) is
future work.
"""),
    ("md", r"""### What this does not show

- **Decode.** Judge reads generate no answer token. Generation throughput,
  TTFT and speculative decoding on GB10 are untested here.
- **Calibration.** Accuracy and calibration on the 42-example labelled set
  live in the 170HX bundle and are descriptive there (n=42, in-sample fit);
  nothing in this run certifies calibration either.
- **Idle latency.** The pilot never stops, so an idle c=1 number is not
  measurable on this endpoint; the single-client probe (7.0 s mean) is a
  loaded number with a synthetic ~1.5k-token prompt.
- **Kernel A/B.** NVFP4-on-GB10 vs W4A16-on-170HX changes platform and
  quantization together. The comparison is a workload comparison.
- **Prefix caching.** Hit rate measured 0.0% on this traffic on both
  platforms; prompts that do share a long preamble would behave differently.

### Safety

Power stayed at 83–85 W (node "max performance" not required for this
workload), SM 96–100%, no error appears in the serve log for the frozen
window, zero failed annotations. Storage, networking and other node residents
were untouched; the receipt collection was read-only against the running
node.

### Evidence

- Receipts and harness: `results/2026-09-21-qwen3.8-27b-nvfp4-1node-jev-vllm/`
- The same contract on the CMP 170HX (W4A16):
  [club-170hx notebook](https://github.com/PixelML/club-170hx/blob/main/notebooks/2026-09-20-qwen3.8-27b-w4a16-jev-1card-vllm.ipynb)
  and its `results/2026-09-20-qwen3.8-27b-w4a16-jev-1card-vllm/` receipts —
  the source of every 170HX number quoted here.
- The Jev contract:
  [`kishida/llama.cpp`, branch `jev`, `docs/jev.md`](https://github.com/kishida/llama.cpp/blob/jev/docs/jev.md)
</details>
"""),
]


def main():
    cells = []
    for i, (kind, src) in enumerate(CELLS):
        cid = f"jev-spark-{i:02d}"
        if kind == "md":
            cells.append({"cell_type": "markdown", "id": cid, "metadata": {},
                          "source": src})
        else:
            cells.append({
                "cell_type": "code", "id": cid, "execution_count": None,
                "metadata": {}, "outputs": [], "source": src,
            })
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python",
                           "name": "python3"},
            "language_info": {"name": "python", "version": "3.10"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(nb, indent=1) + "\n")
    print("wrote", OUT, f"({len(cells)} cells)")


if __name__ == "__main__":
    main()
