# DGX Spark experiment catalog

Status labels describe the evidence level, not whether a recipe will work for you.

- **Measured**: PixelML independently produced benchmark or correctness evidence on its own hardware.
- **Untested**: recipe is published but PixelML has no independent hardware receipt yet.
- **Community-reported**: figures are quoted from the upstream author and not re-measured by PixelML.

## Recipe status matrix

Full-platform depth including context, memory, quality-evidence, and energy/cost columns: [COVERAGE-MATRIX.md](COVERAGE-MATRIX.md).

| Model family | Public repository | Quantization | Runtime | Topology | Context | Evidence status | Key measured result | Blocker |
|---|---|---|---|---|---|---|---|---|
| GLM-5.3-Flash | [GLM-5.3-Flash-NVFP4-Dual-DGX-Spark](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark) | NVFP4 (ModelOpt), FP8 E4M3 KV | vLLM + Ray TP=2 | 2× DGX Spark | 262K | **Measured** | 27–68 aggregate decode tok/s (×1–×8); 1,277–1,372 uncached prefill input tok/s | None for main profile |
| GLM-5.3-Flash (DFlash2) | [dflash2/](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark/tree/main/dflash2) | NVFP4 target, DFlash2 K=7 draft | vLLM + Ray TP=2 | 2× DGX Spark | 262K | **Measured** | 25.3–61.3 decode tok/s depending on prompt shape; non-commercial eval only | CC BY-NC-ND 4.0 draft license |
| GLM-5.3-Flash (EXL3+DFlash2) | [exl3/](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark/tree/main/exl3) | EXL3/TR3 4-bpw experts, FP8 KV | vLLM + Ray TP=2 | 2× DGX Spark | 900K | **Measured** | 66.3 single-stream, 154.9 aggregate ×4; 300K-token stress passed; 8m40s cold start | Non-commercial DFlash2 draft |
| Qwen3.8-Flash-Next | [qwen3-8-flash-next-sglang-2x-dgx-spark](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark) | NVFP4 (ModelOpt, FlashInfer CUTLASS) | SGLang TP=2 | 2× DGX Spark | 262K | **Measured** | 47.5–275 aggregate decode tok/s (×1–×16); 2,328–2,960 uncached prefill input tok/s | None; SM121 QSA workaround merged |
| Step-3.7-Flash | [Step-3.7-Flash-NVFP4-Dual-DGX-Spark](https://github.com/PixelML/Step-3.7-Flash-NVFP4-Dual-DGX-Spark) | NVFP4 | vLLM (no-Ray) TP=2 | 2× DGX Spark | — | **Untested** | No PixelML hardware receipt; upstream figures not quoted | Awaiting dual-Spark validation |
| Hunyuan 3 (295B MoE) | [Hy3-NVFP4-Dual-DGX-Spark](https://github.com/PixelML/Hy3-NVFP4-Dual-DGX-Spark) | NVFP4/W4A16 (MARLIN) | vLLM + Ray TP=2 | 2× DGX Spark | — | **Untested** | Upstream-reported figures only; results/ intentionally empty | Awaiting dual-Spark validation |
| Inkling-Small | [Inkling-Small-NVFP4-Dual-DGX-Spark](https://github.com/PixelML/Inkling-Small-NVFP4-Dual-DGX-Spark) | NVFP4, FP4 MX block16 KV | SGLang (drowzeys champion) + DSpark speculative | 2× DGX Spark | 1M | **Untested** | No PixelML hardware receipt; results/ intentionally empty | Awaiting dual-Spark validation |

## Known negative results and limitations

These are measured findings preserved across repos:

- GLM-5.3-Flash ×7–×8 concurrency showed TTFT queueing; ×6 was the uncached decode sweet spot on that checkpoint.
- GLM-5.3-Flash DFlash2 acceptance is prompt-dependent (91% structured → 31% planning-heavy); decode speed scales with acceptance rate.
- Qwen3.8-Flash-Next NEXTN/MTP allocates additional Mamba state, reducing effective max running requests from 36 to 25.
- GLM-5.3-Flash multimodal UMA failure isolated during revalidation; the earlier smoke test did not reproduce it.
- Step-3.7-Flash, Hunyuan 3, and Inkling-Small have zero PixelML hardware receipts; their upstream figures are community-reported.

## Adding a result

1. Publish the detailed, redacted attempt in its model-family repository.
2. Add or update a row in the matrix above with the evidence status and measured result.
3. Add cross-model metrics only when the methodology is comparable.
4. Preserve blocked and failed attempts; do not list only wins.
