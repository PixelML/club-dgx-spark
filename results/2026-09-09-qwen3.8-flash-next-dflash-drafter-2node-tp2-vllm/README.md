# Qwen3.8-Flash-Next NVFP4 + DFlash drafter — 2x DGX Spark, vLLM TP2

Receipts for
[`notebooks/2026-09-09-qwen3.8-flash-next-dflash-drafter-2node-tp2-vllm.ipynb`](../../notebooks/2026-09-09-qwen3.8-flash-next-dflash-drafter-2node-tp2-vllm.ipynb).

**Status: the benchmark table is pending.** The serving numbers are being
re-measured on the Spark pair with two boots per arm, a wider block sweep
(DFlash blocks 2/3/4/5/7), both native MTP k=3 and k=4, per-workload paired
bootstrap confidence intervals, and a graph-mode versus eager A/B if graph
capture fits under the memory policy at all. Until that lands, `arms.json`
carries nulls for every result field and a clearly-labelled
`preliminary_2026_09_08` block recording what a single-boot session measured.
The preliminary block is not the result and must not be quoted as one.

| file | what it holds |
|---|---|
| `config_pins.json` | model/drafter revisions, engine, topology, sampling, drafter architecture, training budget |
| `arms.json` | the planned arms and protocol (results pending), plus the superseded preliminary single-boot values |
| `engine_findings.json` | the four vLLM blockers with file:line, the three patches, the six-file adapter overlay, adaptive verification vs GDN, the SGLang rejection |
| `training_and_fidelity.json` | the training curve (labelled proxy), served accepted length, teacher-forced agreement and why it is not a losslessness certification, engine nondeterminism |
| `dspark_comparison.json` | the DSpark arm, scoped to this configuration in vLLM today |
| `run_served_eval.py` | the published form of the per-arm serving harness |
| `analyze_paired_bootstrap.py` | the paired stratified bootstrap used for every difference and CI |

## Labels

Every claim in the notebook and in these receipts is labelled **measured**,
**source-supported**, **inferred**, **community-reported**, or **untested**,
per [AGENTS.md](../../AGENTS.md).

## What is not published here

- The 100-prompt `eval100` fixture itself. Its prompts come from
  Apache-2.0 / MIT sources, but it is a held-out slice of a corpus whose
  responses are Qwen model outputs, governed by the Qwen Community License
  1.0 and the NVIDIA Open Model License. The composition, stratification and
  selection rule are published instead; see the notebook's Reproduce section.
- The two-node launcher wrapper, node addressing, mounts, container names and
  raw logs, per the publication boundary in [AGENTS.md](../../AGENTS.md).
- The drafter weights. The model repo is private at time of writing.
