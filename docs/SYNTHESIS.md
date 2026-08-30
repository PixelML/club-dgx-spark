# DGX Spark cross-cutting synthesis

What the curated sources plus PixelML measurements jointly teach about running
models on GB10/SM121 hardware. Every number is labeled: **measured** (PixelML
receipt exists), **community-reported** (upstream, not re-measured), or
**untested**. Sources: [source registry](sources/README.md).

## Topology

| Topology | Status | What we know | Evidence |
|---|---|---|---|
| 1x Spark | community-reported | DS4F-0731 EXL3 3bpw fits single-node with 384k ctx, 44-47 tok/s structured, DSpark K5 (MiaAI one-node repo) | community-reported |
| 2x Spark TP2 | measured | Best-covered: GLM NVFP4, GLM EXL3, Qwen3.8 SGLang all PixelML-measured on Apollo pair | PixelML receipts |
| 3x Spark TP3 | community-reported | GLM-5.2 NVFP4+AQLM 380k ctx ~21 tok/s; only triple recipe found | community-reported |
| 1M context | community-reported + PixelML 300k stress | EXL3 1M pool 1.75x; DS4F 2.49M pool; our 300k stress passed | mixed |

Decision rule: single node only for compressed quants (EXL3 3bpw class);
two nodes for NVFP4 176B+ and 262k+ serving; three nodes only for 272GB+
hybrid checkpoints. Single-node GLM NVFP4 (181 GiB) remains untested and
likely does not fit.

## Runtime compatibility

- vLLM + Ray TP2 is the measured default for GLM NVFP4; **measured**.
- vLLM no-Ray TP2 works for Step-3.7 recipe; **untested** by PixelML.
- SGLang TP2 works for Qwen3.8 after SM121 QSA kernel fixes; **measured** (our lane) and community-reported (upstream 64/117 tok/s).
- llama.cpp/GGUF path is the community default for 27-35B single-node agents; **community-reported**.
- Do-not-repeat failures (all community-reported, several hit by us): SGLang FlashInfer DSA rejects SM121; TileLang DSA exceeds GB10 smem; TRITON_ATTN in speculative config collapses EXL3 acceptance; bf16 or NVFP4 KV on sparse-MLA path unsupported.

## Quantization and precision

| Format | Where seen | Speed character | Quality evidence |
|---|---|---|---|
| NVFP4 weights | GLM, Qwen, Step, DS4F, MiMo, Hy3 | Fast MoE path; measured 27-68 agg (GLM) / 47.5-275.4 (Qwen) | No scored eval anywhere - gap |
| EXL3/TR3 4bpw | GLM EXL3 lane | 66.3/154.9 measured; 62.9/146.5 community | KLD weights-level panel (community): 0.0246 nats, matches FP8 at 54% bytes |
| EXL3 3bpw | DS4F single-node | 44-47 tok/s community | None |
| NVFP4+AQLM hybrid | GLM-5.2 triple | ~21 tok/s community | None |
| GGUF Q8_K_XL | 27-35B agents | Not tok/s-focused; 2.2-3.6s turns | tool-eval-bench scores (community) |

## Memory, KV, and long context

Core lesson across all sources (community + measured): **KV pool is shared
and bounded by live tokens, not by max_num_seqs x max_model_len**. Concurrency
ceilings print at boot; full-context requests queue. Hybrid mamba/NSA models
carry a large length-independent floor. KV dtype trades context for decode:
GLM-5.2 fp8 KV ~+20% decode but 235k vs 348k ctx (community). Prefill decays
with depth on long contexts (community: 1024 -> 350-614 tok/s past 300k).

## Speculative decoding

| Method | Where | Result | Evidence |
|---|---|---|---|
| DFlash2 k=7 | GLM EXL3 | Structured 61.7-62.9 tok/s vs prose 26.9; acceptance 0.918 vs 0.332 | community + PixelML bands |
| MTP k=2 baseline | GLM EXL3 | ~24.6 tok/s lab | community |
| DSpark K5 | DS4F | 1M ctx serving | community |
| NEXTN | Qwen3.8 | 47.5-275.4 agg measured; cuts max seqs 36->25 | PixelML measured |
| MTP-3 | Step-3.7 | ~31-32 tok/s | community |

Prompt-shape dependence is the universal lesson: report acceptance by
prompt class (structured/prose/code), never a single blended number.

## Multimodal

GLM vision tower works on both lanes but first-compile needs UMA headroom;
skip-MM-profiling is required on GB10; video placeholder alignment patch
needed (all community + our gate receipts). Image+video limits: 4 images /
1 video per prompt. Clients silently strip attachments when the model is not
marked vision-capable - a measured operational gotcha.

## Evaluation methodology

1. Always fix and report thinking on/off - it changes scores AND safety outcomes (community: +8 score but TC-60 sleeper-injection fail when ON).
2. Report Pass@k and Pass^k (ceiling and floor) for reliability; 8 trials standard (community).
3. Use unique prefixes to defeat prefix caching when measuring prefill (jvr0x method).
4. Token counting from final usage object only (PixelML standard).
5. Separate acceptance by prompt class.
6. Safety category gate: cap ratings when safety scores below threshold (tool-eval-bench pattern).
7. Our gap: no scored quality layer exists for any PixelML DGX recipe; SparkQuant-Lab dca8259 is the plan.

## Performance, energy, cost

Only speed+latency is measured today. Energy and cost-per-successful-task
are missing everywhere (upstream and ours). Community power envelope for
GB10: 40-45W idle, 120-130W GPU load (jasonacox). Next: add power sampling
to the receipt template, then compute cost-per-task once quality layer lands.

## Monitoring and failure recovery

- earlyoom on DGX Spark SIGTERMs vLLM/Ray under memory pressure - disable before serving large models (community, hit repeatedly).
- sparkDash (MIT) is the reference fleet dashboard; adopt its vLLM health metric set (KV %, queues, TTFT p95, prefix cache, MTP accept).
- Kit-specific bring-up hazards: NIC names differ per pair; NCCL GID index can be all-zero on one node; >=105.9 GiB free needed at util 0.87; MNBT=2048 prefill guard on GB10 indexer topk.
- Never interrupt a degraded head container waiting on a dead peer - diagnose read-only first (PixelML ops rule).
