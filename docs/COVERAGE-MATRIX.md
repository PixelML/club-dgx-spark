# DGX Spark coverage matrix

Full-platform view across every accessible DGX Spark model repository. Speed and quality evidence live in each model repository; this table records only what exists, its validation depth, and what is missing. Claim labels follow the club standard: **measured**, **inferred**, **community-reported**, **untested**.

Column key: Q-evidence = quality/correctness evidence beyond coherence. E/cost = energy or cost-per-task evidence.

## Matrix

| Model family | Repo | Quant / precision | Runtime | Topology | Context | Reproducible command | Speed / latency | Memory | Q-evidence | E/cost | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GLM-5.3-Flash | [GLM-5.3-Flash-NVFP4-Dual-DGX-Spark](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark) | NVFP4 (ModelOpt), FP8 E4M3 KV | vLLM + Ray TP=2 | 2× Spark | 262K | `./start.sh` + `./benchmark.py` + `./prefill-benchmark.py` | **Measured**: 27–68 agg decode tok/s ×1–×8; 1,277–1,372 uncached prefill tok/s; TTFT table | **Measured**: 8.5 GiB KV; cold start 676s + profile | Coherence, stop, tool-call routing, image/video gates — **measured**; no scored accuracy set | None — **gap** | Published recipe |
| GLM DFlash2 | [dflash2/](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark/tree/main/dflash2) | NVFP4 target + K=7 draft | vLLM + Ray TP=2 | 2× Spark | 262K | recipe + benchmark scripts | **Measured**: 25.3–61.3 tok/s; acceptance 31–91% by prompt shape | Draft weights per rank | Same gates as main profile | None — **gap** | Published; eval-only license |
| GLM EXL3 | [exl3/](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark/tree/main/exl3) | EXL3/TR3 4-bpw + FP8 KV | vLLM + Ray TP=2 | 2× Spark | 900K | recipe scripts | **Measured**: 66.3 single, 154.9 agg ×4; 300K stress; 8m40s cold start | Fits with MTP headroom | Coherence + stress pass — **measured** | None — **gap** | Published; eval-only draft |
| Qwen3.8-Flash-Next | [qwen3-8-flash-next-sglang-2x-dgx-spark](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark) | NVFP4 (ModelOpt, FlashInfer CUTLASS) | SGLang TP=2 | 2× Spark | 262K | `./scripts/prepare-model.sh` → `start-cluster.sh` → `smoke-benchmark.py` | **Measured**: 47.5–275.4 agg tok/s ×1–×16; 2,328–2,960 prefill tok/s | **Measured**: +1.45–1.49 GB draft/rank; MTP cuts max seqs 36→25 | Functional validation (text + image VQA) — **measured**; no scored set | None — **gap** | Published recipe |
| Step-3.7-Flash | [Step-3.7-Flash-NVFP4-Dual-DGX-Spark](https://github.com/PixelML/Step-3.7-Flash-NVFP4-Dual-DGX-Spark) | NVFP4 | vLLM (no-Ray) TP=2 | 2× Spark | — | recipe published | **Untested** | **Untested** | **Untested** | None | Recipe-only |
| Hy3-295B | [Hy3-NVFP4-Dual-DGX-Spark](https://github.com/PixelML/Hy3-NVFP4-Dual-DGX-Spark) | NVFP4/W4A16 (MARLIN) | vLLM + Ray TP=2 | 2× Spark | — | recipe published | **Community-reported** upstream only | **Untested** | **Untested** | None | Recipe-only |
| Inkling-Small | [Inkling-Small-NVFP4-Dual-DGX-Spark](https://github.com/PixelML/Inkling-Small-NVFP4-Dual-DGX-Spark) | NVFP4, FP4 MX block16 KV | SGLang + DSpark spec | 2× Spark | 1M | recipe published | **Untested** | **Untested** | **Untested** | None | Recipe-only |
| GLM EXL3 (upstream MiaAI) | [GLM-5.3-Flash-EXL3-2x-DGX-Sparks](https://github.com/MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks) @ 79f10b9 | EXL3/TR3 4-bpw, FP8 ds_mla KV, DFlash2 k=7 | vLLM TP2 (pinned 487ecf187, ExLlamaV3 c5d9c657, CUDA 13.0 sm_121a) | 2× Spark | 1M | full scripts + 11 tests | **Community-reported**: 62.9 x1 / 146.5 agg x4; KLD panel 4bpw 0.0246 nats; prefix-cache ~90% reuse | 18.67 GiB KV pool | KLD weights-level (external) | None — gap | Upstream; our lane vendors bd7f55e |


## Platform-level coverage (not per model)

| Dimension | Coverage | Depth | Where |
|---|---|---|---|
| Bring-up / setup | Covered | Documentation | docs/SETUP.md |
| Networking (CX7/RoCE) | Covered | Measured (GLM, Qwen); recipe-documented (rest) | model repos |
| SM121 kernel workarounds | Covered | Measured | Qwen Triton QSA fallback; GLM Marlin/eager |
| Benchmark methodology | Covered | Documentation | docs/BENCHMARK-METHOD.md |
| Thermal / power | **Missing** | — | template field exists; no receipt data |
| Energy / cost per task | **Missing** | — | no repo measures it |
| Quality scoring | **Missing** | — | gates are pass/fail; no scored eval |
| Single-node topology | **Missing** | — | every recipe is dual-node |
| 3+ node topology | **Missing** | — | untested |

## Cheapest safe gap-fills (documentation/test only, no GPU)

1. Add thermal/power sampling to the receipt template (done in results/TEMPLATE.md) and to both measured repos' next runs.
2. Label every recipe's quality evidence as gate-level, not scored accuracy (done in matrix above).
3. Publish this matrix so untested combinations are visible before anyone schedules GPU time.
4. Ecosystem sources beyond PixelML: [source registry](sources/README.md) with exact revisions and evidence levels.
4. Track SparkQuant-Lab (local commit `dca8259`) as the quality-layer plan: streamed-BF16 vs NVFP4 KL-divergence + capability + agentic layers; it is not yet a PixelML public repository.
