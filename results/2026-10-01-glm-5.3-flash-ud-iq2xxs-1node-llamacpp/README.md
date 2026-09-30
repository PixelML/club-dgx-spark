# GLM-5.3-Flash UD-IQ2_XXS on 1× DGX Spark — 262,144-token context, llama.cpp

Measured 2026-10-01 on one DGX Spark (GB10, SM121, arm64). Notebook:
[`notebooks/2026-10-01-glm-5.3-flash-ud-iq2xxs-1node-llamacpp.ipynb`](../../notebooks/2026-10-01-glm-5.3-flash-ud-iq2xxs-1node-llamacpp.ipynb).

**Verdict.** GLM-5.3-Flash (321B MoE) fits on ONE Spark at 2-bit and serves the
full **262,144-token context**, but it is slow: **15.1 tok/s decode**, ~350–380
tok/s prefill up to ~28k tokens, and a **245k-token prompt takes 28.8 min to
prefill** (8.3 tok/s decode afterwards). It is a one-node fallback, not the
throughput pick: the 4-bit EXL3 build on two Sparks is 2–4× faster at decode
(see the [cookbook](../../docs/cookbook/glm-5.3-flash-dgx-spark.md)).
Output quality at 2 bits is **untested** here.

## Tested configuration

- Hardware: 1 × DGX Spark, GB10 / SM121, 128 GB unified memory, driver 580.159.03.
- Model: `unsloth/GLM-5.3-Flash-GGUF` @ `621d456e93e926e4b52f85cff5f634358c1828f9`, `UD-IQ2_XXS` (97 GB).
- Runtime: llama.cpp `unslothai/llama.cpp` branch `glm5next/upstream` @ `86ebfef2c6a0f3359a2a07d2c215d61b0fa885c9`
  (ggml-org PR #27754, still open). Stock `server-cuda13` build 11277 fails with `unknown model architecture: 'glm5next'`.
- Flags: `-ngl 999 -c 262144 -np 1 -fa on -ctk q8_0 -ctv q8_0 -b 2048 -ub 1024 --jinja`.
- KV cache: q8_0 (indexer key cache stays f16). Context: 262,144 served; model native max 1,048,576.
- Speculative decoding: none. Parallelism: single node, 1 slot.
- Memory: 106 GB used after load, 114–115 GB of 119 GB after the 245k prompt (~4 GB free). No headroom for a second workload.

## Measured (temperature 0, median of 3; n=1 for ≥128k; tokens from the usage object)

| Workload | Prompt tokens | TTFT | Prefill tok/s | Decode tok/s |
|---|---:|---:|---:|---:|
| Short, thinking off | 33 | 0.65 s | — | 15.1 (14.8–15.1) |
| Short, thinking on | 22 | 0.36 s | — | 15.7 |
| Prefill ~7k | 7,398 | 19.6 s | 378 (375–378) | — |
| Prefill ~28k | 27,736 | 80.0 s | 346 (346–351) | — |
| Decode after ~28k context | 27,850 | 78.9 s | — | 13.9 (13.9–14.0) |
| 128k (n=1) | 127,533 | 601 s | 212 | 10.7 |
| 245k (n=1) | 244,570 | 1,730 s | 141 | 8.3 |

Prefill rate falls with context (attention cost), so long prompts are dominated by TTFT. Every prompt had a unique random prefix (no cache hits).

## Correctness gates

- [x] Coherent text; reasoning returned separately as `reasoning_content`
- [x] Tool call routed through a coding harness (shell tool, exact output returned)
- [ ] Multimodal: untested (text GGUF only, no projector loaded)
- [x] Container restart count 0 after all tests
- [ ] Quality at 2 bits: untested

## Limits

One node, 2-bit weights, one request at a time (`-np 1`), ~4 GB host memory free at full context, upstream PR still open (the build tracks a fork branch).

Harness and receipts: [`harness/`](harness/), [`receipts/`](receipts/).
