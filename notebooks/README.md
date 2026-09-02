# Notebooks

Executable companions to the compact summaries in [../results/](../results/). Every
number in a notebook must come from committed receipts — in this repository or a
linked, pinned model-family repository — never from memory or from a live server
at authoring time.

## Convention

Filename: `YYYY-MM-DD-<model>-<quant>-<topology>-<runtime>.ipynb`, where the date
is the first receipt date.

Required sections, in order:

1. **TL;DR** — headline measured numbers with units and the evidence date.
2. **Visible results** — rendered tables and at least one chart when the
   receipts support one; charts are exported to `../assets/charts/` as PNG + SVG.
3. **Reproduce** — sanitized deployment and benchmark steps. No private
   addresses, hostnames, interface names, hardware identifiers, or credentials;
   use placeholders.
4. **Appendix** — full configuration pins, methodology and caveats, functional
   gate status, explicit receipt gaps, and provenance links.

## LIVE flag

The first code cell must define `LIVE = False`. With `LIVE = False` the notebook
renders exclusively from receipts and makes no network calls; any live-query code
must be guarded by `if LIVE:`. Committed notebooks are executed with
`LIVE = False`:

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/<name>.ipynb
```

Re-execute after every edit so committed outputs match committed receipts, and
run the publication gate in [../AGENTS.md](../AGENTS.md) before committing.
