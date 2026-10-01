# GLM-5.3-Flash EXL3 4bpw on 2× DGX Spark — 1M-token window, TensorFold

Measured 2026-10-01 on two DGX Sparks (GB10, SM121, arm64) linked by one ConnectX-7 cable. Notebook:
[`notebooks/2026-10-01-glm-5.3-flash-exl3-2node-tensorfold.ipynb`](../../notebooks/2026-10-01-glm-5.3-flash-exl3-2node-tensorfold.ipynb).

**Verdict.** On two Sparks, TensorFold serves GLM-5.3-Flash 4-bit EXL3 with a **1,048,576-token window** at **54 tok/s decode** (short prompt, thinking off) and **~1,500–1,860 tok/s prefill**: **3.6× the decode and 4–11× the prefill** of the one-Spark 2-bit llama.cpp run. A **245k-token prompt takes 2.6 min** instead of 28.8 min. Decode rows marked * use copy-heavy prompts and are inflated by copy drafts.

## Tested configuration

- Hardware: 2 × DGX Spark, GB10 / SM121, 128 GB unified memory each, driver 580.159.03, one QSFP cable (one RoCE rail).
- Recipe: [`MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks-TensorFold`](https://github.com/MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks-TensorFold) @ `ed026ef92d1650120dada1294a112acb6c8f2f48` (TensorFold v0.5.0 + 52 patches).
- Image: `ghcr.io/miaai-lab/glm-5.3-flash-exl3-2x-dgx-sparks-tensorfold:v0.5.0-cefe8bf45d07`.
- Model: `Mia-AiLab/GLM-5.3-Flash-EXL3-TR3-4bpw` @ `9eaebb7c4e96d983dcd538e18624622ba5b820a8` (EXL3 4-bit routed experts; other weights served as q4).
- Drafter: `incoai/GLM-5.3-Flash-DFlash2` @ `bf582e4eacc1810f76656d1811693ff6c6737d2a` (CC BY-NC-ND 4.0, non-commercial) plus copy drafts.
- Settings: recipe defaults — 4 concurrent requests, 1,048,576-token window, FP8 KV, vision on.
- Memory after load: ~111 GiB used on each Spark, 8–10 GiB available. No headroom for another workload.

## Measured (temperature 0, median of 3; n=1 for ≥128k; tokens from the usage object; one request at a time)

| Workload | Prompt tokens | TTFT | Prefill tok/s | Decode tok/s | 1× Spark 2-bit: decode / prefill / TTFT |
|---|---:|---:|---:|---:|---:|
| Short, thinking off | 30 | 0.17 s | — | 54.4 (53.5–55.9) | 15.1 / — / 0.7 s |
| Short, thinking on | 22 | 0.15 s | — | 67.2 (66.7–68.0) | 15.7 / — / 0.4 s |
| Prefill ~7k | 7,433 | 4.97 s | 1,494 (1,137–1,833) | — | — / 378 / 19.6 s |
| Prefill ~28k | 27,783 | 14.90 s | 1,865 (1,808–1,892) | — | — / 346 / 80.0 s |
| Decode after ~28k context* | 27,717 | 14.98 s | — | 114.3 (105.0–117.3) | 13.9 / — / 78.9 s |
| 128k (n=1)* | 127,724 | 73.91 s | 1,728 | 56.6 | 10.7 / 212 / 601.4 s |
| 245k (n=1)* | 244,136 | 157.23 s | 1,553 | 66.0 | 8.3 / 141 / 1729.6 s |

\* The long-context prompts are random tokens with an instruction to continue or count them, so copy drafts accept
far more tokens than in normal chat. Treat those decode rows as an upper bound; the short-prompt rows are the
single-request decode figure. Every prompt had a unique random prefix (no cache hits).

## Concurrency (1–4 requests, measured)

| Concurrent requests | Aggregate tok/s | Per request tok/s | TTFT |
|---:|---:|---:|---:|
| 1 | 51.1 (50.6–51.6) | 52.2 | 0.18 s |
| 2 | 68.0 (65.9–68.1) | 35.2 | 0.29 s |
| 3 | 79.9 (77.7–81.2) | 27.5 | 0.34 s |
| 4 | 89.2 (89.0–89.5) | 23.2 | 0.38 s |

Unique prose prompt per request, thinking off, `ignore_eos`, 512 output tokens, temperature 0, median of 3 rounds;
aggregate = total completion tokens / wall time from first send to last finish. Four requests give **1.75×** one
request's throughput. The recipe reports 108.8 aggregate / 27.9 per request at 4 (prose); this run is ~18% lower,
with GPU clocks not capped and one RoCE rail cabled instead of two. Harness: [`harness/conc.py`](harness/conc.py).

## Correctness gates

- [x] Coherent text; reasoning returned separately as `reasoning_content`; `enable_thinking=false` honored
- [x] Tool call routed through a coding harness (shell tool, exact output returned)
- [x] Container restart count 0 on both ranks after all tests
- [ ] Multimodal: vision tower loaded, not tested here
- [ ] Quality: not scored here (the recipe reports GSM8K 98.0%, HumanEval 97.6%)
- [x] Concurrency: 1–4 requests measured (above)

## Setup note

`scripts/prepare.sh` stopped with `the worker's tensorfold-glm53:v0.5.0 differs from the head's` although all 71 layer
digests matched: one Spark used Docker's containerd image store and the other overlay2, which report different image
IDs for the same image. [`harness/image-id-check.patch`](harness/image-id-check.patch) compares layer digests instead.

Harness and receipts: [`harness/`](harness/), [`receipts/`](receipts/).
