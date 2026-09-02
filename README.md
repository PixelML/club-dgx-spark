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

Cross-platform views:

- [Coverage matrix](docs/COVERAGE-MATRIX.md) - every accessible DGX Spark model repository by quant, runtime, topology, validation depth, and missing evidence.
- [Source registry](docs/sources/README.md) - curated external DGX Spark ecosystem (NVIDIA, MiaAI-Lab, jvr0x, jasonacox, dataforgex) at exact revisions with three-level evidence labels.
- [Cross-cutting synthesis](docs/SYNTHESIS.md) - what all sources jointly teach about topology, runtimes, quant, KV memory, spec decode, eval, and ops on GB10.
- [Migration proposal](docs/MIGRATION-PROPOSAL.md) - when legacy repository names should move to the canonical Model-DGX-Spark form (not yet).
- [Cookbook (research preview)](docs/cookbook/glm-5.3-flash-dgx-spark.md) - GLM-5.3-Flash profile selector with measured speed and untested quality/cost clearly labeled.
- [Cross-platform cost/watt](docs/EXPERIMENTS.md#cross-platform-cost-and-efficiency-cmp-170hx-vs-dgx-spark) - DGX Spark against a 4-card CMP 170HX rig on the same checkpoint, with tokens/Wh and $/M-token figures.

## Hugging Face

Curated, verified artifacts from this club: [PixelML/club-dgx-spark: verified on DGX Spark (GB10)](https://huggingface.co/collections/PixelML/club-dgx-spark-verified-on-dgx-spark-gb10-6a97c6b97ebd12f082dac6ca).

## Notebooks

Executable, receipt-backed walkthroughs of experiments summarized here. Committed notebooks ship with `LIVE = False` — every number renders from committed receipts and no cell makes a network call. Flip `LIVE` only against your own authenticated deployment. Convention: [notebooks/README.md](notebooks/README.md).

| Notebook | Model | Quant | Runtime | Topology | Evidence | LIVE default |
|---|---|---|---|---|---|---|
| [Qwen3.8-Flash-Next NVFP4 on 2× DGX Spark (SGLang)](notebooks/2026-08-26-qwen3-8-flash-next-nvfp4-2node-sglang.ipynb) | Qwen3.8-Flash-Next @ `b80180e3…` | NVFP4 | SGLang TP=2 + NEXTN/MTP | 2× Spark | [2026-08-26/27 receipts](results/2026-08-26-qwen3-8-flash-next-nvfp4-sglang-2node/) | `False` |

## What belongs here

| Put in `club-dgx-spark` | Put in a model-family repository |
|---|---|
| platform setup and shared tooling | complete launch/build recipes |
| concise verified result summaries | raw redacted benchmark artifacts |
| cross-model comparison tables | all quantization/runtime attempts |
| common failure and recovery lessons | model-specific patches and scripts |
| links and status tracking | detailed positive and negative results |

## Notebooks

Each row links one executed Jupyter notebook, top to bottom, with committed
outputs. The schema and the `LIVE`-replay convention are in
[notebooks/README.md](notebooks/README.md).

| Date | Experiment | Headline | Notebook |
|---|---|---|---|
| 2026-08-26 | Qwen3.8-Flash-Next NVFP4, 2x DGX Spark, SGLang TP=2 | Backfilled from evidence-repo receipts: 47.54 tok/s @ c=1 up to 275.37 tok/s @ c=16 aggregate decode (NEXTN/MTP, 3 steps); uncached prefill 2,960.12 tok/s at 16K prompt; text, tool-call, and vision functional checks pass | [notebooks/2026-08-26-qwen3-8-flash-next-nvfp4-2node-sglang.ipynb](notebooks/2026-08-26-qwen3-8-flash-next-nvfp4-2node-sglang.ipynb) |
| 2026-09-02 | DeepSeek-V4-Flash-Vision-Exp, 2x DGX Spark, vLLM TP=2 | 10/10 golden vision fixtures pass keyword match; C1 31.9 tok/s and TTFT 0.323 s live re-measured today | [notebooks/2026-09-02-deepseek-v4-flash-vision-exp-2node-tp2-vllm.ipynb](notebooks/2026-09-02-deepseek-v4-flash-vision-exp-2node-tp2-vllm.ipynb) |

Detailed evidence for the Qwen3.8-Flash-Next checkpoint on this hardware
lives in
[qwen3-8-flash-next-sglang-2x-dgx-spark](https://github.com/PixelML/qwen3-8-flash-next-sglang-2x-dgx-spark)
@ `682504bec9e7e99206212f4e172b7ec823e4605c`; this notebook is a backfill
replay of those receipts and adds no new measurements. Sanitized receipts:
[results/2026-08-26-qwen3-8-flash-next-nvfp4-sglang-2node/](results/2026-08-26-qwen3-8-flash-next-nvfp4-sglang-2node/).

Detailed evidence for the DeepSeek-V4-Flash-Vision-Exp checkpoint on this
hardware lives in
[DeepSeek-V4-Flash-Vision-Exp-DGX-Spark](https://github.com/PixelML/DeepSeek-V4-Flash-Vision-Exp-DGX-Spark);
this notebook links back to it and adds a fresh live re-measurement plus a
reproducible end-to-end vision demo.

## Publication safety

This is a public repository. Read [AGENTS.md](AGENTS.md) before adding live-system evidence. Do not publish credentials, private network details, hostnames, hardware identifiers, customer data, or unredacted logs.

## Contributing

Use the result format in [results/README.md](results/README.md), then open a branch-based pull request. Detailed results must live in the appropriate model-family repository and link back here.
