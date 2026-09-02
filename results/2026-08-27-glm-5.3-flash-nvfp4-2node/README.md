# Receipts — GLM-5.3-Flash NVFP4, 2x DGX Spark, vLLM TP=2

Sanitized receipts backing
`notebooks/2026-08-27-glm-5.3-flash-nvfp4-2node-tp2-vllm.ipynb`. This is a
**backfill**: the measurements were taken on 2026-08-27/28 on a private
two-node DGX Spark kit and published in the evidence repository first; this
bundle re-publishes the sanitized numbers with a replayable notebook. No
measurement in this bundle was taken for this notebook.

## Evidence sources (pinned)

- `PixelML/GLM-5.3-Flash-NVFP4-Dual-DGX-Spark` @
  `3407023e0b8109a1dd12e8a5544e106ca6912afe` (MIT) — validation,
  revalidation, and DFlash2 receipts; retrieved 2026-09-02.
- `PixelML/GLM-5.3-Flash-DGX-Spark-Eval` @
  `b81f7eca052d0f81a831527bbf7a6b3ce8b49d0b` (MIT) — quality-eval status and
  arm64 build smoke only (no performance numbers; the repo states its draft
  eval numbers are not real yet).
- Upstream DFlash2 port credited to
  `tonyd2wild/GLM-5.3-Flash-NVFP4-DFlash2-2x-DGX-Spark`; draft model by
  IncoAI (CC BY-NC-ND 4.0, evaluation-only).

## Files

- `config-pins.json` — tested configuration and revision pins, plus the
  quality-eval status (`untested`).
- `decode-matrix-mtp.json` — both measured decode concurrency passes
  (validation and fresh revalidation), protocol, ranges, TTFT.
- `prefill-uncached.json` — uncached 1K/4K/16K prefill with cache counters.
- `gates-coldstart-failures.json` — cold start, functional gates, MTP
  acceptance behavior, coding-agent regression, the nondeterministic vision
  UMA failure, and the SGLang rejection (negative result).
- `dflash2-profile.json` — the DFlash2 K=7 speculative-decode profile on the
  same NVFP4 target checkpoint (separate, evaluation-only draft).
- `make_chart.py` — regenerates the throughput chart into `assets/charts/`
  from `decode-matrix-mtp.json`.
- `build_notebook.py` — builds the notebook from these receipts.
- `upstream/` — sanitized copies of the three source receipts (see the
  redaction log below).

## Redactions applied to the upstream copies

All measured values are unchanged. The following private-infrastructure
identifiers in the upstream files were replaced with generic terms:

1. The private two-node cluster name (upstream receipt titles and text) →
   "two-Spark" / "the deployment"; local proxy alias names → "the local
   CLIProxy/OpenCodex alias".
2. Node-to-node private IP addresses (RFC1918, one /24 pair) → "the direct
   CX7 RoCE link".
3. NIC interface names (the head/worker port pairs) → "the QSFP port pair".
4. Overlay-network route details (an overlay-VPN route and a public tunnel
   wording) → "every tested route returned HTTP 401 without a key".
5. Absolute cold-start clock timestamps → durations only (already published
   as durations upstream).

## Receipt gaps (honest holes)

- **Power, temperature, and fan telemetry**: not captured in any source
  receipt. Every power/thermal column is a gap, not a zero.
- **Driver / OS / container digest for the serving lane**: not recorded in
  the 2026-08-27 receipts (the image digest is recorded for the 2026-08-28
  DFlash2 profile only). The eval repo records driver 580.173.02 / CUDA 13.0
  on a DGX Spark node for the separate eval lane; it is not evidence for the
  serving cluster.
- **Raw per-request dumps for the 2026-08-27 passes**: the evidence repo
  publishes medians and ranges, not raw JSON, for these two passes; the raw
  JSON dumps it does publish belong to the EXL3 profile (different
  quantization) and are deliberately not copied here.
- **Quality/accuracy**: no scored eval exists anywhere for this checkpoint on
  DGX Spark; qbench fidelity run not yet executed.
- **Single-node (1x Spark) operation**: untested; 181.29 GiB of weights does
  not fit one 128 GiB UMA node (inferred, not measured).
- **Vision/multimodal**: conditionally working at best; a first-compile image
  request crossed Ray's node-memory threshold by 6,606,848 bytes and killed
  the engine on one start, while an earlier start passed the same gate.

## Notes

- Token counts come from final `usage` objects / client-observed completed
  tokens, per the club method.
- All claims in the notebook are labeled measured, inferred,
  community-reported, or untested; negative results are preserved.
