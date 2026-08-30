# GLM-5.3-Flash NVFP4 now runs on two DGX Sparks with measured receipts

GLM-5.3-Flash NVFP4 serves from two DGX Spark nodes with vLLM TP=2, with independently measured decode, uncached prefill, tool-call, and multimodal gates. This page is a **research preview** selector for practitioners who already own two Sparks; it is not claim-ready for a quality or cost recommendation.

> **Validation:** measured (speed + functional gates) · quality/cost: untested · **Updated:** 2026-08-30 · **Evidence:** [GLM DGX-Spark repository](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark)

## Choose a profile

| Goal | Hardware | Artifact | Runtime | Topology | Validation | Notes |
|---|---|---|---|---|---|---|
| Balanced serving | 2× Spark | GLM-5.3-Flash-NVFP4 @ 11d7321 | vLLM + Ray TP=2 | 2 nodes | Measured | 27–68 agg tok/s ×1–×8; 7 streams is the no-queue sweet spot |
| Max context | 2× Spark | EXL3/TR3 4-bpw + FP8 KV | vLLM + Ray TP=2 | 2 nodes | Measured | 900K context; 66.3 single / 154.9 agg ×4; eval-only draft license |
| Faster drafting | 2× Spark | NVFP4 + DFlash2 K=7 | vLLM + Ray TP=2 | 2 nodes | Measured | 25–61 tok/s; acceptance is prompt-shape dependent (31–91%) |
| Single Spark | 1× Spark | any | any | 1 node | **Untested** | 181 GiB checkpoint; hypothesis: does not fit — see gap analysis |
| Quality/cost pick | any | any | any | any | **Untested** | No scored quality or cost-per-task evidence yet |

## Run it

From the GLM evidence repository on the rank-zero (controller) node:

```bash
git clone https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark.git
cd GLM-5.3-Flash-NVFP4-Dual-DGX-Spark
# Provide the serving key via a masked prompt (or your platform secret store); nothing is written to the repo
read -rs VLLM_API_KEY   # paste your API key, then press Enter
export VLLM_API_KEY
./start.sh
```

First run downloads ~181 GiB, refreshes the chat template, stages the worker node, and polls `/health` for up to 3600s. Weights already local: `SKIP_DOWNLOAD=1 ./start.sh`.

Expected ready signal: `./start.sh status` shows both ranks healthy and the API answering at the documented port.

Minimal verification (functional gates + concurrency matrix):

```bash
./benchmark.py --concurrency 1,2,4,8
./prefill-benchmark.py
```

## Results

| Profile | Concurrency | Aggregate tok/s | Uncached prefill tok/s | Quality | Cost |
|---|---|---:|---:|---|---|
| NVFP4 main | ×1–×8 | 27–68 | 1,277–1,372 | gate-pass only | untested |
| EXL3 4-bpw | ×1 / ×4 | 66.3 / 154.9 | 702–795 | gate-pass + 300K stress | untested |
| DFlash2 K=7 | ×1 | 25–61 | 1,310–1,400 | gate-pass only | untested |

Full tables, ranges, TTFT, cold start, and failure notes: [results/](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark/tree/main/results). Cross-model comparison: [club summary](../../results/SUMMARY.md).

## What failed

- SGLang was rejected on GB10: FlashInfer DSA rejected SM121 and TileLang DSA exceeded GB10 dynamic shared memory; the recipe routes SM121 through the SM90 path instead.
- ×8 concurrency queues on the eighth stream (TTFT rise, aggregate drop) on the validated 8.5 GiB KV layout.
- Multimodal first-compile needs UMA headroom the throughput profile lacks; vision is opt-in with a lowered GPU/KV budget.

## Reproduce the evaluation

- Checkpoint revision: `11d73216cd636238e82e1d77fe1042ffab36e7fa` (120 shards, 181.29 GiB)
- Recipe commits: `aed98a1` (validated), `3407023` (current tip)
- Methodology: [club benchmark method](../BENCHMARK-METHOD.md) + per-receipt details
- Token counting: final usage object only

## Limits

- Two-node cluster, one specific checkpoint revision, three-run medians; your interconnect and host config will move the numbers.
- No scored accuracy, no energy/power, no cost-per-task, no single-node test. Speed-only comparisons across models are directional.
- DFlash2 draft is CC BY-NC-ND 4.0; EXL3 checkpoint is ShapleyMCG 1.0 — both profiles are evaluation-only.

## Artifacts and evidence

- Detailed repository: [GLM-5.3-Flash-NVFP4-Dual-DGX-Spark](https://github.com/PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark)
- Coverage matrix: [COVERAGE-MATRIX.md](../COVERAGE-MATRIX.md)
- Gap analysis: [GAP-ANALYSIS.md](../GAP-ANALYSIS.md)
- Draft release manifest: [releases/draft-glm-5.3-flash-dgx-spark.json](../../releases/draft-glm-5.3-flash-dgx-spark.json)
- Hugging Face artifact: none (third-party checkpoint, curated not duplicated)
