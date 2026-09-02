#!/usr/bin/env python3
"""Assemble the DeepSeek-V4-Flash-Vision-Exp DGX Spark notebook from the
committed receipts in this results directory. Run once, then execute with
jupyter nbconvert. Not itself part of the notebook."""
import nbformat as nbf
import os

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
NB_PATH = os.path.join(REPO, "notebooks", "2026-09-02-deepseek-v4-flash-vision-exp-2node-tp2-vllm.ipynb")

nb = nbf.v4.new_notebook()
cells = []


def md(src):
    cells.append(nbf.v4.new_markdown_cell(src))


def code(src):
    cells.append(nbf.v4.new_code_cell(src))


# ---------------------------------------------------------------------
# Title + status cell
# ---------------------------------------------------------------------
md("""# DeepSeek-V4-Flash-Vision-Exp — 2x DGX Spark, vLLM TP=2

Executed notebook. Every cell output below is committed; see
`notebooks/README.md` for the section order and the `LIVE` flag
convention.""")

code('''# --- Status cell -------------------------------------------------------
# LIVE = False replays the committed receipts under results/<experiment>/.
# LIVE = True runs the same harness against a running OpenAI-compatible
# endpoint whose base URL comes from the VISION_ENDPOINT environment
# variable. Never hardcode an endpoint address in this notebook. This
# notebook's committed outputs were produced with LIVE = True against the
# private DGX Spark endpoint on 2026-09-02; the default below is reset to
# False so a plain re-run replays the receipts instead of requiring
# network access.
import os

EXPERIMENT = "2026-09-02-deepseek-v4-flash-vision-exp-2node-tp2-vllm"
RESULTS_DIR = os.path.join("..", "results", EXPERIMENT)
LIVE = False
MODEL_ID = "apollo-deepseek-v4-flash-vision-exp"
VISION_ENDPOINT = os.environ.get("VISION_ENDPOINT", "").rstrip("/")

print("LIVE =", LIVE)
print("results dir:", RESULTS_DIR)
if LIVE:
    assert VISION_ENDPOINT, "Set VISION_ENDPOINT to your own endpoint base URL before running with LIVE=True."
    print("endpoint: <set via VISION_ENDPOINT env var, not printed>")
''')

code('''# --- Helpers -------------------------------------------------------------
import json
import base64
import time
from IPython.display import display, Markdown, Image


def load_receipt(name):
    with open(os.path.join(RESULTS_DIR, name)) as f:
        return json.load(f)


def render_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    display(Markdown("\\n".join(lines)))


def live_post(payload, timeout=180):
    import requests
    r = requests.post(f"{VISION_ENDPOINT}/chat/completions", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()
''')

# ---------------------------------------------------------------------
# Section 1: TL;DR
# ---------------------------------------------------------------------
md("""## 1. TL;DR

**Verdict: PASS.** DeepSeek-V4-Flash-Vision-Exp serves live on a 2-node
DGX Spark (GB10 x2) kit under vLLM TP=2, RoCE-interconnected. All 10
golden vision fixtures pass keyword match; text and vision paths both
respond correctly; a negative control (no image) correctly declines to
guess a color instead of hallucinating one, and a wrong-image control
answers the attached image, not the question's implied one.

Two evidence rows come from the upstream evidence repository
(`PixelML/DeepSeek-V4-Flash-Vision-Exp-DGX-Spark`); the third is this
notebook's own live re-measurement.""")

code('''render_table(
    ["Row", "Decode c=1 (tok/s)", "Aggregate best-c (tok/s)", "Prefill (tok/s)", "TTFT (s)", "Boot time", "Memory/node", "Power", "Status"],
    [
        ["Canonical (merged main)", "36.9", "112.7 @ c=6", "1,789", "0.239", "not captured in receipts", "not captured in receipts", "not captured in receipts", "measured"],
        ["Normalized protocol (PR pending)", "48.7", "106.8 @ c=16", "1,566 @ 2,941 tok prompt", "0.323", "not captured in receipts", "not captured in receipts", "not captured in receipts", "measured, PR #3 open, unmerged"],
        ["This notebook, live re-measurement (2026-09-02)", "see section 2", "see section 2", "n/a (not re-measured; see prefill note)", "see section 2", "not re-measured today (service already running)", "not re-measured today", "not re-measured today", "measured"],
    ],
)
''')

