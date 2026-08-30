# SM121 troubleshooting

Measured workarounds for GB10 / SM121 / DGX Spark issues encountered during verified runs. Each entry states the symptom, root cause, and fix.

## NCCL hangs at init

**Symptom**: `ncclCommInitRank` hangs indefinitely; both containers stay alive but make no progress.

**Root cause**: NCCL discovers the wrong network interface. DGX Spark's on-board Ethernet does not carry RDMA traffic.

**Fix**: Pin NCCL to the CX7 interface and HCA:

```bash
export NCCL_SOCKET_IFNAME=<cx7-interface>
export NCCL_IB_HCA=<roce-interface>
```

Do not rely on default discovery. See [SETUP.md](SETUP.md#networking) for verification steps.

## MoE kernel failure (GLM-5.3-Flash NVFP4)

**Symptom**: vLLM crashes or produces garbage output with NVFP4 MoE weights.

**Root cause**: Default MoE kernel backend is not SM121-safe for this checkpoint.

**Fix**: Force the Marlin MoE kernel and eager execution:

```bash
--quantization moe_marlin --enforce-eager
```

This is the known-good configuration in the GLM-5.3-Flash recipe. CUDA graphs are not validated for this path.

## TRT-LLM QSA decode failure (Qwen3.8-Flash-Next)

**Symptom**: SGLang decode output is empty or produces token-0 tokens on SM121.

**Root cause**: The TRT-LLM QSA decode kernel is incompatible with SM121 in the pinned SGLang image.

**Fix**: Replace QSA decode with the Triton fallback and add a token-0 guard. See [qwen3-8-flash-next-sglang-2x-dgx-spark](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark) for the patch and tested image digest.

## EarlyOOM kills vLLM during model load

**Symptom**: Container or process killed during shard loading with a kernel OOM message.

**Root cause**: DGX Spark's unified memory means RSS spikes during model load; earlyoom interprets this as a system threat.

**Fix**: Disable earlyoom before launch:

```bash
sudo systemctl disable --now earlyoom
```

## Speculative decoding reduces throughput

**Symptom**: Enabling MTP/NEXTN/DFlash2 makes aggregate throughput worse, not better.

**Root cause**: Speculative decoding is prompt-dependent. Low acceptance rates or reduced scheduler capacity from draft-state allocation can erase the gain.

**Fix**: Benchmark with and without speculative decoding at your actual prompt shape. Compare single-stream and concurrent results separately.

Examples from measured runs:

- Qwen3.8-Flash-Next NEXTN/MTP improved single-stream decode by 82% but reduced effective max running requests from 36 to 25.
- GLM-5.3-Flash DFlash2 acceptance ranged from 91% (structured) to 31% (planning-heavy), producing a 2.4× decode speed range.

## Multimodal UMA failure (GLM-5.3-Flash)

**Symptom**: Image or video input fails under memory pressure that text-only requests handle.

**Root cause**: Unified-memory contention between multimodal preprocessing and the KV cache.

**Status**: Isolated once during revalidation; not fully resolved. See the GLM-5.3-Flash repo's revalidation receipt for details.

## Adding a new entry

Open a PR to this repo with the symptom, root cause, fix, and a link to the detailed receipt in the model-family repository. Label the fix **measured** only if you reproduced it on your own DGX Spark hardware.