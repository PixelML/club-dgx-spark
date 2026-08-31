# Repository instructions for agents

This is a public repository. Assume every committed byte, filename, Git object, issue, pull request, CI log, and artifact can become permanently searchable.

## Publication boundary

Never publish:

- passwords, tokens, cookies, API keys, private keys, credential locations, or secret-manager paths;
- private or overlay-network IPs, public rental IPs, hostnames, MAC addresses, serial numbers, full GPU UUIDs, exact private PCI maps, or physical locations;
- account/instance IDs, billing or purchase details, vendor conversations, customer data, private prompts, personal information, or unrelated model outputs;
- unredacted logs, shell history, environment dumps, SSH configuration, `.env` files, service names tied to private infrastructure, or private repository content;
- model weights, license-restricted artifacts, compiled third-party binaries, or data that cannot be redistributed.

Do not copy private repository history or raw live-state dumps. Reconstruct public documentation from verified facts and use generic terms such as “DGX Spark node,” “dual-node test,” and “shared model storage.” If a value is unnecessary for reproduction, omit it. If uncertain, stop and ask the repository owner.

## Repository routing

- `club-dgx-spark` contains platform-wide guidance, common tools, concise comparison tables, and links.
- A model-family repository contains the full experiment: recipes, patches, all quantizations/sizes/runtimes/topologies, raw redacted results, and failures.
- Do not create a new repository merely because quantization, runtime, checkpoint size, or node count changed.
- Use a new repository when the model family or non-model workload is genuinely distinct.
- Every detailed experiment PR should add or update a compact linked summary in `club-dgx-spark`.

## Evidence rules

- Label claims **measured**, **inferred**, **community-reported**, or **untested**.
- Record hardware count, topology, power mode, software/model revisions, quantization, runtime configuration, prompts/workload shape, sample count, and metric calculation.
- Preserve negative results and incompatibilities with the exact tested boundary.
- Count generated tokens from the final usage object, never from stream-event count.
- Never invent measurements, versions, citations, or successful tests.
- Do not publish a new measured benchmark as an index row alone. Add a runnable `recipes/<model-runtime>/reproduce.ipynb` with immutable pins, clean recorded outputs, structured source data, a generated chart, and an editable final `curl` request.

## Infrastructure safety

Agents may run read-only checks by default. They must not reboot nodes, change networking, power, storage, firmware, containers, services, or running workloads; download models; build software; or launch benchmarks without explicit authorization.

For authorized workloads, define temperature, power, storage, process-conflict, and error stop conditions before launch. Do not interrupt an existing job unless the user explicitly authorizes it.

## Required pre-publication gate

Before every commit, push, release, or pull request:

1. Review the complete staged diff and every new filename.
2. Run `git diff --cached --check` and targeted secret/infrastructure scans.
3. Check for large files, binaries, archives, model weights, dumps, and unsafe symlinks.
4. Review relevant Git history when content came from another repository or live machine.
5. Verify claims have redacted evidence and primary-source links.
6. Run `python3 scripts/validate_recipe_notebooks.py` when a recipe or benchmark result changes.

Suggested checks:

```bash
git diff --cached --check
git diff --cached --stat
git diff --cached
git grep -nEI '(api[_-]?key|access[_-]?token|authorization:|bearer |password|private[_-]?key|BEGIN [A-Z ]*PRIVATE KEY)'
git ls-files -s | awk '$1 == "120000" {print $4}'
find . -type f -size +10M -not -path './.git/*' -print
```

Inspect every match; a matching word is not automatically a secret. Add targeted scans for IPs, hostnames, UUIDs, account identifiers, and source-repository metadata.

## Change discipline

- Preserve unrelated changes; never force-push.
- Use branches and pull requests; do not push directly to `main`.
- Do not add AI attribution to commits or pull requests.
- Do not weaken these instructions in nested files.
- Do not merge a result that lacks the publication and evidence checks above.


## Ecosystem curation contract

club-dgx-spark curates the broader DGX Spark ecosystem, not only PixelML
experiments. When you find novel, useful external work:

1. Add or update an entry in [docs/sources/](docs/sources/README.md) with the exact upstream revision, license, review date, and the three-level evidence label (upstream/community-reported, PixelML independently reproduced, PixelML measured differently). Never silently convert upstream numbers into PixelML results.
2. Every entry must answer: what did we learn, how strong is the evidence, did PixelML reproduce it, and what experiment should happen next?
3. Update [docs/SYNTHESIS.md](docs/SYNTHESIS.md) when a source changes a cross-cutting conclusion (topology limits, runtime compatibility, KV math, spec-decode behavior, ops hazards).
4. Detailed evidence stays in the canonical model repo; the club gets links and reusable guidance only. Do not mirror third-party weights or copy entire recipes.
5. Preserve attribution: name the upstream authors and link the pinned revision in every receipt that uses their work.
