# Qwen3.8-Flash-Next: official NVIDIA NVFP4 vs community NVFP4 on GB10 — 2026-09-05

## Outcome

**Measured.** NVIDIA's official `nvidia/Qwen3.8-Flash-Next-NVFP4` cannot be served
on 2× DGX Spark by the SGLang recipe that runs the community NVFP4 build of the
same model: it is killed by the host OOM killer during weight loading, at both the
published `mem-fraction-static` 0.80 and a more conservative 0.70. The community
NVFP4 checkpoint loads and serves on the same two nodes, same image, same flags,
minutes before and after.

## Why this generalises beyond one model

"Official NVFP4" and "community NVFP4" are not the same artifact class, and size
does not tell you which you have. Check `hf_quant_config.json` before assuming a
vendor checkpoint is a drop-in:

| | community (RadixArk) | official (NVIDIA) |
|---|---|---|
| `quant_algo` | `NVFP4` (uniform) | `MIXED_PRECISION` |
| excluded modules | 13 wildcards | 292 explicit |
| `quantized_layers` map | absent | present, 50 entries |
| actually in FP4 | all non-excluded linears | `mlp.experts` only |
| runtime flag needed | `modelopt_fp4` | `modelopt_mixed` |
| on-disk size | 126,586 MiB | 126,586 MiB |
| BF16 tensors | 16.0 GB | **11.0 GB** |

The official build is the *smaller* one in high-precision tensors and still OOMs,
so the cost is in the `modelopt_mixed` load path, not the weights. On a 120 GiB
unified-memory node that difference decides whether the model runs at all.

**Check the vendor card's supported matrix first.** NVIDIA's card lists vLLM as
the only supported runtime and B200/B300 as the supported hardware. GB10 and
SGLang are outside both, so this is a boundary finding, not a defect report.

## Reusable engine finding for this SGLang image

`lmsysorg/sglang` `0.0.0.dev1+gd91c3682b` defaults
`SGLANG_ENABLE_STRICT_MEM_CHECK_DURING_IDLE=True`. Under sustained mixed-length
load the KV/mamba page accounting drifts by a few thousand tokens out of ~570k
(the engine logs a rising `mamba num:` while `#running-req` is 1) and the strict
check turns that drift into a fatal `ValueError: pool memory leak detected!`.

**Measured:** four engine deaths in the first 40 minutes of a prompt-length sweep,
each costing a ~10 minute reload. With the variable set to `0` the same sweep ran
for hours. Short benchmarks never hit this, which is why it does not show up in
published single-shot numbers. Anyone doing long unattended runs on this image
should set it explicitly.

Two related traps on the same image: `ignore_eos` / `min_tokens` trip the identical
check immediately, and `/v1/completions` refuses `echo` + `logprobs` outright
("use the native `/generate` API") if you want teacher-forced input logprobs.

## Also measured: the community checkpoint's full context ladder

Ten prompt lengths, 327 → 258k tokens, thinking off/on, cold + warm + 4 reps,
512-token outputs, SGLang TP=2 with NEXTN/MTP. Generation is flat at **40–62
tok/s across a 780× range of prompt length**, with warm TTFT staying under 1 s
while cold TTFT climbs to 107 s at 256k.

One cliff, at maximum context **with thinking enabled** (~258k prompt tokens):
speculative acceptance collapses to exactly **1.00**, generation falls to **7.6
tok/s** against 43.7 tok/s at the same length with thinking off, and warm TTFT
(163 s) exceeds cold TTFT (100 s). The SM121 token-0 guard fires there, and the
engine can afterwards wedge with HTTP still answering while the scheduler stops.

## Evidence

Full receipts, raw per-sample data, the 3×3 chart, and the OOM logs:
[PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark#5](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark/pull/5)

## Attribution

- NVIDIA — [`nvidia/Qwen3.8-Flash-Next-NVFP4`](https://huggingface.co/nvidia/Qwen3.8-Flash-Next-NVFP4), quantized with Model Optimizer v0.46.0, NVIDIA Open Model License.
- RadixArk — [`RadixArk/Qwen3.8-Flash-Next-NVFP4`](https://huggingface.co/RadixArk/Qwen3.8-Flash-Next-NVFP4), the community NVFP4 conversion.
- Qwen — [`Qwen/Qwen3.8-Flash-Next`](https://huggingface.co/Qwen/Qwen3.8-Flash-Next), Qwen Community License 1.0.
- MiaAI-Lab — the SM121 QSA fallback and token-0 guard ported by the lane recipe.
