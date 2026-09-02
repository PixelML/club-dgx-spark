# Notebooks

This directory holds one executed Jupyter notebook per experiment. Each
notebook runs top to bottom and every cell output is committed. The
collection grows over time; older notebooks are not rewritten, only
superseded by a newer file that links back to them.

## File naming

```
YYYY-MM-DD-<model>-<topology>-<runtime>.ipynb
```

- `YYYY-MM-DD` is the measurement date, not the commit date.
- `<model>` is a short, lowercase, hyphenated model name.
- `<topology>` names node count and parallelism, for example `2node-tp2`.
- `<runtime>` names the serving engine, for example `vllm`.

Example: `2026-09-02-deepseek-v4-flash-vision-exp-2node-tp2-vllm.ipynb`.

## Required sections

Every notebook reads top to bottom in four sections, in this order. A
reader who stops after section 1 gets the verdict; a reader who stops
after section 3 can reproduce the run; nobody has to read the appendix
unless they want the failure history.

1. **TL;DR.** Nothing above this but the notebook title and the `LIVE`
   status cell. One key-metrics table (pass/fail, headline throughput
   numbers, cold boot time, memory per node, power) and one pins table
   (model revision, runtime commit, image tag, driver, topology,
   quantization, KV dtype, speculative-decode depth). Keep this section
   short enough to screenshot.
2. **Visible results.** Every chart, every results table, and — for a
   vision notebook — the fixture images shown inline next to the model's
   answer. This is where a reader checks the claim in section 1 against
   the evidence.
3. **Reproduce.** Hardware requirements (node count, memory per node,
   interconnect, power), the launch commands, the snapshot download with
   the pinned revision, the expected boot time, and how to point the
   notebook at a different endpoint. A reader with the right hardware can
   run this section and get comparable numbers.
4. **Appendix.** Collapsed under a `<details>` heading so it stays out of
   the main scroll. Every failed attempt with its exact error class and
   its fix or its dead end, how the approach evolved, safety notes, cost
   and limitations, and links to the evidence source. Long narrative
   belongs here, not in sections 1 to 3.

## The hero cell

The very first cell in the notebook is a markdown hero, and it holds
nothing else:

- A one-line title naming the model and the topology (for example
  "DeepSeek-V4-Flash-Vision-Exp on 2x DGX Spark").
- A four-row metrics table with units: decode at concurrency 1, best
  aggregate throughput, prefill, and TTFT. Mark each row's source
  (live, this notebook or canonical, merged main) if the numbers come
  from different runs.
- For a vision notebook, the demo preview image (a relative path into
  `results/<experiment>/demo/`) with the model's own three-sentence
  description underneath it as the vision proof.
- The launch command or the pinned-revision pull command, as one code
  line.
- One line of links: the evidence repository and the model's page or
  collection.

Everything else — pins, protocol, full tables, reproduce steps, and the
appendix — stays below the hero cell, starting with section 1.

## The LIVE flag

Each notebook has a status cell near the top with a `LIVE` flag.

- `LIVE = False` (default) replays the committed receipts under
  `results/<experiment>/`. This is what gets executed and committed. It
  needs no GPU and no network access.
- `LIVE = True` runs the same harness code against a running
  OpenAI-compatible endpoint. The endpoint URL comes from an environment
  variable (`VISION_ENDPOINT`), never a literal address in the notebook.
  Use this mode only for local reproduction against your own endpoint; do
  not commit a notebook that was executed with `LIVE = True`, because the
  receipts it reads may not be sanitized.

## Publication rules

These follow `AGENTS.md` and apply to every notebook and every file under
`results/<experiment>/`:

- Commit every cell output. A notebook with cleared outputs is not
  published.
- No private IPs, hostnames, container names, PIDs, or storage paths. Use
  the same masking convention as the evidence bundle (`<dgx-head>`,
  `<node-a>`, and so on).
- Label every claim as measured, inferred, community-reported, or
  untested.
- State units and denominators on every axis and every table column.
- Preserve negative and failed results; do not delete a failed
  configuration or rejected setting from a table.

## Adding a notebook

1. Copy an existing notebook as a starting point, or build one following
   the section order above.
2. Copy the sanitized receipts for the experiment into
   `results/<experiment>/` (README/receipts JSON, harness script, chart
   sources, demo output).
3. Fill in each section using the receipts. Do not invent a number that is
   not in a receipt.
4. Set `LIVE = False` and execute top to bottom:
   `jupyter nbconvert --to notebook --execute --inplace notebooks/<file>.ipynb`.
5. Export any chart to `assets/charts/` as PNG and SVG.
6. Add a row to the Notebooks table in the top-level `README.md`.
7. Run the pre-publication gate in `AGENTS.md` before committing.
