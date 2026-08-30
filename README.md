# Club DGX Spark

Community-tested recipes, diagnostics, and reproducible benchmarks for NVIDIA DGX Spark workloads.

This repository is the platform-wide index for our DGX Spark experiments. It consolidates:

- system setup, networking, storage, cooling, and operations;
- common validation and benchmark methodology;
- cross-model comparisons and lessons;
- links to detailed model-family experiment repositories;
- LLM, image, video, training, and distributed workload coverage.

## Repository structure

Use a hybrid organization:

```text
club-dgx-spark                         platform guide + result index
├── GLM-5.3-Flash-DGX-Spark           all GLM quants/runtimes/topologies
├── Qwen3.8-Flash-Next-DGX-Spark      all Qwen attempts
├── Step-3.7-Flash-DGX-Spark           all Step attempts
└── <Model-or-workload>-DGX-Spark      one durable experiment repository
```

The rule is **one repository per model family and hardware platform**—not one repository per quantization, runtime, checkpoint size, machine count, or individual run.

For example, one GLM repository should contain NVFP4, AWQ, GPTQ, EXL3, FP8/BF16, conversion experiments, vLLM/SGLang/other runtimes, single/dual/multi-Spark topologies, successful benchmarks, and documented failures.

See [Repository strategy](docs/REPOSITORY-STRATEGY.md) for naming and migration rules.

## Existing public experiments

These repositories predate the consolidated naming policy. Keep their links stable while gradually moving future work into broader model-family repositories.

| Model family | Existing experiment repository | Current scope |
|---|---|---|
| GLM-5.3-Flash | [GLM-5.3-Flash-NVFP4-Dual-DGX-Spark](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark) | NVFP4, dual Spark |
| Qwen3.8-Flash-Next | [qwen3-8-flash-next-sglang-2x-dgx-spark](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark) | SGLang, dual Spark |
| Step-3.7-Flash | [Step-3.7-Flash-NVFP4-Dual-DGX-Spark](https://github.com/PixelML/Step-3.7-Flash-NVFP4-Dual-DGX-Spark) | NVFP4, dual Spark |
| Hunyuan 3 | [Hy3-NVFP4-Dual-DGX-Spark](https://github.com/PixelML/Hy3-NVFP4-Dual-DGX-Spark) | NVFP4, dual Spark |
| Inkling Small | [Inkling-Small-NVFP4-Dual-DGX-Spark](https://github.com/PixelML/Inkling-Small-NVFP4-Dual-DGX-Spark) | NVFP4, dual Spark |

The experiment catalog is in [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md). A repository appearing here means it is relevant; it does not independently certify every performance claim inside it.

## What belongs here

| Put in `club-dgx-spark` | Put in a model-family repository |
|---|---|
| platform setup and shared tooling | complete launch/build recipes |
| concise verified result summaries | raw redacted benchmark artifacts |
| cross-model comparison tables | all quantization/runtime attempts |
| common failure and recovery lessons | model-specific patches and scripts |
| links and status tracking | detailed positive and negative results |

## Publication safety

This is a public repository. Read [AGENTS.md](AGENTS.md) before adding live-system evidence. Do not publish credentials, private network details, hostnames, hardware identifiers, customer data, or unredacted logs.

## Contributing

Use the result format in [results/README.md](results/README.md), then open a branch-based pull request. Detailed results must live in the appropriate model-family repository and link back here.
