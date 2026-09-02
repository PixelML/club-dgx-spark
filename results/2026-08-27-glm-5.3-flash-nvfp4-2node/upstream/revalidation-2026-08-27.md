# PixelML two-Spark full revalidation — 2026-08-27

> Sanitized copy of `results/UPSTREAM-2026-08-27-REVALIDATION.md` from
> `PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark` @ `3407023e0b8109a1dd12e8a5544e106ca6912afe`
> (MIT). Redactions: private cluster name and local proxy alias names replaced
> with generic terms; see `../README.md` for the full redaction log. All
> measured values are unchanged.

This pass revalidated the warm dual-DGX-Spark deployment with three independent
questions: uncached prefill speed, repeated decode speed, and behavior inside a
real coding-agent harness. It also isolated a multimodal UMA failure that the
earlier smoke test did not reproduce.

## Runtime under test

- Two DGX Spark nodes, Ray tensor parallel 2 over the direct CX7 link.
- `LibertAIDAI/GLM-5.3-Flash-NVFP4` revision
  `11d73216cd636238e82e1d77fe1042ffab36e7fa`.
- vLLM `0.1.dev20051+g487ecf187`; upstream recipe commit `aed98a1`.
- ModelOpt NVFP4 weights, Marlin MoE, FP8 E4M3 KV, MTP-4, eager execution.
- 262,144-token context, `GPU_MEM_UTIL=0.84`, `max-num-seqs=8`.
- Authenticated direct API plus a local CLIProxy/OpenCodex alias.

## Uncached prefill

`prefill-benchmark.py` calibrates each prompt against the API-reported token
count. Every measured sample begins with a unique randomized prefix, requests
one output token, and records client TTFT. Input throughput is prompt tokens
divided by TTFT, so it includes HTTP, tokenization, queueing, prefill, and the
first decode step.

| Target | Median actual prompt | Median TTFT | Median input tok/s | Three-run range |
|---|---:|---:|---:|---:|
| 1K | 1,048 | 0.8206s | 1,276.65 | 1,274.69–1,288.94 |
| 4K | 4,131 | 3.0105s | 1,371.87 | 1,364.91–1,372.45 |
| 16K | 16,553 | 12.1670s | 1,362.75 | 1,349.84–1,363.53 |

The complete run used seed `1787822600564263149`. Server counters after all
prefill and decode work reported 142,694 prefix-cache queries, zero hits, and
zero cached prompt tokens. These are uncached rates, not warm-prefix numbers.

## Fresh structural decode matrix

Each row is the median of three requests sets. Every stream uses the same small
coding prompt, `reasoning_effort=low`, `temperature=0`, `ignore_eos=true`, and
exactly 256 output tokens. The range contains the three client-observed
aggregate measurements.

| Concurrency | Median aggregate tok/s | Three-run range | Median mean-stream decode tok/s | Median TTFT |
|---|---:|---:|---:|---:|
| ×1 | 27.28 | 22.74–29.01 | 28.26 | 0.359s |
| ×2 | 40.10 | 36.04–47.32 | 22.95 | 0.477s |
| ×4 | 56.00 | 42.92–56.54 | 16.53 | 0.526s |
| ×6 | **67.55** | 63.38–69.89 | 14.80 | 0.555s |
| ×7 | 64.88 | 59.80–66.69 | 16.46 | 2.816s |
| ×8 | 65.60 | 64.67–67.83 | 16.13 | 4.684s |

The fresh no-queue sweet spot was six streams. Seven and eight showed queueing
in TTFT. This run is lower than the earlier 82.12 tok/s ×7 median, which is why
both measured passes are retained rather than replacing the earlier result
with a cherry-picked peak.

Across the full controlled pass, all 103 requests finished with
`finish_reason=length`; there were no aborts, repetition errors, container
restarts, or cache hits before the separate vision test.

## Coding-agent loop regression

A fresh ephemeral OpenCodex run selected the local proxy alias. GLM was
explicitly instructed to inspect the recipe itself with local read-only tools,
without delegation. It enumerated the repository, read the README, benchmark,
launch/download/build paths, kernel patch, validation report, and Git history,
then returned a structured purpose/architecture/risk assessment.

- Input tokens: 111,106; cached input tokens: 0.
- Output tokens: 4,002.
- Multiple coherent command executions completed with exit code zero.
- Final turn completed normally with no repeated-punctuation loop.
- It independently found a real recipe bug: `benchmark.py` defaulted to port
  8889 while the public recipe serves on 8888. This revalidation fixes it.

OpenCodex first attempted the Responses WebSocket route, received HTTP 426 from
the local proxy, fell back to the supported HTTP path, and completed the turn.
The model route itself is therefore usable for repo-scale coding-agent work.

## Functional gates and vision failure

On the final pre-restart functional pass:

- Coding returned a complete binary-search implementation: 90 tokens in
  2.711 seconds, or 33.2 client-observed e2e output tok/s.
- High reasoning separated reasoning from the correct `$60` final answer.
- Automatic tool routing emitted exactly `get_weather`.
- The image gate returned HTTP 500 and terminated the vLLM engine.

The root cause was Ray's node-memory monitor, not a malformed model response or
CUDA kernel error. The first 32×32 image request caused node use to reach
124,136,656,896 bytes, 6,606,848 bytes above Ray's 95% threshold of
124,130,050,048 bytes. Ray killed the TP0 worker, then vLLM shut down. The
earlier result file records a successful image smoke test on a prior start, so
the path is nondeterministic at this memory margin and is not production-safe.

The published benchmark now makes vision opt-in with `--include-vision`.
For multimodal production, reduce `GPU_MEM_UTIL` or pin a smaller KV cache and
repeat the image/video gates. Raising or disabling Ray's memory monitor without
first creating real UMA headroom can turn a controlled Ray kill into a host OOM
and is not the recommended first fix.

## Operational conclusion

The current dual-Spark profile is validated for text coding, reasoning, tool
calling, uncached long-context prefill, concurrency, CLIProxy, and OpenCodex.
Treat it as a text-first max-throughput profile. Vision remains experimental
until a lower-memory profile is separately benchmarked.
