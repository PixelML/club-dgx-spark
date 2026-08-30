# Migration proposal — repository naming and supersession

Status: **proposal only**. No rename, deletion, redirect, or supersession happens without explicit owner approval. Existing repositories and history are preserved.

## Current state vs canonical topology

The PixelML canonical topology for model-family evidence is `PixelML/<Model-Family>-<Platform>` with platform spelled `DGX-Spark`.

| Current repository | Canonical expectation | Verdict |
|---|---|---|
| GLM-5.3-Flash-NVFP4-Dual-DGX-Spark | GLM-5.3-Flash-DGX-Spark | Name embeds quant + topology; **no migration recommended now** |
| qwen3-8-flash-next-sglang-2x-dgx-spark | Qwen3.8-Flash-Next-DGX-Spark | Lowercase, embeds runtime + node count; **no migration now** |
| Step-3.7-Flash-NVFP4-Dual-DGX-Spark | Step-3.7-Flash-DGX-Spark | Same pattern; **no migration now** |
| Hy3-NVFP4-Dual-DGX-Spark | Hy3-DGX-Spark | Same pattern; **no migration now** |
| Inkling-Small-NVFP4-Dual-DGX-Spark | Inkling-Small-DGX-Spark | Same pattern; **no migration now** |

## Why not migrate immediately

1. All five repositories are public with inbound links, receipts, and (in GLM/Qwen) merged PR histories. Renames invalidate nothing at GitHub but churn every deep link and open PR across the org.
2. The naming variance is cosmetic; the content placement already follows the one-repo-per-model-family-plus-platform rule. No repository per quant/runtime/topology was created.
3. Renames during active benchmark work (EXL3 profile, Qwen SM121 patch series) risk breaking collaborators' checkouts and pinned links in receipts.

## When migration becomes worth it

Trigger: a repository needs its **second** quantization family or a single-node profile that would force the embedded "NVFP4-Dual" out of the name anyway.

Proposed sequence when triggered (owner-approved, each step verified):

1. Create the canonical-named repository as the continuing home (or use GitHub rename, which auto-redirects).
2. Port README, recipes, results, and releases byte-identical; verify redirects on the old URL.
3. Update every cross-link in club-dgx-spark, receipts, and the cookbook pages to the new URLs.
4. Mark the old path superseded **only after** the replacement contains all evidence and redirects resolve.
5. Never rewrite or delete history.

## SparkQuant-Lab

SparkQuant-Lab (local commit `dca8259`, not yet a public PixelML repository) is the quality-layer plan for GLM-5.3-Flash vs Qwen3.8-Flash-Next quantization fidelity. When published, its evidence splits by the same topology:

- GLM fidelity evidence → the GLM DGX-Spark evidence repository.
- Qwen fidelity evidence → the Qwen DGX-Spark evidence repository.
- Reusable harness/methodology → SparkQuant-Lab as a `PixelML/<Domain>-Eval`-style evaluation repository, named at publication time.

Nothing is renamed or superseded for it today.
