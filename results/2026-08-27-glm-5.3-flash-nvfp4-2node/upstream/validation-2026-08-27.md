# PixelML two-Spark NVFP4 validation — 2026-08-27

> Sanitized copy of `results/UPSTREAM-2026-08-27.md` from
> `PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark` @ `3407023e0b8109a1dd12e8a5544e106ca6912afe`
> (MIT). Redactions: private cluster name, NIC interface names, overlay-network
> route details, and local proxy alias names replaced with generic terms; see
> `../README.md` for the full redaction log. All measured values are unchanged.

This is an independent reproduction of the MiaAI-Lab dual-DGX-Spark recipe,
not a copy of the upstream benchmark table.

## Exact configuration

- Hardware: two NVIDIA DGX Spark systems, one GB10 GPU per node, direct CX7
  RoCE (the QSFP port pair).
- Model: `LibertAIDAI/GLM-5.3-Flash-NVFP4` revision
  `11d73216cd636238e82e1d77fe1042ffab36e7fa` (120 shards, 181.29 GiB).
- Recipe base: `MiaAI-Lab/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark` commit
  `aed98a1`.
- Runtime: vLLM `0.1.dev20051+g487ecf187`, Ray TP=2, FlashInfer
  `0.6.18.dev20260819`, NCCL `2.30.7`.
- Kernels: patched SM90 sparse-MLA + FA2 on SM121; Marlin weight-only NVFP4
  MoE; FlashInfer CUTLASS NVFP4 dense GEMM.
- Decode: MTP speculative decoding with four draft tokens; FP8 E4M3 KV;
  eager execution.
- Context: 262,144 tokens; 431,157 total KV-cache tokens; 8.5 GiB KV.
- Scheduler: `max-num-seqs=8`; effective simultaneous short-request capacity
  is seven for this KV/page layout.
- API: authenticated with `VLLM_API_KEY`; every tested route returned HTTP 401
  without a key.

## Correctness gates

All gates passed through the direct vLLM API and again through the local
CLIProxy alias where applicable:

- Low-effort coding returned a complete Python binary-search implementation
  (`stop`, 90 output tokens, 2.715 seconds).
- High-effort reasoning was separated from the final `$60` answer.
- Forced/automatic tool routing emitted exactly `get_weather`.
- A generated solid-red PNG returned `Red`.
- Fresh ephemeral OpenCodex runs returned `GLM_LOCAL_OK` through the local
  CLIProxy alias and `GLM_PUBLIC_OK` through the public proxy alias.
- Both rank containers remained `running` with restart count zero after the
  full test matrix.

The refreshed checkpoint template supports exactly `low`, `high`, and `max`
for the top-level OpenAI-compatible `reasoning_effort` field. vLLM exposes
reasoning in `message.reasoning`; clients should not assume the field is named
`reasoning_content`.

## TPS methodology

Each request asks for a compact Python topological-order validator, sets
`reasoning_effort=low`, `temperature=0`, `ignore_eos=true`, and forces exactly
256 output tokens. Streaming client timestamps record TTFT and wall time. Each
row below is the median of three fully warm runs; the range contains all three
aggregate measurements.

| Concurrency | Median aggregate e2e tok/s | Three-run range | Median mean-stream decode tok/s | Median TTFT |
|---|---:|---:|---:|---:|
| ×1 | 26.55 | 24.10–27.00 | 27.69 | 0.432s |
| ×2 | 43.19 | 42.64–44.50 | 25.27 | 0.538s |
| ×4 | 58.36 | 51.74–58.47 | 17.64 | 0.481s |
| ×6 | 80.57 | 79.58–93.83 | 16.11 | 0.560s |
| ×7 | **82.12** | 72.77–84.84 | 14.01 | 0.499s |
| ×8 | 69.85 | 69.50–73.63 | 15.27 | 2.908s |

Server telemetry briefly reached 82.9 generated tok/s during the first ×8
gate. Client-observed ×7 is the better production operating point because all
seven requests run immediately; at ×8, vLLM reports seven running and one
waiting with about 96% KV use.

## MTP behavior

Observed average draft acceptance varied by workload and concurrency, roughly
47–73%, with mean accepted lengths around 2.7–3.9 tokens. That variation is why
the report publishes three-run medians and ranges rather than one peak.

## Cold start

The first start took 15 minutes 18 seconds from head-container launch to
authenticated API readiness. Rank-zero model loading reported 91.23 GiB and
676.17 seconds; engine profile/KV/warm-up took another 133.79 seconds,
followed by multimodal API warm-up. JIT and FlashInfer caches persist in a
Docker volume, so subsequent starts reuse compiled artifacts.

## Why SGLang was not selected on GB10

The official SGLang path was tested first with TP=2/EP=2, online ModelOpt
NVFP4, FP8 KV, and the available SM120/SM121 sparse-MLA backend. Weight loading
completed in 1,880.41 seconds, but the first real decode failed: the packed
SM120 GLM kernel requires `qk_rope_head_dim=64` and query dimension 576, while
GLM-5.3 is NoPE with `qk_rope_head_dim=0` and query dimension 512. TensorRT-LLM
DSA also rejected SM121, and TileLang DSA exceeded GB10's allowed dynamic shared
memory. The selected vLLM patch deliberately routes SM121 through the SM90
NoPE sparse-MLA + FA2 implementation instead of altering the checkpoint.

## Security note

This fork passes `VLLM_API_KEY` into both generated containers without placing
the secret in `EXTRA_ARGS`, generated launcher text, or startup logs. vLLM API
keys protect OpenAI-compatible routes, not every diagnostic route; expose the
service only behind a restrictive network or reverse proxy.
