# Benchmark methodology

This is the shared methodology used across DGX Spark benchmark receipts. Model repos may add model-specific details but must not weaken these rules.

## Uncached prefill

1. Each request begins with a unique randomized prefix so the prompt cache cannot help.
2. Request exactly one output token so decode cost is negligible.
3. Divide the API-reported `prompt_tokens` (from the usage object or the response's token count) by the time to first content or reasoning token. This is a client-observed rate including HTTP, tokenization, scheduling, and the first decode step.
4. Calibrate the prompt to within ~5% of the target size against the API's reported token count.
5. Warm once at the calibrated size, then measure three samples. Report median and full range.
6. After the run, check server logs for `#cached-token: 0` in every prefill batch. If any cache hits occurred, discard the run.

## Decode throughput

1. Use a fixed prompt shape (same tokens, same reasoning effort, same temperature).
2. Set `ignore_eos=true` and request a fixed output-token count so all streams finish at the same length.
3. For concurrent runs, launch all streams simultaneously and measure client-side wall time from first-stream start to last-stream finish.
4. Aggregate tok/s is `total_output_tokens / wall_time_seconds`.
5. Per-stream tok/s is each stream's output tokens divided by that stream's individual completion time.
6. Take the median of three independent request sets. Report the range.
7. Count tokens from the final usage object in the streaming response, never by summing delta events, unless the API contract explicitly documents a different counting rule.

## Correctness gates

Every benchmark receipt must confirm at minimum:

- The model produces coherent text (not gibberish, not a loop, correct stop condition).
- The container or process remains healthy with restart count zero after the full test.
- Tool calls (if the model supports them) route to the correct function.
- Multimodal input (if the model supports it) returns the expected answer.

## What to record

- Hardware: GPU count, node topology, interconnect. Use generic terms ("DGX Spark node", "dual-node TP=2").
- Software: model revision, runtime version, container image digest, driver/CUDA if known.
- Configuration: context length, quantization, KV cache dtype, speculative decoding settings, scheduler limits.
- Workload: prompt shape, output length, concurrency, sample count, seed.
- Metrics: throughput, latency, TTFT, memory. Thermal/power when available.
- Failures: preserve any error, restart, OOM, or NCCL failure even if the rest of the run succeeded.

## What not to do

- Do not cherry-pick the best run. Report median and range.
- Do not compare uncached prefill tok/s to aggregate decode tok/s — they measure different things.
- Do not report a number without its configuration and evidence link.
- Do not publish a claim without labeling it measured, inferred, community-reported, or untested.