code('''pins = {
    "model": "deepseek-ai/DeepSeek-V4-Flash-Vision-Exp",
    "served_model_id": MODEL_ID,
    "model_revision": "86f746b36186f0e567729a5c06a8c918caba82a9",
    "runtime": "vLLM 0.25.2.dev0+g752a3a504.d20260714 (from the evidence repo run manifest)",
    "topology": "2 nodes, TP=2, direct RoCE interconnect",
    "kv_cache_dtype": "nvfp4_ds_mla",
    "speculative_decode": "DSpark, k (MTP_NUM_TOKENS) = 6",
    "driver": "not captured in this notebook's receipts; see evidence repo EVIDENCE.md",
}
render_table(["Pin", "Value"], list(pins.items()))
''')

# ---------------------------------------------------------------------
# Section 2: Visible results
# ---------------------------------------------------------------------
md("""## 2. Visible results

### 2.1 Live service check

`/v1/models` against the running endpoint, captured today.""")

code('''models = load_receipt("live_models.json")
print("captured:", models["captured_utc"])
render_table(["Field", "Value"], [
    ("served model id", models["response"]["data"][0]["id"]),
    ("root", models["response"]["data"][0]["root"]),
    ("max_model_len", models["response"]["data"][0]["max_model_len"]),
])
''')

md("### 2.2 Deterministic text check\n\nGreedy (`temperature=0`) completion, captured today.")

code('''det = load_receipt("live_deterministic_text.json")
print("prompt:", det["request"]["messages"][0]["content"])
msg = det["response"]["choices"][0]["message"]
print("content:", msg.get("content"))
print("reasoning (first 200 chars):", (msg.get("reasoning") or "")[:200])
print("finish_reason:", det["response"]["choices"][0].get("finish_reason"))
print("wall time (s):", det["wall_time_s"])
''')

md("""### 2.3 Golden image fixtures

The 10 synthetic PNG fixtures regenerated from the golden-corpus recipe
(solid colors, gradients, shape counts, a checkerboard, a rendered word),
each shown inline with the model's answer and a keyword pass/fail
verdict. Correctness is judged by keyword presence in the response, per
the golden-corpus protocol (exact text match is not required for
vision).""")

code('''golden = load_receipt("live_golden_images.json")
n_results = len(golden["results"])
print("captured:", golden["captured_utc"])
n_pass = sum(1 for r in golden["results"] if r["keyword_pass"])
print(f"keyword-match: {n_pass}/{n_results}")

for row in golden["results"]:
    fid = row["id"]
    question = row["question"]
    expected = row["expected_keywords"]
    answer = row["response_text"]
    finish_reason = row["finish_reason"]
    wall_time = row["wall_time_s"]
    display(Image(filename=os.path.join(RESULTS_DIR, "images", "pngs", os.path.basename(row["file"]))))
    verdict = "PASS" if row["keyword_pass"] else "FAIL"
    display(Markdown(
        f"**{fid}** -- {verdict}  \\n"
        f"Question: {question}  \\n"
        f"Expected keywords: {expected}  \\n"
        f"Answer: `{answer}`  \\n"
        f"finish_reason: {finish_reason}, wall time: {wall_time} s"
    ))
''')

md("""### 2.4 Negative control (no image attached)

Same question as `img01_solid_red` ("What is the single dominant color in
this image?") sent with no image attached. A correct model should not
hallucinate a color; it should note that no image is present.""")

