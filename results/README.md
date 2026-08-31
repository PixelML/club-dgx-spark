# Result submission format

The detailed result belongs in its model-family repository. This repository stores a runnable canonical notebook plus a compact linked summary.

Every measured recipe folder under `recipes/<model-runtime>/` must contain `recipe.json`, `reproduce.ipynb`, `results/summary.csv`, and a generated chart. The notebook preserves sanitized measured outputs, runs from configuration through benchmark, and ends with an editable `curl` that prints the response and final usage object.

Required summary fields:

```markdown
| Model/checkpoint | Quant | Runtime | Topology | Workload | Result | Power/thermal note | Detailed evidence |
|---|---|---|---|---|---:|---|---|
```

The detailed repository must record:

- exact model, runtime, container/image, and source revisions;
- checkpoint bytes and static/runtime memory plan;
- node count, interconnect, parallelism, and launch command;
- warmup, workload shape, sample count, metric calculation, and raw redacted output;
- power, temperature, memory, utilization, correctness, and failure evidence.

Run the publication gate in [AGENTS.md](../AGENTS.md) before committing either side of the linked result.

Also run `python3 scripts/validate_recipe_notebooks.py` from the repository root.
