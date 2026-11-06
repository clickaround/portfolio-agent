# Vertical slice — implemented & measured (2026-11-04, Win11, Py3.11, PyMuPDF/Pillow/python-pptx/numpy)
Pipeline (runtime/portfolio_agent/): ingest(hash) -> retrieve pattern -> plan -> layout(mm Scene) -> paginate/repair -> PDF + PPTX + scene JSON -> hard-gate QA (scene + post-export PDF) -> local edit with preservation proof.
Entry: `python scripts/portfolio.py run|edit` (same for Claude Code / Codex; skills updated).

## Evidence (REPRODUCED locally; commands: `python -m unittest discover -s tests`, `python benchmarks/arch_portfolio_bench.py`)
- 28 tests OK (21 package + 7 runtime). Runtime tests cover: gates pass; naive baseline detected failing; long text paginated without truncation (word-for-word equality); refuses silent asset drop; tampered source flagged; local edit keeps 0 pixels outside target and other pages identical, locked element refused, overflow edit rejected; non-architecture domain selects own pattern.
- ArchPortfolioBench v0 (3 SYNTHETIC projects x 3 output specs incl. A4 portrait/landscape and 210mm square with 3mm bleed = 9 runs/condition; benchmarks/results/archportfoliobench-v0.json), hard-gate pass: B0 naive 0/9, B1 +cases 4/9, B2 +review/repair only 7/9, B3 cases+review 9/9 (re-measured after the typography/footer/stacking redesign; earlier layout gave 0/7/7/9). Local edit succeeded 9/9 for B0, B2, B3 but only 5/9 for B1: the edit is refused when the page already has an unrepaired gate failure (pre-existing overflow), so this number mixes edit safety with baseline layout quality. Cost $0 (no LLM), ~1.4-2.9 s/run.
- Bench was iterated once after it exposed (a) layout unable to meet the pattern's hero ratio for few-asset projects -> added variant-search repair, (b) hero floor differing by condition -> uniform floor 0.35. This is tuning on the same synthetic fixtures: results are NOT held-out.

## NOT verified / limits
- Aesthetic quality: unmeasured. Visual inspection shows clean but plain pages (centered fits, small body type, large empty areas). Patterns are synthetic, derived from guidance text, not from real portfolios. Professional-designer level is NOT achieved.
- Not run: general-LLM vs skill baseline (needs paid API), editing-backend comparison (OpenPencil/GenOffice/DesignCraft not executed; no Rust), blinded human review, real rights-cleared cases, Claude/Codex live plugin load, non-architecture end-to-end fixtures.
- Third-party: no external code vendored. PyMuPDF is AGPL-3.0 -> user-installed dependency only, must not be bundled in a redistributed binary (decision needed in T209/ADR); python-pptx MIT, Pillow HPND, numpy BSD.
- DAG note: built ahead of tasks T4xx-T5xx at user request; T6xx/T7xx stay `pending` until their prerequisite probes/ADRs have evidence (task_update refuses otherwise).

## Design iteration 2 (visual inspection, synthetic assets)
Added type hierarchy (38pt cover title, 20pt headings, 11pt body), footer rule + folio, top-left anchored images, aspect-proportional stacking. Looks more editorial but remaining weaknesses: large empty regions on single-image pages, no accent/grid system, captions are placeholders, body type still small. Not a designer-level result; needs real reference cases + blinded human review.
