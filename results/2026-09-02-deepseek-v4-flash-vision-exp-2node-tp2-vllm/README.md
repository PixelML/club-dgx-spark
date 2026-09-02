# Receipts — DeepSeek-V4-Flash-Vision-Exp, 2x DGX Spark, vLLM TP=2

Sanitized receipts backing
`notebooks/2026-09-02-deepseek-v4-flash-vision-exp-2node-tp2-vllm.ipynb`.
Captured live on 2026-09-02 against a private, Tailscale-only DGX Spark
endpoint. No IP address, hostname, or other private infrastructure
identifier appears in any file here; the endpoint is addressed only
through the `VISION_ENDPOINT` environment variable in the harness
scripts.

## Files

- `live_models.json` — `/v1/models` response.
- `live_deterministic_text.json` — greedy one-word text completion.
- `live_golden_images.json` — the 10 regenerated golden-corpus image
  fixtures sent live, with the model's answer, `finish_reason`, `usage`,
  wall time, and a keyword-match verdict per row.
- `live_negative_control.json` — the `img01_solid_red` question sent with
  no image attached.
- `live_wrong_image_control.json` — the `img01_solid_red` question sent
  with the `img02_solid_blue` image attached.
- `live_c1_x3.json` — concurrency-1, greedy, 400-token decode, 3 reps.
- `live_ttft_x3.json` — warm streaming time-to-first-token, 3 reps.
- `images/` — the regenerated synthetic PNG fixtures from the golden
  correctness corpus's recipe (solid colors, gradients, shape counts, a
  checkerboard, a rendered word) and `image_fixtures.json` (question,
  expected keywords, SHA-256, data URL per fixture).
- `demo/` — the "Try it" demo: the exact prompt's raw response receipt
  (`demo_receipt.json`), the extracted HTML file
  (`ww1-voxel-diorama.html`), the headless Playwright screenshot
  (`preview.png`), and the follow-up vision-description receipt
  (`vision_proof.json`).
- `measure_live.py`, `run_demo.py`, `make_chart.py`, `build_notebook.py`
  — the harness scripts that produced the receipts, the chart, and the
  notebook itself. Re-run `measure_live.py` and `run_demo.py` with
  `VISION_ENDPOINT` and `MODEL_ID` set to reproduce against your own
  endpoint.

## Evidence sources

- `PixelML/DeepSeek-V4-Flash-Vision-Exp-DGX-Spark` (main branch:
  `results/ledger-state.json`, `README.md`) for the canonical merged
  measurements.
- `PixelML/DeepSeek-V4-Flash-Vision-Exp-DGX-Spark#3` for the normalized
  concurrency ladder (open, unmerged as of this notebook).
- The golden correctness corpus and DSpark draft-depth (k) sweep receipts
  that back sections 2.3 and 2.8 of the notebook.

## Notes

- Token counts come from each response's final `usage` object.
- The demo's HTML generation did not complete within its 8,000-token
  budget (see `demo/demo_receipt.json`); this is reported as a negative
  result in the notebook, not smoothed over.
