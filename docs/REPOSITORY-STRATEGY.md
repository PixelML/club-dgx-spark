# Repository strategy

## Decision

Do not put every experiment in one giant repository, and do not create one repository per run. Use two layers:

1. A hardware club repository for shared platform knowledge, the comparison index, and one runnable canonical notebook per published recipe.
2. A dedicated repository for each model family on that hardware platform.

This keeps the club browsable without fragmenting one model's evidence across dozens of repositories.

The club notebook is a thin executable entry point: it pins and invokes the detailed model repository, preserves clean headline outputs, regenerates its chart from committed summary data, and ends with an editable API request. Raw logs, patches, attempt history, and large receipts remain in the model repository.

## Naming

Preferred model repository:

```text
<Model-Family>-DGX-Spark
```

Examples:

```text
GLM-5.3-Flash-DGX-Spark
Qwen3.8-Flash-Next-DGX-Spark
Step-3.7-Flash-DGX-Spark
```

Do not encode these details in the canonical repository name:

- quantization (`NVFP4`, `AWQ`, `GPTQ`, `EXL3`);
- runtime (`vLLM`, `SGLang`, TensorRT-LLM);
- topology (`1x`, `2x`, dual, cluster);
- checkpoint size or benchmark version.

Those details change and belong in attempt directories, manifests, tags, and result tables.

## Model repository layout

```text
README.md
AGENTS.md
attempts/
  <checkpoint-or-quant>/
    <runtime-and-topology>/
      README.md
      config/
      scripts/
      results/
docs/
  COMPATIBILITY.md
  TROUBLESHOOTING.md
results/
  SUMMARY.md
```

Every attempt remains visible, including failures. The summary table should record model/checkpoint revision, exact checkpoint bytes, quantization, runtime revision, node topology, status, blocker, metrics, thermals/power when available, and evidence links.

## When to create another repository

Create a new repository when:

- the model family changes;
- an image/video/training pipeline is a durable standalone workload rather than a model variant;
- the hardware platform changes enough that recipes and constraints are materially different.

Do not create one when only a quantization, runtime, model size within the same family, topology, or tuning flag changes.

## Existing repositories

Do not rename, delete, or rewrite existing experiment repositories casually; their URLs may already be shared. Add a deprecation or canonical-repository notice, preserve old evidence, and migrate future attempts gradually through normal pull requests.
