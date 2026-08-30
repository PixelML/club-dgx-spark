# Quantization fidelity evaluation: methodology and open gap

This page records the club's **planned** quality-layer methodology so the gap is
visible before any GPU time is scheduled. Nothing here has been run yet; no
benchmark numbers are claimed.

## Why this gap exists

Every PixelML DGX Spark recipe currently has gate-level checks only (coherence,
stop, tool-call routing, image/video gates). No scored quality layer exists for
any recipe: no KL-divergence fidelity measurement, no capability scoring, no
agentic-suite results, and no cost-per-successful-task calculation.

## Planned methodology (not yet run)

1. **Fidelity layer**: KL-divergence between a quantized checkpoint and its BF16
   reference on identical prompts. Harness source selection is **unresolved**;
   the chosen upstream harness must be pinned by full commit at run time. The
   plan self-samples test prompts from the candidate endpoint, splits them with
   the reference tokenizer, and measures both per-window and aggregate
   divergence.
2. **Capability layer**: deterministic tool-calling scenarios with pass/partial/
   fail scoring and a safety-capped rating, following the upstream
   tool-eval-bench pattern (69 deterministic scenarios plus 15 opt-in Hard Mode
   scenarios at the pinned revision).
3. **Agentic layer**: reliability framing with both Pass@k and Pass^k over
   repeated trials, plus thinking-on/off as a fixed reported axis.
4. **Energy/cost layer**: power sampling during each run so cost-per-successful-
   task can be computed once scored eval exists.

## Evidence labels

- Weights-level KLD panels published upstream (e.g., the EXL3 4-bpw discussion)
  stay **community-reported**; they measure weights, not a serving stack.
- Any future PixelML fidelity runs will be **measured** with the full recipe,
   pins, and raw receipts published in the canonical model repository.
- Until then, every quality/cost selector row stays **untested**.

## Preconditions before any run

1. Cluster availability and workload-conflict checks pass; no other workload is
   interrupted.
2. Model storage paths and free space are verified on both nodes.
3. The pinned harness revision and both checkpoint revisions are recorded.
4. The offline integrity suite of the evaluation plan passes without network.

## Next experiment

GLM-5.3-Flash NVFP4 vs streamed BF16 reference fidelity smoke on the two-node
DGX Spark pair - the smallest run that upgrades the biggest quality gap from
untested to measured. Do not schedule until the preconditions above pass.