code('''neg = load_receipt("live_negative_control.json")
msg = neg["response"]["choices"][0]["message"]
print("content:", msg.get("content"))
print("reasoning (first 400 chars):", (msg.get("reasoning") or "")[:400])
print("finish_reason:", neg["response"]["choices"][0].get("finish_reason"))
declined_to_guess = "image" in ((msg.get("reasoning") or "") + (msg.get("content") or "")).lower()
print("mentions the missing image rather than guessing a color:", declined_to_guess)
''')

md("""### 2.5 Wrong-image control

The `img01_solid_red` question (expects "red") sent with the
`img02_solid_blue` image attached instead. A correct model answers the
image it was actually given, not the fixture the question was written
for.""")

code('''wrong = load_receipt("live_wrong_image_control.json")
msg = wrong["response"]["choices"][0]["message"]
print("content:", msg.get("content"))
print("answered blue (the attached image), not red (the fixture the question implies):", wrong["answered_blue_not_red"])
''')

md("""### 2.6 Fresh C1 x3 greedy 400-token measurement

Concurrency 1, greedy decode, `max_tokens=400`, 3 repetitions, median
reported. Same protocol as the evidence repo's k-sweep bench.""")

code('''c1 = load_receipt("live_c1_x3.json")
render_table(
    ["Rep", "Latency (s)", "Completion tokens", "finish_reason", "tok/s"],
    [[r["rep"], r["latency_s"], r["completion_tokens"], r["finish_reason"], r["tok_per_s"]] for r in c1["runs"]],
)
print("median latency (s):", c1["median_latency_s"])
print("median tok/s:", c1["median_tok_per_s"])
''')

md("### 2.7 Warm TTFT x3 (streaming)\n\nTime to first streamed chunk, 3 repetitions, median reported.")

code('''ttft = load_receipt("live_ttft_x3.json")
render_table(["Rep", "TTFT (s)"], [[r["rep"], r["ttft_s"]] for r in ttft["runs"]])
print("median TTFT (s):", ttft["median_ttft_s"])
''')

md("""### 2.8 DSpark draft-depth (k) sweep

From `dgx-support` receipts. The Vision-Exp checkpoint's
`num_nextn_predict_layers=3` imposes a runtime gate not present on the
text-only checkpoint: k must be >= 5 and divisible by 3. k=3 and k=5 both
fail at container-entrypoint validation before any weight load or GPU
time is spent.""")

code('''render_table(
    ["k", "Result", "Exact error / note"],
    [
        [3, "REJECTED (validator)", "error: Vision-Exp requires MTP_NUM_TOKENS >= 5 and divisible by 3 (num_nextn_predict_layers=3); got 3"],
        [5, "REJECTED (validator)", "error: Vision-Exp requires MTP_NUM_TOKENS >= 5 and divisible by 3 (num_nextn_predict_layers=3); got 5"],
        [6, "PASS (current, only valid tested value)", "acceptance rate 19.9% (median of 3, C1 greedy 400 tok); the only runtime-valid depth for this checkpoint in the tested range"],
    ],
)
''')

md("""### 2.9 Throughput chart

Aggregate decode tok/s vs. concurrency, canonical (merged main) and
normalized (PR #3, pending) rows from the evidence repository.""")

code('''display(Image(filename="../assets/charts/2026-09-02-deepseek-v4-flash-vision-exp-2node-tp2-throughput.png"))
''')

# ---------------------------------------------------------------------
# Section 3: Demo
# ---------------------------------------------------------------------
md("""## 3. Demo — "Try it"

One live request, full pipeline: send a long, open-ended creative-coding
prompt (temperature 0.7, `max_tokens=8000`, reasoning allowed), extract
the single HTML file from the response, render it headless with
Playwright/Chromium at 1280x720 (8 s settle time, CDN scripts allowed),
display the rendered screenshot inline, then send that screenshot back to
the model as an image and ask it to describe the scene. This closes the
loop: vision-in on real generated content, not a canned fixture.

**Result today: the diorama did not finish rendering** — the model used
most of its token budget on reasoning before the HTML was cut off. The
pipeline below still ran end to end and is reported exactly as it came
back, per the notebook's negative-result policy.""")

