# DGX Spark source registry

Curated external DGX Spark ecosystem sources reviewed by PixelML. This is a
learning registry, not a link dump: every entry records the exact revision,
evidence level, what we learned, and the next experiment. PixelML never
converts upstream numbers into PixelML results.

Entry requirements: exact upstream revision, license noted at review time,
review date, hardware/topology scope, claimed result, evidence type,
reproduction status, reusable learning, limitations, and a canonical
PixelML experiment link when one exists.

## Evidence levels

| Level | Meaning |
|---|---|
| **upstream/community-reported** | Numbers are the source authors' own measurements on their hardware; PixelML has not reproduced them. |
| **PixelML independently reproduced** | PixelML re-ran the recipe (or its material equivalent) on its own cluster and confirmed the headline claim within stated bands. |
| **PixelML measured differently** | PixelML measured a materially different result; the delta and protocol differences are documented in the linked evidence. |

When an entry says **PixelML independently reproduced**, a dated receipt must
exist in the linked PixelML repository. Community numbers never enter PixelML
results tables without that receipt.

## Inclusion and quality criteria

1. **Primary sources only** - a recipe, harness, or measurement from its own repository, pinned to an exact revision. Social posts are not entries.
2. **DGX Spark relevance** - must run on, measure, or materially affect GB10/SM121 work.
3. **Reusable learning** - the entry teaches something transferable: a kernel workaround, topology limit, eval method, or operational hazard.
4. **Verifiable claims** - numbers must state protocol (concurrency, temperature, thinking mode, token counting) or be labeled directional.
5. **Living review** - re-review a source when its upstream moves materially; record the new revision and what changed.

## Registry

External ecosystem: [ECOSYSTEM-SOURCES.md](ECOSYSTEM-SOURCES.md) - NVIDIA, jvr0x, jasonacox, dataforgex.
MiaAI-Lab: [MIAAI-SOURCES.md](MIAAI-SOURCES.md) - serving, quantization, speculative decoding, eval, monitoring, topology.
PixelML experiments: [../EXPERIMENTS.md](../EXPERIMENTS.md) and [../COVERAGE-MATRIX.md](../COVERAGE-MATRIX.md).

## Update contract

See the curation contract in [AGENTS.md](../../AGENTS.md). When you learn from
or use any of these sources, update the entry with what changed and what
PixelML should measure next.
