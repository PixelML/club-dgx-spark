# Qwen3.8-27B (NVFP4) as a no-train Jev endpoint — 1× DGX Spark (GB10), vLLM

Measured 2026-09-21 on one DGX Spark (GB10, SM121, arm64). Notebook:
[`notebooks/2026-09-21-qwen3.8-27b-nvfp4-1node-jev-vllm.ipynb`](../../notebooks/2026-09-21-qwen3.8-27b-nvfp4-1node-jev-vllm.ipynb).

**Question.** Can one GB10 carry the no-train Jev classification endpoint —
label distribution from a single prompt evaluation, no answer generated — at
production rate, on NVIDIA's NVFP4 checkpoint?

**Answer.** Yes. The first production workload (the same LLM-as-judge
annotation pilot later run on the CMP 170HX, same pool, same contract) completed
**4,295 annotations in 43 minutes with zero failures**: engine prefill 2,573
tok/s in a 94 s sampled window (2,582 tok/s ledger average) at an 83.4 W mean,
mean answer per engine request 6.86 s with every sampled read ≤ 10 s.

## Findings

1. **The serving recipe transfers unchanged.** `--logprobs-mode
   processed_logprobs` is required (the default computes logprobs before
   `allowed_token_ids`), prefix caching on, `--max-logprobs` ≥ label count —
   the same flags the 170HX bundle established.
2. **Prefix cache hits 0.0% on this traffic** (0 reused of 241,840 queried
   tokens in the window): per-item judge prompts share no leading KV blocks.
   Same result on both platforms.
3. **The wait is queue, not compute.** 49 requests in flight at 8.47 req/s
   predicts 5.8 s by Little's law; measured mean 6.86 s. Engine prefill rate
   and ledger rate agree within 2% — the pilot keeps the GB10 fed.

## Measured

| Quantity | Value | Receipt |
|---|---|---|
| Production run | 4,295 annotations, 0 failures, 43 min, 6.63M prompt tokens, $0.28 pilot-internal | `load/load-summary.json` |
| Prefill | 2,572.8 tok/s (window) · 2,580.3 tok/s steady ledger-side | `load/metrics-delta.json`, `load-summary.json` |
| Answer, mean e2e per request | 6,862.5 ms; 796/796 window reads ≤ 10 s | `load/metrics-delta.json` |
| Reads per annotation / gen tokens per request | 5.1 / 1.00 | `load/metrics-delta.json` |
| Prefix cache hit rate | 0.0% | `load/metrics-delta.json` |
| Single-client probe under load | 7,046 ms mean (5,809–7,960), n=15, synthetic ~1.5k-token prompt | `load/load-summary.json` |
| GPU package power | 83.4 W mean (82.3–85.1), SM 96–100%, SM clock 2,385–2,424 MHz | `load/gpu-telemetry.json` |
| Boot | weights 19.95 GiB loaded in 162.6 s; startup ≈ 2.9 min | `env.json`, serve log |

## Receipts and harness

| File | What it is |
|---|---|
| `receipts/load/load-summary.json` | frozen aggregate of the pilot's ledger (counts, tokens, per-hour, per-minute, probe) |
| `receipts/load/metrics-delta.json` | engine `/metrics` deltas over the 94 s window |
| `receipts/load/load-ledger-minutes.json` | annotations and prompt tokens per UTC minute |
| `receipts/load/gpu-telemetry.json` | 46 × 2 s `nvidia-smi` samples |
| `receipts/env.json` | runtime versions, model revision, masked serve flags, boot facts |
| `harness/make_chart.py`, `harness/build_notebook.py` | rebuild the figure and the notebook from the receipts |

The raw pilot ledger names pool items and stays outside the repository; the
collection recipe mirrors the CMP 170HX bundle's `collect_load_receipts.py`.

## Comparison caveat

The cross-card comparison is NVFP4-on-GB10 vs W4A16-on-CMP-170HX of the same
contract and pool — platform and quantization change together. Every 170HX
number comes from that bundle's committed receipts.

## Positioning vs TypeSafe Jev

TypeSafe's Jev (jev-1.13.0) is a hosted System One model trained with RLCD —
probabilities optimized against outcomes. That calibration is their product.
This bundle replicates the **contract and the read mechanic** (kishida's
`jev` contract on vLLM) and explicitly does **not** claim the calibration.

| Claim | Status | Evidence |
|---|---|---|
| Contract shape (state + questions, choice/noul/score, probabilities, confidence, usage, 422s) | **measured** | the 170HX bundle's probe receipts (`negatives.json`, `mask-processed_logprobs.json`) |
| Read mechanic (one evaluation, no generation, bit-identical at c=1) | **measured** | 170HX `determinism.json`; this bundle's production run |
| No-train production operation on GB10 | **measured** | `receipts/load/` |
| Calibrated probabilities | **not claimed** — T=1 reads; 170HX n=42: acc 0.571, ECE 0.274 | 170HX `metrics.json` |
| Confidence numeric parity with jev-1.13 | **measured: no parity** — mean |Δ| 0.649, Pearson r −0.23 on the same 28 reads | 170HX bundle `positioning-bench/jev-leg.json` |
| >62 Choice options (Jev: 255), 64k context (deployed: 8k), multi-question single-call latency | **untested / not supported** | — |

**Measured alignment, self-hostable options** (n=42, the 170HX bundle's
labelled set; receipts in the 170HX bundle `positioning-bench/`): our raw
read 0.571 vs Laya (421M RLCD encoder, zero-shot) 0.643 vs GLiNER 2.5 Multi
0.476 — choice: 0.60 / **0.90** / 0.60. On the classification judgment
itself the trained-decision direction wins even zero-shot; our raw read's
edge is scale, context and zero training. Closing calibration (temperature
fit, trained heads, fine-tune) is future work. The jev-1.13 leg of the bench


## Credits

Jev contract: [kishida's `jev` branch docs](https://github.com/kishida/llama.cpp/blob/jev/docs/jev.md).
Serving-recipe lineage (`processed_logprobs`, prefix caching, label-masked
reads): the CMP 170HX bundle and Kis's
[DFlash2 notebook](https://github.com/PixelML/club-170hx/blob/main/notebooks/2026-08-30-qwen3.8-27b-w4a16-dflash2-1card-vllm.ipynb).
Related self-hosted judges: [Solomon](https://huggingface.co/DoccyHealth/Solomon)
(trained heads on the same base), [Laya](https://huggingface.co/convaiinnovations/laya)
(421M RLCD encoder), [GLiNER 2.5](https://huggingface.co/fastino/gliner2.5-multi-v1)
(schema extraction).

## Limitations

- Classification reads only; decode/TTFT/speculative decoding untested on GB10.
- No idle-c=1 latency: the pilot never stops; the probe is a loaded number.
- Calibration claims live in the 170HX bundle (n=42, descriptive) — nothing
  here certifies calibration.
- Thermals untested: GB10 reports temperature as N/A through `nvidia-smi` on
  this driver.

**Measured vs jev-1.13.0** (n=42, the 170HX bundle's labelled set;
`receipts/positioning-bench/` there): jev-1.13.0 (live API) **0.881** —
choice 0.95, noul 0.93, score 0.63 — vs our raw read 0.571, Laya 0.643
(choice 0.90), GLiNER 0.476. Jev agrees with our read on only 61.9% of
reads, diverges from our choice distributions (JS 0.254), and its
confidence is unrelated to our entropy confidence (mean |Δ| 0.649, r
−0.23): the RLCD calibration is the product, and we do not claim it.
Closing the gap (temperature fit, trained heads, task fine-tune) is
future work.
