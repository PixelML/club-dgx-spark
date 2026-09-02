# DGX Spark experiment catalog

Status labels describe the evidence level, not whether a recipe will work for you.

- **Measured**: PixelML independently produced benchmark or correctness evidence on its own hardware.
- **Untested**: recipe is published but PixelML has no independent hardware receipt yet.
- **Community-reported**: figures are quoted from the upstream author and not re-measured by PixelML.

## Recipe status matrix

Full-platform depth including context, memory, quality-evidence, and energy/cost columns: [COVERAGE-MATRIX.md](COVERAGE-MATRIX.md).

| Model family | Public repository | Quantization | Runtime | Topology | Context | Evidence status | Key measured result | Blocker |
|---|---|---|---|---|---|---|---|---|
| GLM-5.3-Flash | [GLM-5.3-Flash-NVFP4-Dual-DGX-Spark @ `3407023e`](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark/tree/3407023e0b8109a1dd12e8a5544e106ca6912afe) | NVFP4 (ModelOpt), FP8 E4M3 KV | vLLM + Ray TP=2 | 2× DGX Spark | 262K | **Measured** | 27–68 aggregate decode tok/s (×1–×8); 1,277–1,372 uncached prefill input tok/s | None for main profile |
| GLM-5.3-Flash (DFlash2) | [dflash2/](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark/tree/3407023e0b8109a1dd12e8a5544e106ca6912afe/dflash2) | NVFP4 target, DFlash2 K=7 draft | vLLM + Ray TP=2 | 2× DGX Spark | 262K | **Measured** | 25.3–61.3 decode tok/s depending on prompt shape; non-commercial eval only | CC BY-NC-ND 4.0 draft license |
| GLM-5.3-Flash (EXL3+DFlash2) | [exl3/](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark/tree/3407023e0b8109a1dd12e8a5544e106ca6912afe/exl3) | EXL3/TR3 4-bpw experts, FP8 KV | vLLM + Ray TP=2 | 2× DGX Spark | 900K | **Measured** | 66.3 single-stream, 154.9 aggregate ×4; 300K-token stress passed; 8m40s cold start | Non-commercial DFlash2 draft |
| Qwen3.8-Flash-Next | [qwen3-8-flash-next-sglang-2x-dgx-spark @ `682504be`](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark/tree/682504bec9e7e99206212f4e172b7ec823e4605c) | NVFP4 (ModelOpt, FlashInfer CUTLASS) | SGLang TP=2 | 2× DGX Spark | 262K | **Measured** | 47.5–275 aggregate decode tok/s (×1–×16); 2,328–2,960 uncached prefill input tok/s | None; SM121 QSA workaround merged |
| Step-3.7-Flash | [Step-3.7-Flash-NVFP4-Dual-DGX-Spark](https://github.com/PixelML/Step-3.7-Flash-NVFP4-Dual-DGX-Spark) | NVFP4 | vLLM (no-Ray) TP=2 | 2× DGX Spark | — | **Untested** | No PixelML hardware receipt; upstream figures not quoted | Awaiting dual-Spark validation |
| Hunyuan 3 (295B MoE) | [Hy3-NVFP4-Dual-DGX-Spark](https://github.com/PixelML/Hy3-NVFP4-Dual-DGX-Spark) | NVFP4/W4A16 (MARLIN) | vLLM + Ray TP=2 | 2× DGX Spark | — | **Untested** | Upstream-reported figures only; results/ intentionally empty | Awaiting dual-Spark validation |
| Inkling-Small | [Inkling-Small-NVFP4-Dual-DGX-Spark](https://github.com/PixelML/Inkling-Small-NVFP4-Dual-DGX-Spark) | NVFP4, FP4 MX block16 KV | SGLang (drowzeys champion) + DSpark speculative | 2× DGX Spark | 1M | **Untested** | No PixelML hardware receipt; results/ intentionally empty | Awaiting dual-Spark validation |

## Cross-platform cost and efficiency: CMP 170HX vs DGX Spark

DeepSeek-V4-Flash-Vision-Exp ran on both a four-card CMP 170HX rig and a
two-node DGX Spark kit at the same checkpoint and revision, using the same
greedy/400-token/`ignore_eos` protocol. Full receipts, raw power logs, and
the cost model live in
[PixelML/club-170hx](https://github.com/PixelML/club-170hx/blob/main/docs/BENCHMARKS.md#cross-platform-4x-cmp-170hx-vs-2x-dgx-spark)
(two-node DGX Spark evidence is
[PixelML/DeepSeek-V4-Flash-Vision-Exp-DGX-Spark](https://github.com/PixelML/DeepSeek-V4-Flash-Vision-Exp-DGX-Spark)).

| Concurrency | CMP 170HX tok/s | CMP 170HX tok/Wh | DGX Spark tok/s | DGX Spark tok/Wh |
|---|---|---|---|---|
| 1 | 97.4 | 681 | 37.7 | 1,862 |
| 2 | 103.7 | 966 | 48.4 | 2,179 |
| 4 | 165.5 | 1,151 | 73.5 | 3,002 |
| 8 | 220.2 | 1,457 | 81.1 | 3,172 |

At c=8 and an assumed $8,300 four-card CMP build vs. $8,000 for two DGX
Spark units (3-year lifetime, 50% utilization, $0.15/kWh), the CMP rig
comes out to about $0.90 per million output tokens and the DGX Spark pair
to about $2.13. DGX Spark still wins on tokens per watt-hour by roughly
2x, since GB10's unified memory draws far less than four discrete GPUs;
its power reading is GPU-only, so it is a lower bound on whole-node draw.
Hardware price, electricity rate, and the lifetime/utilization figures are
assumed inputs, not measurements — throughput and GPU power are measured.

![Tokens per Wh and dollars per million tokens, 4x CMP 170HX vs 2x DGX Spark](../assets/charts/2026-09-02-cross-platform-cmp170hx-vs-dgxspark.png)

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
