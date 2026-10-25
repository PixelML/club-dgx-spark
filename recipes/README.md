# Reproducible benchmark notebooks

This directory is the runnable public entry point for measured DGX Spark recipes. Each recipe is a self-contained folder that a reader can configure once and run from top to bottom from a Jupyter controller.

## Published recipes

| Model | Runtime | Hardware | Notebook | Headline result |
|---|---|---|---|---:|
| Qwen3.8-Flash-Next NVFP4 | SGLang + NEXTN/MTP | 2 × DGX Spark, TP=2 | [Open notebook](qwen3.8-flash-next-sglang/reproduce.ipynb) | 275.37 aggregate decode tok/s at concurrency 16 |

## Folder contract

```text
recipes/<model-runtime>/
├── README.md             short verdict and notebook link
├── recipe.json           immutable pins and artifact index
├── reproduce.ipynb       configure → preflight → install → serve → benchmark → curl
├── assets/performance.png
└── results/summary.csv   clean measured data used by the notebook and chart
```

The notebook must preserve clean measured outputs, regenerate its chart from committed data, avoid machine-specific defaults, and finish with an editable `curl` request that prints both the response and the API's final usage object.

Validate before publication:

```bash
python3 scripts/validate_recipe_notebooks.py
python3 scripts/render_recipe_chart.py \
  --spec recipes/qwen3.8-flash-next-sglang/chart-spec.json \
  --data recipes/qwen3.8-flash-next-sglang/results/summary.csv \
  --output recipes/qwen3.8-flash-next-sglang/assets/performance.png
```

Detailed patches, lifecycle scripts, and raw redacted evidence remain in the pinned model repository. The club notebook is the readable, runnable entry point.
