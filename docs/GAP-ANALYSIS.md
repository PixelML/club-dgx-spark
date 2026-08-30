# Gap analysis — DGX Spark platform coverage

Compared against the club's practical mission, ranked by user impact, evidence risk, and effort.

## Covered

| Area | Where | Evidence |
|---|---|---|
| Dual-node LLM inference (TP=2) | All five model repos | Measured (GLM, Qwen) or recipe-published (Step, Hy3, Inkling) |
| Speculative decoding (MTP/NEXTN/DFlash2/DSpark) | GLM, Qwen (measured); Inkling (recipe-documented, untested) | Measured for GLM DFlash2/EXL3 and Qwen NEXTN; untested for Inkling DSpark |
| Multimodal input (image, video) | GLM, Qwen | Measured with mixed results: GLM image/video gates passed in throughput runs but one image gate failed during revalidation under memory pressure; Qwen image VQA passed. See pinned receipts. |
| Tool calling / OpenAI-compatible API | GLM, Qwen, Step, Hy3, Inkling | Measured (GLM, Qwen); recipe-documented (rest) |
| Uncached prefill benchmarking | GLM, Qwen | Measured |
| SM121 kernel workarounds | Qwen (Triton fallback), GLM (Marlin MoE + eager) | Measured |
| Direct CX7 RoCE networking | All dual-node repos | Measured (GLM, Qwen); recipe-documented (rest) |

## Gaps

### Priority 1 — high impact, low effort, fillable now

| Gap | Type | Evidence | Effort |
|---|---|---|---|
| Platform-level first-time setup guide (OS, NVIDIA driver, Docker, networking) | Missing evidence | Recipes imply requirements but no club-level bring-up walkthrough exists | Low — derive from verified dual-node recipes |
| Shared benchmark methodology doc (warmup, token counting, prefill vs decode, usage-object rule) | Missing evidence | Each repo embeds its own scripts but no club-level methodology is documented | Low — extract common pattern from GLM/Qwen receipts |
| Single-node recipes for any model | Untested | Every recipe is dual-node only; single-Spark coverage is zero | Low documentation, needs hardware to validate |

### Priority 2 — medium impact

| Gap | Type | Evidence | Effort |
|---|---|---|---|
| Thermal and power observations in any receipt | Missing evidence | No receipt records temperature, power draw, or sustained-power behavior | Low to add template; hardware to collect |
| Storage and model-cache layout guidance (local NVMe vs shared, rsync vs SSHFS) | Missing evidence | GLM uses rsync; Inkling uses SSHFS; no club-level guidance on when to use which | Low |
| Step-3.7-Flash hardware validation | Untested | Recipe is complete but results/ is empty; no known blocker | Medium — needs idle dual-Spark node |
| Hy3-295B hardware validation | Untested | Same as Step-3.7-Flash | Medium |
| Inkling-Small hardware validation | Untested | Same | Medium |

### Priority 3 — lower near-term demand

| Gap | Type | Evidence | Effort |
|---|---|---|---|
| 3+ node DGX Spark networking | Untested | No repo covers >2 nodes | High — needs hardware |
| Distributed training or fine-tuning | Untested | Zero coverage in any repo | High |
| Standalone image/video generation workload (non-LLM) | Untested | GLM multimodal inference is measured, but no dedicated image/video generation recipe exists | Medium |
| Single-node vs dual-node speedup ratio for same checkpoint | Untested | No repo provides both topologies for one model | Medium |
| Quality/cost-per-success evaluation alongside speed | Missing evidence | Speed is measured; no repo reports accuracy, correctness scoring, or cost per successful task alongside latency | Medium — needs benchmark tooling extension |

## Hypotheses for the highest-priority untested gaps

1. **Single-node GLM-5.3-Flash NVFP4** — hypothesis: the 181 GiB checkpoint does not fit into a single 128 GiB UMA Spark at any usable context; cheapest validation is a load attempt with `gpu-memory-utilization` reduced and minimal context. Falsifier: successful single-node start with >2K context.
2. **Thermal envelope under sustained decode** — hypothesis: sustained dual-Spark decode keeps both GB10 nodes below their thermal limit; cheapest validation is a 30-minute decode benchmark with thermal sampling every 30s. Falsifier: thermal throttling observed or temperature exceeds vendor threshold.
3. **Step-3.7-Flash no-MTP baseline** — hypothesis: the no-Ray vLLM recipe starts and serves on two Sparks with the documented image; cheapest validation is a bring-up with three prompt generations and container restart-count check. Falsifier: NCCL or SM121 kernel failure.

## Do not invent coverage

This matrix intentionally lists "untested" rather than filling gaps with unsupported recipes. A precise untested entry is more useful than a guess.
