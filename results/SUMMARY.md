# Cross-model result summary

Only PixelML-measured results appear here. Community-reported and untested entries are in the [gap analysis](../docs/GAP-ANALYSIS.md).

| Model/checkpoint | Quant | Runtime | Topology | Workload | Aggregate tok/s | Uncached prefill input tok/s | Detailed evidence |
|---|---|---|---|---|---:|---:|---|
| GLM-5.3-Flash @ 11d7321 | NVFP4 | vLLM + Ray TP=2 | 2× Spark | Decode ×1–×8 | 27.3–67.6 | 1,277–1,372 | [NVFP4 receipts 2026-08-27](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark/tree/main/results) |
| GLM-5.3-Flash DFlash2 @ 7d74cdd | NVFP4 + K=7 draft | vLLM + Ray TP=2 | 2× Spark | Decode ×1 (structured/code/planning) | 25.3–61.3 | 1,310–1,400 | [DFlash2 receipts 2026-08-28](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark/tree/main/results) |
| GLM-5.3-Flash EXL3 @ 25a44fd | EXL3 4bpw + DFlash2 | vLLM + Ray TP=2 | 2× Spark | Decode ×1 / ×4 aggregate | 66.3 / 154.9 | 702–795 | [EXL3 receipts 2026-08-28](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark/tree/main/results) |
| Qwen3.8-Flash-Next @ b80180e | NVFP4 | SGLang TP=2 | 2× Spark | Decode ×1–×16 | 47.5–275.4 | 2,328–2,960 | [RESULTS](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark/blob/main/results/RESULTS-2026-08-26.md) / [PREFILL](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark/blob/main/results/PREFILL-2026-08-27.md) |

Notes:

- Aggregate decode tok/s is the sum of per-stream output rates at the stated concurrency; single-stream tok/s is the per-stream mean.
- Uncached prefill input tok/s is measured client-side with a unique randomized prefix, one forced output token, and the API-reported prompt-token count. It includes HTTP, tokenization, scheduling, and the first decode step.
- GLM and Qwen use different checkpoints, runtimes, and active-parameter counts; cross-model speed comparisons are directional, not apples-to-apples.
- Token counts for decode come from the final usage object in the streaming response, not from summing stream events.