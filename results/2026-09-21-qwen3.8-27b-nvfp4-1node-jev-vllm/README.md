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

## Credits

Jev contract: [kishida's `jev` branch docs](https://github.com/kishida/llama.cpp/blob/jev/docs/jev.md).
Serving-recipe lineage (`processed_logprobs`, prefix caching, label-masked
reads): the CMP 170HX bundle and Kis's
[DFlash2 notebook](https://github.com/PixelML/club-170hx/blob/main/notebooks/2026-08-30-qwen3.8-27b-w4a16-dflash2-1card-vllm.ipynb).

## Limitations

- Classification reads only; decode/TTFT/speculative decoding untested on GB10.
- No idle-c=1 latency: the pilot never stops; the probe is a loaded number.
- Calibration claims live in the 170HX bundle (n=42, descriptive) — nothing
  here certifies calibration.
- Thermals untested: GB10 reports temperature as N/A through `nvidia-smi` on
  this driver.
