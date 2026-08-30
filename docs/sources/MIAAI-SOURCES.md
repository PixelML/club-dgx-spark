# MiaAI-Lab source registry

Reviewed 2026-08-30 from the 73-repository organization. Prioritized by the
four topic clusters: multi-node/topology, runtime/quant/spec-decode,
measurement/eval, and operations. Dated HTML galleries, editor forks, and
non-Spark awesome-lists are excluded by the quality criteria.

All rows are **upstream/community-reported** unless noted.

## Multi-node serving and topology

| Repository | Revision | License | Topology | Model / quant | Claimed result | Reproduction | Reusable learning | Limitations | Next experiment |
|---|---|---|---|---|---|---|---|---|---|
| [GLM-5.3-Flash-EXL3-2x-DGX-Sparks](https://github.com/MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks) | `79f10b9` | MIT | 2x GB10, vLLM TP2 over CX7 | GLM-5.3-Flash EXL3/TR3 4bpw + FP8 KV + DFlash2 k=7 | Structured decode 62.9 tok/s x1, 146.5 agg x4; 1M context pool 1.75x; prefix-cache reuse ~90% on 8k follow-ups | **PixelML independently reproduced** (decode bands) - [PixelML GLM lane](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark) | NoPE sparse-MLA padding into SM120 geometry; DFlash2 padded slot-share allocator; XGrammar spec-decode backports; MNBT=2048 prefill ladder | DFlash2 draft CC BY-NC-ND 4.0; EXL3 ShapleyMCG 1.0; prose acceptance collapses (0.332 vs 0.918) | Port MNBT=2048 + prefix-cache bench into our GLM lane; then scored quality layer |
| [Qwen3.8-Flash-Next-Dual-DGX-Sparks](https://github.com/MiaAI-Lab/Qwen3.8-Flash-Next-Dual-DGX-Sparks) | `0f95001` | MIT | 2x GB10, SGLang TP2 | Qwen3.8-Flash-Next NVFP4 176B | 64 tok/s single, 117 agg x2 with NEXTN; NVFP4 KV cache for QSA layers | **PixelML independently reproduced** (our SGLang lane, different bands) - [PixelML Qwen lane](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark) | SM121 QSA kernel work upstream said was missing; NVFP4 KV dequant-workspace approach | Upstream numbers on different Spark pair; KLD not measured | Adopt its NVFP4-KV defaults review into our Qwen lane next run |
| [DeepSeek-v4-Flash-DSpark-2x-DGX-Spark](https://github.com/MiaAI-Lab/DeepSeek-v4-Flash-DSpark-2x-DGX-Spark) | `0107cef` | MIT | 2x GB10, vLLM TP2 | DS4F-0731 NVFP4 + DSpark K5 | 1M context, 2.49M-token KV pool, 2.38x concurrency ceiling | None | nvfp4_ds_mla KV + issue-22 long-context hotfix + P-core spin hotfix pattern | Not reproduced; numbers from one pair | Candidate for first PixelML DeepSeek lane if model becomes relevant |
| [DeepSeek-v4-Flash-One-DGX-Spark](https://github.com/MiaAI-Lab/DeepSeek-v4-Flash-One-DGX-Spark) | `fdcd538` | MIT | 1x GB10 TP1 | DS4F-0731 EXL3 3.0bpw + DSpark K5 | 44-47 tok/s structured; 439k KV pool; 370k exact needle recall | None | Single-node EXL3 path; prefill decays with depth (1024 -> 350-614 tok/s past 300k); boot-to-boot KV variance (~28k tokens) | 3bpw quality unassessed; one device | Single-node feasibility template for our single-node gap row |
| [GLM-5.2-NVFP4-AQLM-Triple-DGX-Sparks](https://github.com/MiaAI-Lab/GLM-5.2-NVFP4-AQLM-Triple-DGX-Sparks) | `5c85163` | MIT | 3x GB10, vLLM TP3 | GLM-5.2 NVFP4+AQLM hybrid | ~21 tok/s (nvfp4 KV, 348k ctx) vs ~25-26 (fp8 KV, 235k ctx) | None | Only 3-node recipe found; KV dtype trades context for decode; disable earlyoom on all nodes | Vision graft nascent; not reproduced | Triple-node topology candidate if a third Spark joins |
| [MiMo-V2.5-vLLM-Dual-DGX-Sparks](https://github.com/MiaAI-Lab/MiMo-V2.5-vLLM-Dual-DGX-Sparks) | `eb9c5fa` | none | 2x GB10 TP2 | MiMo-V2.5 Omni NVFP4-KV + MTP1 | 2.70M-token KV pool; 2 full-1M streams, third queues | None | KV pool math: concurrency x max_len reserves nothing; live tokens bound | No license file - reference only, do not copy code | Cite the KV accounting pattern in our memory guide |
| [Hy3-Dual-DGX-Spark](https://github.com/MiaAI-Lab/Hy3-Dual-DGX-Spark) | `d7510b5` | none | 2x GB10 TP2 | Hy3-295B NVFP4/W4A16 MARLIN | ~287k FP8 KV tokens; 2x full-128k or 1x 256k; earlyoom kills vLLM/Ray | None (PixelML recipe untested too) | earlyoom SIGTERM failure mode + fix; hybrid KV pool sizing table | No license file; no decode tok/s receipt | Our Hy3 lane should verify earlyoom behavior before first run |
| [Dual-DGX-Spark-Step-3.7-Flash-NVFP4](https://github.com/MiaAI-Lab/Dual-DGX-Spark-Step-3.7-Flash-NVFP4) | `475722b` | MIT | 2x GB10 TP2 | Step-3.7-Flash NVFP4 + MTP-3 | ~31-32 tok/s with MTP | None | Verify no-MTP before grafting MTP; tensor-size error signature | Not reproduced | Cross-check with our untested Step lane recipe |
| [Leanstral-1.5-119B-A6B_2x_DGX_Sparks_vLLM](https://github.com/MiaAI-Lab/Leanstral-1.5-119B-A6B_2x_DGX_Sparks_vLLM) | `94d7298` | none | 2x GB10 TP2 | Leanstral-1.5 119B BF16 | 262k context, 7 max seqs operational scripts | None | Minimal ops-script template; context-above-model-card caveat | No license file | None; formal-math workload out of scope |
| [DeepSeek-V4-Flash-Dual-DGX-Spark-1M-Context](https://github.com/MiaAI-Lab/DeepSeek-V4-Flash-Dual-DGX-Spark-1M-Context) | `d843199` | none | 2x GB10 | DS4F 1M ctx FP8 KV MTP2 | Superseded recipe | None | Upstream marks it OLD - kept only as history | Superseded upstream; do not use | Use DSpark-2x repo instead |

## Runtime, quantization, and speculative decoding

| Repository | Revision | License | Claimed result | Reproduction | Reusable learning | Limitations | Next experiment |
|---|---|---|---|---|---|---|---|
| [tool-eval-bench](https://github.com/MiaAI-Lab/tool-eval-bench) | `8eca976` | MIT | 84 deterministic tool-calling scenarios, pass/partial/fail, safety-capped rating | None (mirror of SeraphimSerapis/tool-eval-bench) | The quality layer our matrix lacks; deterministic scoring, safety gate at K<50% | Scores are stack+model properties, not weights alone | Wire tool-eval-bench into SparkQuant-Lab capability layer |
| [DS4F-Thinking-On-vs-Off-Benchmark](https://github.com/MiaAI-Lab/DS4F-Thinking-On-vs-Off-Benchmark) | `6554ca5` | none | Thinking ON +8 score but TC-60 sleeper-injection fail; OFF 30% faster | None | Thinking mode changes safety outcomes, not just speed; always report toggle state | Single model, single run pair | Make thinking-on/off a fixed axis in our eval defaults |
| [Agents-A1_vs_Qwen3.6-35B_tools_eval](https://github.com/MiaAI-Lab/Agents-A1_vs_Qwen3.6-35B_tools_eval) | `475722b` | none | Qwen3.6-35B-Q8 91.0 vs Agents-A1 83.4 mean; Pass^8 76.2 vs 64.3 | None | Pass@8 vs Pass^8 ceiling/floor framing for reliability | GGUF quants, temperatures differ between arms | Adopt Pass^k framing in SparkQuant-Lab reporting |
| [Best-Local-Model_Agentic-Workflows_2026](https://github.com/MiaAI-Lab/Best-Local-Model_Agentic-Workflows_2026) | `879b09b` | none | 7-model agentic ranking; Qwen3.6-35B-Q8 default; safety tiers | None | Deployability weighting (quality 70% + responsiveness 30%) | Rankings model-specific, single host | Reference framing only |

## Operations

| Repository | Revision | License | Claimed result | Reproduction | Reusable learning | Limitations | Next experiment |
|---|---|---|---|---|---|---|---|
| [sparkDash](https://github.com/MiaAI-Lab/sparkDash) | `7b47cd1` | MIT | Real-time multi-Spark dashboard: GPU/CPU/UM/storage/network + LLM probe (llama.cpp/vLLM/SGLang/ds4/EXL3), decode bench, vLLM health incl. KV %, queues, TTFT p95, prefix cache, MTP accept | Used read-only by PixelML (head dashboard) | Best-in-class fleet observability for Spark; vLLM Prometheus metric surfacing pattern | Monitoring only - measures nothing about model quality | Adopt its vLLM health metric set as our standard telemetry list |
