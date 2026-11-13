# portfolioAgent Guardrails

<!-- Harness² C2 guardrails (guardrails.md). Every call. Hard constraints that hold regardless of task or tool. -->

1. The host never writes coordinates. It chooses plan fields and edit operations; rules compute geometry.
2. Facts, words and images come from the manifest and its source IDs only. Nothing is invented.
3. Source bytes are never modified by layout or export.
4. Every layout states medium, page size, units, margins, bleed and safe area. A3 is never forced.
5. Blocking gates (bounds, unintended overlap, missing elements, provenance, stale references, readability) are never bypassed. Failures are repaired or reported in `qa.json`.
6. An edit changes its target only; off-target changes are a gate failure.
7. Layers: `core <- layout <- authors/*, backends/* <- engine <- cli`. A new page device = `layout/<device>.py` + gate rule + schema field + test.
8. No deploy, purchase, secret access or mass scraping without the owner's permission.
