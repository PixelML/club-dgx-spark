# GLM-5.3-Flash EXL3 upstream reference (MiaAI-Lab)

Upstream: [MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks](https://github.com/MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks/tree/79f10b91f84779b2b1ff2c9327b1a5847cd97f70) at revision `79f10b91f84779b2b1ff2c9327b1a5847cd97f70` (2026-08-29), MIT. Our public GLM lane pins [`3407023e0b8109a1dd12e8a5544e106ca6912afe`](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark/tree/3407023e0b8109a1dd12e8a5544e106ca6912afe) (validated receipts at [`aed98a13ca75140d2691cc5c651ea5817d9a3e44`](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark/tree/aed98a13ca75140d2691cc5c651ea5817d9a3e44)); upstream has since added the MNBT=2048 cold-prefill ladder.

## Provenance and licensing

| Component | Source | License |
|---|---|---|
| Serve recipe / overlay | MiaAI-Lab repo (MIT) | MIT |
| EXL3/TR3 4bpw weights | [brandonmusic/GLM-5.3-Flash-tr3-4bpw](https://huggingface.co/brandonmusic/GLM-5.3-Flash-tr3-4bpw/tree/5ab363a8dcf6405955fd5f99671e01a1c9fb124b) snapshot `5ab363a8dcf6405955fd5f99671e01a1c9fb124b` (byte-identical mirror at Mia-AiLab) | ShapleyMCG License 1.0 (HF license:other) |
| Base model | [zai-org/GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash/tree/04c4e9e95c5da8862dced7e5056455116f83a7e0) snapshot `04c4e9e95c5da8862dced7e5056455116f83a7e0` | MIT (upstream terms) |
| DFlash2 k=7 draft | [incoai/GLM-5.3-Flash-DFlash2](https://huggingface.co/incoai/GLM-5.3-Flash-DFlash2/tree/dc77ff1c99eeb2df044ee3d4f0094eb033fee410) snapshot `dc77ff1c99eeb2df044ee3d4f0094eb033fee410` (~2.3 GiB BF16) | CC BY-NC-ND 4.0 (research/eval) |
| KLD panel | [malaiwah HF discussion #1, comment #6a9144846b0bdba943bfe86f](https://huggingface.co/brandonmusic/GLM-5.3-Flash-tr3-4bpw/discussions/1#6a9144846b0bdba943bfe86f) (weights-level, not overlay) | community-reported |

PixelML vendors and attributes; it does not mirror weights or claim the
measurements below as its own.

## Runtime pins

- Image: ghcr.io/miaai-lab/glm-5.3-flash-2x-dgx-sparks:exl3, FROM vllm/vllm-openai:glm53-flash-arm64-cu130 (arm64, CUDA 13.0) — mutable tag; digest not yet pinned
- vLLM pin: [487ecf187d3dfe74d2cf6119a92881dba403c219](https://github.com/vllm-project/vllm/commit/487ecf187d3dfe74d2cf6119a92881dba403c219); ExLlamaV3 pin: [c5d9c657966ffeeaa9353f0cc899f18629da4a13](https://github.com/turboderp-org/exllamav3/commit/c5d9c657966ffeeaa9353f0cc899f18629da4a13) (0.0.43) exposing fused exl3_moe
- Target: sm_121a cubins, TORCH_CUDA_ARCH_LIST=12.1a
- Two source-exact vLLM XGrammar backports: [#52805](https://github.com/vllm-project/vllm/pull/52805/commits/12f64b39d29282437e35be9aa5db432fb2a1a6e6) ([12f64b39d29282437e35be9aa5db432fb2a1a6e6](https://github.com/vllm-project/vllm/commit/12f64b39d29282437e35be9aa5db432fb2a1a6e6)) and [#53046](https://github.com/vllm-project/vllm/pull/53046/commits/c6e19b3be24338759a443e03c8325d76da9ee202) ([c6e19b3be24338759a443e03c8325d76da9ee202](https://github.com/vllm-project/vllm/commit/c6e19b3be24338759a443e03c8325d76da9ee202))

## Requested gap rows

| Dimension | Upstream claim (community-reported) | PixelML status | Gap |
|---|---|---|---|
| Provenance / licensing | Full chain documented (table above) | Public lane pinned at `3407023e0b8109a1dd12e8a5544e106ca6912afe` with attribution | Refresh lane pin to upstream `79f10b91f84779b2b1ff2c9327b1a5847cd97f70` |
| arm64/CUDA13/sm_121a runtime + vLLM/ExLlamaV3 pins | Pins above; aarch64 allreduce stubs | Reproduced bring-up on the two-node DGX Spark pair | Record our image digest in next GLM receipt |
| DFlash2 k=7 vs MTP baseline | Structured 61.7 vs MTP k=2 ~24.6 tok/s lab protocol | Our lane measured 66.3 single-stream EXL3 | Run MTP-rollback A/B on our pair for a same-kit delta |
| Structured vs prose acceptance | Structured 0.918 accept vs prose 0.332; per-position decay published | Not measured separately by PixelML | Add prompt-shape axis to decode bench |
| Cold/warm TTFT | x1 719ms warm; x2 6.62s; x4 6.30s | Our receipts have TTFT tables | Align TTFT definitions with upstream for comparability |
| Prefix caching | Block-aligned 3584-token pages; ~90% reuse on 8k follow-ups; MNBT=2048 best | Not measured by PixelML | Port tests/bench_prefix_cache.py protocol |
| Long-context prefill | 256k cold 263s; 300k 319s; ~941-975 tok/s | Our stress test passed at 300k | Add cold-prefill ladder receipt |
| Vision / tools / reasoning | Vision on (image+video, skip-MM-profile), GLM tool parser, reasoning parser with stop suppression | Tools/reasoning gates passed (**measured**); vision mixed - throughput gates passed but one image gate failed under memory pressure during revalidation (**measured differently**) | Combine into one eval profile with fixed seeds |
| Reproducible tests | 11 test files + 2 benches upstream | Our lane adds concurrency/prefill benches | Cross-run upstream suite on our pair |
| Operational hardening | NIC-name vars, GID-index preflight, >=105.9 GiB free check, MNBT guard | Kit-specific adjustments documented in our lane | Fold NIC/GID preflight into club SETUP.md |
| Quality evidence | Weights-level KLD panel (4bpw 0.0246 vs FP8 0.0246 nats, ~54% bytes); externally reported | None scored by PixelML | Capability + fidelity layers planned in [EVAL-METHODOLOGY-GAP.md](EVAL-METHODOLOGY-GAP.md) |
| Energy / cost per success | Not measured upstream or by us | Gap for everyone | Add power sampling to template receipt |

## What PixelML can do with this

1. **Link**: cite upstream revision `79f10b91f84779b2b1ff2c9327b1a5847cd97f70` in every EXL3 receipt (do now, no GPU).
2. **Independently reproduce**: MNBT=2048 cold-prefill ladder + prefix-cache bench on our pair (GPU, ~2-4h, after cluster availability and workload-conflict checks).
3. **Carefully adapt**: thinking-on/off axis and Pass^k framing into the future quality layers (no GPU; see [EVAL-METHODOLOGY-GAP.md](EVAL-METHODOLOGY-GAP.md)).
4. **Not ours to claim**: KLD panel, upstream tok/s - they stay community-reported unless we re-measure.