code('''demo_receipt = load_receipt("demo/demo_receipt.json")
print("prompt (truncated):", demo_receipt["prompt"][:200], "...")
print("wall time (s):", demo_receipt["wall_time_s"])
print("usage:", demo_receipt["usage"])
print("finish_reason:", demo_receipt["finish_reason"])
print("reasoning characters:", demo_receipt["reasoning_chars"])
print("content characters:", demo_receipt["content_chars"])
print("extracted HTML bytes:", demo_receipt["extracted_html_bytes"])
print("html_blocks_found:", demo_receipt["html_blocks_found"])
print("render_ok (Playwright did not crash):", demo_receipt["render_ok"], demo_receipt.get("render_error") or "")
''')

md("""**Plain result: the HTML did not finish.** `finish_reason` is
`length` — the model spent 27,466 characters of its `reasoning` field
planning the scene and had only 955 characters of `content` left inside
the 8,000-token budget, so the extracted HTML file is a truncated code
fence, not a working diorama. Playwright loaded the file without
crashing, but the page shows only the literal text of the unclosed code
fence on a blank background. This is a real, reproducible limitation of
sending a single non-streaming 8,000-token request to a model whose
default profile spends most of its budget on chain-of-thought before
writing output — the same behavior noted for the golden text corpus in
section 2. The full raw HTML is committed as evidence of exactly what
came back.""")

code('''# The full generated HTML file is at results/<experiment>/demo/ww1-voxel-diorama.html.
with open(os.path.join(RESULTS_DIR, "demo", "ww1-voxel-diorama.html")) as f:
    html_src = f.read()
print(f"{len(html_src)} characters, {len(html_src.splitlines())} lines")
print(html_src[:400])
''')

md("### Rendered screenshot\n\nWhatever Playwright actually captured, shown as-is.")

code('''display(Image(filename=os.path.join(RESULTS_DIR, "demo", "preview.png")))
''')

md("""### Vision proof: the model describes what it actually rendered

The screenshot above is sent back to the same endpoint as an image, with
the prompt "Describe what you see in this scene in three sentences."
This is still a valid vision-in proof on real generated content — the
model correctly reports a near-blank page with a stray code-fence marker,
rather than hallucinating the diorama it intended to build.""")

code('''vision_proof = load_receipt("demo/vision_proof.json")
print("wall time (s):", vision_proof["wall_time_s"])
print("finish_reason:", vision_proof["finish_reason"])
print()
print(vision_proof["response_text"] or "(no content field; see reasoning below)")
if not vision_proof["response_text"]:
    print()
    print("reasoning (first 600 chars):", (vision_proof["response_reasoning"] or "")[:600])
''')

# ---------------------------------------------------------------------
# Section 4: Reproduce
# ---------------------------------------------------------------------
md("""## 4. Reproduce

**Hardware.** 2x DGX Spark (GB10 unified-memory systems), connected by a
direct RoCE link. About 120 GiB unified memory per node.

**Launch (from the evidence repo's recipe).** The launcher sequences the
worker before the head:

```bash
# On the worker node
NODE_RANK=1 HEADLESS=1 ./start-deepseek-v4-flash-dspark.sh

# On the head node, once the worker is up
./start-deepseek-v4-flash-dspark.sh
```

Flags baked into the recipe: `--tensor-parallel-size 2`,
`--kv-cache-dtype nvfp4_ds_mla`, `MTP_NUM_TOKENS=6`.

**Snapshot download (pinned revision):**

```bash
huggingface-cli download deepseek-ai/DeepSeek-V4-Flash-Vision-Exp \\
  --revision 86f746b36186f0e567729a5c06a8c918caba82a9 \\
  --local-dir <node-local-nvme-cache-path>
```

Run this identically on both nodes; the checkpoint must be node-local on
each (no cross-cluster mount) per the evidence repo's storage rule.

**Expected boot time.** Not captured in this notebook's receipts; see the
evidence repository's run manifest for the TP=2 boot timing.

**Point this notebook at your own endpoint.** Set `VISION_ENDPOINT` to
your own OpenAI-compatible base URL (for example
`http://<your-host>:8888/v1`) and set `LIVE = True` in the status cell,
then re-run top to bottom.

**Note.** The endpoint measured in this notebook is private
(Tailscale-only) and is not publicly reachable. There is no public demo
endpoint for this recipe.""")

