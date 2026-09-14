# Qwen3.8-Flash-Next NVFP4 + DFlash drafter — 2x DGX Spark, vLLM TP2

Receipts for
[`notebooks/2026-09-09-qwen3.8-flash-next-dflash-drafter-2node-tp2-vllm.ipynb`](../../notebooks/2026-09-09-qwen3.8-flash-next-dflash-drafter-2node-tp2-vllm.ipynb).

**Status: final, measured 2026-09-09.** The definitive sweep ran on the Spark
pair with **two boots per arm** and two runs of 100 prompts per boot: AR;
native MTP k=1/3/4/6; native MTP k=4 in graph mode; DFlash blocks 2/3/4/5/7;
per-workload aggregate throughput with paired stratified bootstrap intervals;
a losslessness certification with common-prefix controls; and a measured
engine nondeterminism floor.

**Headline: DFlash block 5 is +3.87 % [+2.10 %, +5.77 %] in aggregate output
throughput over the tuned native MTP baseline (k=4)**, and +4.50 %
[+2.35 %, +6.80 %] against the softer k=3 baseline this repository previously
quoted at +4.59 %. The baseline was swept before the comparison was made; k=3
and k=4 are statistically a tie at about 50.2.

Three things a reader should carry away with the number:

- **Boot-to-boot variance is not in any interval.** Two boots cannot estimate
  it, and observed boot-to-boot movement (+3.4 % / −2.0 % / +1.0 % on three
  arms) is the same order as the +3.87 % being claimed. This is the weakest
  part of the result.
- **Chat regresses at every servable block**, every interval excluding zero,
  including the short blocks that were untested before. Code is a wash at
  block 5. It is a math drafter.
- **The graph A/B is one-sided.** Graph memory fits (first demonstration) and
  graphs make the baseline 3.97 % slower, but the DFlash side is blocked by
  our own adapter assertion at `serving/plugin/dflash_epoch7.py:80`, not by
  vLLM and not by memory.

The 2026-09-08 single-boot set is preserved in `arms.json` as
`preliminary_2026_09_08`, labelled **superseded**. It is kept for the audit
trail and must not be quoted as a result.

| file | what it holds |
|---|---|
| `config_pins.json` | model/drafter revisions, engine, topology, sampling, drafter architecture, training budget |
| `arms.json` | every arm and its protocol, headline, per-workload split, per-boot aggregates, boot-variance disclosure, thin/patched arm labels, graph-mode result, and the superseded preliminary single-boot values |
| `engine_findings.json` | the four vLLM blockers with file:line, the three patches, the six-file adapter overlay, adaptive verification vs GDN, the SGLang rejection |
| `training_and_fidelity.json` | the training curve (labelled proxy), served accepted length per arm, the losslessness certification with its method, controls, per-offset breakdown and scope, and the measured engine nondeterminism floor |
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
- The drafter weights themselves; the model repo is linked instead.
