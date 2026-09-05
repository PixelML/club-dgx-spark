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

## vLLM loads mixed-precision ModelOpt NVFP4 that SGLang cannot (2x Spark, TP2)

**Evidence**: measured (Qwen3.8-Flash-Next lane, 2026-09-05).
**Receipt**: [Qwen lane @ `1b3d154`](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark/tree/codex/nvidia-nvfp4-vllm-tp2/results/2026-09-05-nvidia-nvfp4-vllm-tp2)

**Symptom**: A ModelOpt checkpoint whose `hf_quant_config.json` says `quant_algo: MIXED_PRECISION` (MoE experts FP4, attention and shared experts BF16) is killed by the host OOM killer during weight loading under SGLang's `modelopt_mixed` path, at `MEM_FRACTION_STATIC` 0.80 and again at 0.70.

**Root cause**: engine-specific loader behaviour, not the checkpoint or the hardware.

**Fix**: load it under upstream vLLM instead. The same checkpoint on the same two Sparks loads at `Model loading took 61.13 GiB memory and 407.05 seconds` per node, TP=2, with `--quantization modelopt` (vLLM reads `hf_quant_config.json` and resolves it to `modelopt_mixed` itself). Note this is a load result only — that run did not reach serving, for the unified-memory reason in the next entry.

## Multi-node TP under upstream vLLM needs no Ray, but the follower needs `--headless`

**Evidence**: measured (Qwen3.8-Flash-Next lane, 2026-09-05).
**Receipt**: [Qwen lane @ `1b3d154`](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark/tree/codex/nvidia-nvfp4-vllm-tp2/results/2026-09-05-nvidia-nvfp4-vllm-tp2)

**Symptom**: Two-node TP starts, both nodes load weights, then the follower's EngineCore aborts:

```
AssertionError: collective_rpc should not be called on follower node
```

and the head hangs waiting for a peer that is gone.

**Root cause**: Ray is not installed in the upstream `vllm/vllm-openai` image and is not needed — `--nnodes / --node-rank / --master-addr / --master-port` drive multi-node TP natively. But only rank 0 may run an API server. A follower launched with the head's command minus the rank number still tries to serve, and issues collective RPCs it must not.

**Fix**: pass `--headless` on every node with `--node-rank` != 0, and keep everything else identical between ranks.

## `--gpu-memory-utilization` does not mean on GB10 what it means on a discrete GPU

**Evidence**: measured symptom (Qwen3.8-Flash-Next lane, 2026-09-05); root cause inferred, not logged.
**Receipt**: [Qwen lane @ `1b3d154`](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark/tree/codex/nvidia-nvfp4-vllm-tp2/results/2026-09-05-nvidia-nvfp4-vllm-tp2)

**Symptom**: vLLM finishes weight loading on both nodes, logs the attention/mamba page-size setup, then goes silent. Minutes later both Sparks stop answering SSH — and eventually ICMP — with no traceback and no OOM line. The API port never opens.

**Root cause (inferred)**: GB10's ~120 GiB is **unified** — host and device draw on one pool. `--gpu-memory-utilization 0.85` reserves 85% of that pool for the engine while the host-side runtime is still allocating from the same pool during post-load profiling and CUDA-graph capture. On the discrete B200/B300 that upstream recipes are tuned against, those are two separate budgets. With a 61 GiB per-node weight load, 0.85 left too little for the rest.

**Fix**: start at **0.70-0.75** on a Spark, not at the 0.85-0.90 an x86 recipe suggests, and watch **host** free memory through the profiling stage rather than only the GPU pool. Related: the earlyoom entry above covers the case where the kill does get logged; this one is the case where the box thrashes instead and has to be power-cycled.

## `torch.cuda.get_arch_list()` omits `sm_121` and the image still runs

**Evidence**: measured (Qwen3.8-Flash-Next lane, 2026-09-05).
**Receipt**: [Qwen lane @ `1b3d154`](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark/tree/codex/nvidia-nvfp4-vllm-tp2/results/2026-09-05-nvidia-nvfp4-vllm-tp2)

**Symptom**: A candidate container reports `['sm_80', 'sm_90', 'sm_100', 'sm_110', 'sm_120']` with no `sm_121`, which looks like it rules the image out for GB10.

**Root cause**: CUDA family compatibility covers `sm_121` from `sm_120` binaries.

**Fix**: do not screen images on the arch list. Screen them by running on the device: `torch.cuda.get_device_capability()` returning `(12, 1)` plus a real bf16 matmul takes ten seconds and is the answer that counts. The upstream `vllm/vllm-openai:nightly-*` arm64 images pass this despite the arch list.

## Adding a new entry

Open a PR to this repo with the symptom, root cause, fix, and a link to the detailed receipt in the model-family repository. Label the fix **measured** only if you reproduced it on your own DGX Spark hardware.