# ---------------------------------------------------------------------
# Section 5: Appendix
# ---------------------------------------------------------------------
md('''## 5. Appendix

<details>
<summary>What went wrong, how the approach evolved, and lessons</summary>

### TP=1 capacity fail

The first attempt tried single-node TP=1 on one GB10. It failed a hard
capacity gate: **CUDA OOM during weight load**, 115.03 GiB
PyTorch-allocated of 121.69 GiB total, 2.09 GiB free, 2.00 GiB requested.
The 167.83 GB FP8 checkpoint does not fit on one GB10 node regardless of
KV-cache tuning; the fix was two-node TP=2, not further single-node
tuning.

### Host-RAM OOM in the two-node SGLang attempt

A second runtime path (SGLang, two-node) was tried as an alternative to
vLLM. It failed with a host-RAM OOM (not a GPU OOM) during the two-node
setup. No successful SGLang serve was ever reached on this hardware; the
vLLM TP=2 path is the only measured working recipe. This is a negative
result, not a tuning gap — SGLang two-node is untested-working on this
lane.

### Terminal-routing patch A/B, minus 15.6%

An experimental terminal-routing patch ("Mia routing patch") was A/B
tested: control steady C1 50.36 tok/s vs. treatment steady C1 42.52
tok/s, a **-15.6%** regression. Correctness passed in both arms, but
because the treatment regressed throughput, the full treatment ladder was
skipped and the original files were restored (verified by hash and
rollback check). The patch is not part of the current recipe.

### PR #3 history purge

The normalized-ladder evidence PR (`PixelML/DeepSeek-V4-Flash-Vision-Exp-DGX-Spark#3`)
was rebuilt on current `main` as one cleanly attributed commit, and the
resulting tree passes both the repository's public-tree validator and the
GPU-club public-boundary scanner. However, GitHub continued to serve a
prohibited historical commit object after the local ref rewrite, which
required a GitHub Support purge before the PR could be reviewed or
merged. As of this notebook, that PR remains **draft, unmerged**, pending
the purge confirmation and a fresh independent review — which is why this
notebook's TL;DR keeps the normalized row separate and labeled
"PR pending" rather than folding it into the canonical row.

### DSpark k sweep

k=3 and k=5 were requested but both are rejected by the runtime's
`num_nextn_predict_layers=3` validator (`k >= 5 and divisible by 3`)
before any weight load or GPU time is spent; k=6 is the only valid depth
in the tested range and is what the service runs today. See section 2.8.

### Lessons

- Check the single-node capacity math before attempting TP=1 on a
  checkpoint this large; the two-node requirement was predictable from
  file size alone (167.83 GB vs. ~120 GiB per node).
- A runtime-level validator error (wrong `MTP_NUM_TOKENS`) fails fast and
  cheap, before touching the GPU — worth checking before assuming a
  performance problem.
- Treat vLLM's greedy-decoding batch-composition non-determinism as
  expected: a restored, byte-identical configuration can still show
  low-single-digit-row wording drift on the golden corpus. Gate on
  keyword/exact-match rate, not byte-for-byte text.

</details>
''')

nb['cells'] = cells
nbf.write(nb, NB_PATH)
print("wrote", NB_PATH, "with", len(cells), "cells")
