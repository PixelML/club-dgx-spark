# SM121 troubleshooting

Workarounds for GB10 / SM121 / DGX Spark issues. Each entry states its evidence
label (measured, community-reported, or inferred), the symptom, root cause, and
fix, with a commit-pinned receipt or patch link for every measured entry.

## NCCL hangs at init

**Evidence**: measured (GLM/Qwen lanes); community-reported for the same symptom upstream.
**Receipts**: [GLM lane @ `3407023e`](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark/tree/3407023e0b8109a1dd12e8a5544e106ca6912afe/results) · [Qwen lane @ `682504be`](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark/tree/682504bec9e7e99206212f4e172b7ec823e4605c/results)

**Symptom**: `ncclCommInitRank` hangs indefinitely; both containers stay alive but make no progress.

**Root cause**: NCCL discovers the wrong network interface. DGX Spark's on-board Ethernet does not carry RDMA traffic.

**Fix**: Pin NCCL to the CX7 interface and HCA:

```bash
CX7_IFNAME="${CX7_IFNAME:?run ip link here and set the CX7 port name}"
ROCE_HCA="${ROCE_HCA:?run ibstat here and set the RoCE HCA name}"
export NCCL_SOCKET_IFNAME="$CX7_IFNAME"
export NCCL_IB_HCA="$ROCE_HCA"
```

Do not rely on default discovery. See [SETUP.md](SETUP.md#networking) for verification steps.

## MoE kernel failure (GLM-5.3-Flash NVFP4)

**Evidence**: measured (GLM lane receipts).
**Receipt**: [GLM lane @ `3407023e`](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark/tree/3407023e0b8109a1dd12e8a5544e106ca6912afe/results)

**Symptom**: vLLM crashes or produces garbage output with NVFP4 MoE weights.

**Root cause**: Default MoE kernel backend is not SM121-safe for this checkpoint.

**Fix**: Force the Marlin MoE kernel and eager execution:

```bash
--quantization moe_marlin --enforce-eager
```

This is the known-good configuration in the GLM-5.3-Flash recipe. CUDA graphs are not validated for this path.

## TRT-LLM QSA decode failure (Qwen3.8-Flash-Next)

**Evidence**: measured (Qwen lane receipts).
**Receipt + patch**: [qwen3-8-flash-next-sglang-2x-dgx-spark @ `682504be`](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark/tree/682504bec9e7e99206212f4e172b7ec823e4605c)

**Symptom**: SGLang decode output is empty or produces token-0 tokens on SM121.

**Root cause**: The TRT-LLM QSA decode kernel is incompatible with SM121 in the pinned SGLang image.

**Fix**: Replace QSA decode with the Triton fallback and add a token-0 guard. See [qwen3-8-flash-next-sglang-2x-dgx-spark](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark) for the patch and tested image digest.

## EarlyOOM kills vLLM during model load

**Evidence**: community-reported (Hy3 upstream reports; not reproduced in a PixelML lane).

**Symptom**: Container or process killed during shard loading with a kernel OOM message.

**Root cause**: DGX Spark's unified memory means RSS spikes during model load; earlyoom interprets this as a system threat.

**Fix**: Stop the authorized earlyoom service around model load, then restart it afterward (scoped and reversible):

```bash
sudo systemctl stop earlyoom      # before launch, if authorized
# ... run the load ...
sudo systemctl start earlyoom     # restore afterward
```

## Speculative decoding reduces throughput

**Evidence**: measured (GLM DFlash2 acceptance spread 31-91% by prompt shape).
**Receipts**: [GLM DFlash2 @ `3407023e`](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark/tree/3407023e0b8109a1dd12e8a5544e106ca6912afe/results) · [Qwen NEXTN @ `682504be`](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark/tree/682504bec9e7e99206212f4e172b7ec823e4605c/results)

**Symptom**: Enabling MTP/NEXTN/DFlash2 makes aggregate throughput worse, not better.

**Root cause**: Speculative decoding is prompt-dependent. Low acceptance rates or reduced scheduler capacity from draft-state allocation can erase the gain.

**Fix**: Benchmark with and without speculative decoding at your actual prompt shape. Compare single-stream and concurrent results separately.

Examples from measured runs:

- Qwen3.8-Flash-Next NEXTN/MTP improved single-stream decode by 82% but reduced effective max running requests from 36 to 25.
- GLM-5.3-Flash DFlash2 acceptance ranged from 91% (structured) to 31% (planning-heavy), producing a 2.4× decode speed range.

## Multimodal UMA failure (GLM-5.3-Flash)

**Evidence**: measured once during revalidation; not fully resolved.
**Receipt**: [GLM revalidation @ `3407023e`](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark/tree/3407023e0b8109a1dd12e8a5544e106ca6912afe/results)

**Symptom**: Image or video input fails under memory pressure that text-only requests handle.

**Root cause**: Unified-memory contention between multimodal preprocessing and the KV cache.

**Status**: Isolated once during revalidation; not fully resolved. See the GLM-5.3-Flash repo's revalidation receipt for details.

## Adding a new entry

Open a PR to this repo with the symptom, root cause, fix, and a link to the detailed receipt in the model-family repository. Label the fix **measured** only if you reproduced it on your own DGX Spark hardware.

## SGLang engine dies every 10-15 minutes with "pool memory leak detected"

**Image:** `lmsysorg/sglang` `0.0.0.dev1+gd91c3682b` (measured; likely wider).

**Symptom:** during a long benchmark or unattended session the scheduler raises

```
ValueError: pool memory leak detected! [full] total=..., available=..., evictable=...
[mamba] total=130, available=126, ..., leaked_full_pages={...}
```

and the process is SIGQUIT'd. With `--restart unless-stopped` this becomes a
reload loop costing ~10 minutes each time. Preceding decode lines show a rising
`mamba num:` while `#running-req` is 1 -- linear-attention states retained
alongside the radix cache.

**Cause:** this build defaults `SGLANG_ENABLE_STRICT_MEM_CHECK_DURING_IDLE=True`,
so `invariant_checker._report_leak` calls `raise_error_or_warn(..., strict=True)`
and a few-thousand-token accounting drift out of ~570k becomes fatal.

**Fix:** set `SGLANG_ENABLE_STRICT_MEM_CHECK_DURING_IDLE=0` to demote it to a
warning. Measured: four deaths in the first 40 minutes with the default; hours of
clean running with it set to 0.

**Related traps on the same image:** `ignore_eos` and `min_tokens` trip the same
check on the first request that uses them; `/flush_cache` between blocks does not
prevent it; and `/v1/completions` rejects `echo` + `logprobs` ("use the native
`/generate` API") if you need teacher-forced input logprobs.
