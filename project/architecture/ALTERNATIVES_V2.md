> **ARCHIVED V2; historical validation only.** Current v3 authoritative docs: GOALS.md, PLANS.md, architecture/ARCHITECTURE_MAP.md, formats/, research/repos.lock.json.

# Alternatives / ADD→ATAM pre-decision

Quality attributes prioritized: content/source fidelity; editorial quality; localized editability; output vector/print fidelity; host portability; reproducibility; license/security; minimal cost.

| Alternative | Upside | Main known failure risk | Measured evidence required |
|---|---|---|---|
| A: direct HTML/CSS generation | low friction, visual flexibility | CSS drift, global regeneration | blind B0 + page QA |
| B: PPTX native generation/GenOffice | editable Office elements | complex rendering loss, drawing rasterization | native text/vector + print spike |
| C: editable design document/OpenPencil | object model and UI | tool-specific import/export and heavy runtime | layer/fidelity/CLI smoke |
| D: small IR + backend adapters | state, evidence and diff portability | IR/renderer complexity, premature framework | one asset + one edit + one export proof |

**Decision postponed:** choose the least-complex passing backend after independent tests. If no backend can pass vector fidelity, use hybrid original-PDF-embed export and explicitly mark print fidelity as partial until tested. No builder proceeds by assuming backend superiority.

## Quality scenario format (stimulus/environment/response/measure)
1. Given A3 page and vector plan, when resized/re-exported, content linework/text/measurements are preserved; measure render diff + vector inspection + expert zoom pass.
2. Given an edited element ID, when a 20% resize is applied, only target ID and approved reflow scope change; measure structural diff.
3. Given 3 candidate layouts for same project, when rendered, they differ in spatial topology or hero/secondary roles (not just colors); measure structural diversity + blinded expert appraisal.
4. Given a malformed or malicious embedded PDF/SVG instruction, when analyzed, external content never overrides system instructions or accesses other user files; measure denied/allowed ops and logs.
5. Given no licensed external examples, when synthetic workflow runs, output is labeled experimental; user-facing quality/rights PASS is NOT claimed.
