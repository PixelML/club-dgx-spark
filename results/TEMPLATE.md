# Result submission template

Copy this template into the model-family repository's `results/` directory, then add a summary row to [`results/SUMMARY.md`](SUMMARY.md) here.

```markdown
# <Model> <quantization> validation — YYYY-MM-DD

## Outcome

One-sentence headline with the key measured number.

## Tested configuration

- Hardware: N × DGX Spark, GB10 / SM121, one GPU per node.
- Interconnect: direct CX7 RoCE.
- Model revision: <repo/checkpoint @ commit or revision hash>.
- Runtime and version: <vLLM/SGLang version or image digest>.
- Quantization: <NVFP4 / AWQ / GPTQ / EXL3 / BF16 / ...>.
- KV cache: <dtype and size>.
- Speculative decoding: <method, draft length, or "none">.
- Context: <max tokens>.
- Parallelism: <TP=N, PP=N, or "single node">.
- Power mode: <max performance / balanced / ...> if recorded.

## Uncached prefill

| Target | Median actual prompt | Median TTFT | Median input tok/s | Range |
|---|---:|---:|---:|---|
| 1K | | | | |
| 4K | | | | |
| 16K | | | | |

Methodology per [BENCHMARK-METHOD.md](../docs/BENCHMARK-METHOD.md). Confirm zero cache hits in server logs after the run.

## Decode throughput

| Concurrency | Median aggregate tok/s | Range | Median per-stream tok/s | Median TTFT |
|---|---:|---|---:|---:|
| ×1 | | | | |
| ×4 | | | | |
| ×8 | | | | |

Fixed prompt shape, `ignore_eos=true`, fixed output length. Tokens counted from the final usage object.

## Correctness gates

- [ ] Coherent text output
- [ ] Tool calls route correctly (if supported)
- [ ] Multimodal input returns expected answer (if supported)
- [ ] Container restart count = 0 after all tests
- [ ] No loops or repetition errors

## Failures and limitations

Document any error, restart, OOM, NCCL failure, thermal throttling, or unexpected behavior observed during the run.

## Hardware observations

Power draw, temperature, memory headroom, or thermal notes if collected. Record the sampling method.
```

## Publishing

1. Save the filled template in the model-family repo's `results/` directory.
2. Add one row to [`results/SUMMARY.md`](SUMMARY.md) linking to it.
3. Update [`docs/EXPERIMENTS.md`](../docs/EXPERIMENTS.md) if this is a new model family, quantization, runtime, or topology.
4. Run the publication gate in [AGENTS.md](../AGENTS.md).
5. Label every material claim as measured, inferred, community-reported, or untested.