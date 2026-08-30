# GLM-5.3-Flash EXL3 upstream reference (MiaAI-Lab)

Upstream: [MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks](https://github.com/MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks) at revision `79f10b91f84779b2b1ff2c9327b1a5847cd97f70` (2026-08-29), MIT. Our vendored lane pins `bd7f55e`; upstream has since added the MNBT=2048 cold-prefill ladder.

## Provenance and licensing

| Component | Source | License |
|---|---|---|
| Serve recipe / overlay | MiaAI-Lab repo (MIT) | MIT |
| EXL3/TR3 4bpw weights | brandonmusic/GLM-5.3-Flash-tr3-4bpw snapshot 5ab363a8 (byte-identical mirror at Mia-AiLab) | ShapleyMCG License 1.0 |
| Base model | zai-org/GLM-5.3-Flash | upstream terms |
| DFlash2 k=7 draft | incoai/GLM-5.3-Flash-DFlash2 (~2.3 GiB BF16) | CC BY-NC-ND 4.0 (research/eval) |
| KLD panel | malaiwah HF discussion (weights-level, not overlay) | community-reported |

PixelML vendors and attributes; it does not mirror weights or claim the
measurements below as its own.

## Runtime pins

- Image: ghcr.io/miaai-lab/glm-5.3-flash-2x-dgx-sparks:exl3, FROM vllm/vllm-openai:glm53-flash-arm64-cu130 (arm64, CUDA 13.0)
- vLLM pin: 487ecf187; ExLlamaV3 pin: c5d9c657 (0.0.43) exposing fused exl3_moe
- Target: sm_121a cubins, TORCH_CUDA_ARCH_LIST=12.1a
- Two source-exact vLLM XGrammar backports: #52805 (12f64b39) and #53046 (c6e19b3)

## Requested gap rows

| Dimension | Upstream claim (community-reported) | PixelML status | Gap |
|---|---|---|---|
| Provenance / licensing | Full chain documented (table above) | Vendored at bd7f55e with attribution | Refresh vendored pin to 79f10b9 in the GLM lane |
| arm64/CUDA13/sm_121a runtime + vLLM/ExLlamaV3 pins | Pins above; aarch64 allreduce stubs | Reproduced bring-up on Apollo pair | Record our image digest in next GLM receipt |
| DFlash2 k=7 vs MTP baseline | Structured 61.7 vs MTP k=2 ~24.6 tok/s lab protocol | Our lane measured 66.3 single-stream EXL3 | Run MTP-rollback A/B on our pair for a same-kit delta |
| Structured vs prose acceptance | Structured 0.918 accept vs prose 0.332; per-position decay published | Not measured separately by PixelML | Add prompt-shape axis to decode bench |
| Cold/warm TTFT | x1 719ms warm; x2 6.62s; x4 6.30s | Our receipts have TTFT tables | Align TTFT definitions with upstream for comparability |
| Prefix caching | Block-aligned 3584-token pages; ~90% reuse on 8k follow-ups; MNBT=2048 best | Not measured by PixelML | Port tests/bench_prefix_cache.py protocol |
| Long-context prefill | 256k cold 263s; 300k 319s; ~941-975 tok/s | Our stress test passed at 300k | Add cold-prefill ladder receipt |
| Vision / tools / reasoning | Vision on (image+video, skip-MM-profile), GLM tool parser, reasoning parser with stop suppression | Gates passed in our receipts | Combine into one eval profile with fixed seeds |
| Reproducible tests | 11 test files + 2 benches upstream | Our lane adds concurrency/prefill benches | Cross-run upstream suite on our pair |
| Operational hardening | NIC-name vars, GID-index preflight, >=105.9 GiB free check, MNBT guard | Kit-specific adjustments documented in our lane | Fold NIC/GID preflight into club SETUP.md |
| Quality evidence | Weights-level KLD panel (4bpw 0.0246 vs FP8 0.0246 nats, ~54% bytes); externally reported | None scored by PixelML | SparkQuant-Lab capability + fidelity layers |
| Energy / cost per success | Not measured upstream or by us | Gap for everyone | Add power sampling to template receipt |

## What PixelML can do with this

1. **Link**: cite upstream revision 79f10b9 in every EXL3 receipt (do now, no GPU).
2. **Independently reproduce**: MNBT=2048 cold-prefill ladder + prefix-cache bench on our pair (GPU, ~2-4h, after Apollo checks).
3. **Carefully adapt**: thinking-on/off axis and Pass^k framing into SparkQuant-Lab (no GPU).
4. **Not ours to claim**: KLD panel, upstream tok/s - they stay community-reported unless we re-measure.
