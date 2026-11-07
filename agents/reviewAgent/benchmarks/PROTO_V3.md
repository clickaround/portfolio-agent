# ArchPortfolioBench v3 pre-registration

## First compare
Same input project, same page dimensions, same briefing, same time/token budget. B0 host directly, B1 + domain knowledge, B2 + lawful case retrieval, B3 + structured storyboard, B4 + backend + hard gates, B5 + targeted review/repair. Run separately for Claude and Codex; backend and harness are independent axes. Report improvements/declines and 95% uncertainty bounds where meaningful; no fake significance at n=5.

## Independent test axes
- Content: preserved, credited project facts, design decision evidence, coherent *book-level* page sequence.
- Hard geometry: finite numbers, within trim/safe, permitted overlap layering, minimum font sizes, bleed, raster effective PPI, source preservation, no unintended image crop.
- Editing: original objects editable, fixed target and no unintended diff, reverse/redo.
- Media/format: A4/A3/square/custom/slide, native vs print export parity, reflow not resize-only, multi-page facing spreads.
- Human preference: randomized blind paired comparisons, domain practitioners, issue comments, prevent source/creator leakage; reject 'looks like AI report' as a measurable criterion (generic-card repetition, equal-height grid, irrelevant text).
- Cost/latency: per attempt, per valid result, all tokens and rerenders, human correction time.
- Host/plugin: install, activation, files, session restart, backend failure, blocked recovery.

## Hard gates before preference
Off-page geometry, missing important evidence, source fact fabrication, export corruption, changed source hashes, unreadable font, major crop, unsupported client license. If hard gate fails no high aesthetic score can rescue output.

## Output
`reports/<run-id>.json` with `source_case_ids` (restricted), `output_format`, `renderer`, `host`, `model`, `sha`, `prompt_version`, `hard_gates`, `scores`, `human_preferences`, `cost`, `latency`, `evidence_paths`, `blinded` and `status`.

Each runner uses a unique directory under `.cache/bench_ap/` or `.cache/bench/`; it does not delete a previous run. The AP runner writes a unique `reports/apbench-<run-id>.json`; the engine regression runner writes a unique `results/engine-regression-<run-id>.json`. These synthetic subsets record fixture hashes, Git revision and dirty state, Python and PyMuPDF versions. Existing historical reports are retained and may contain paths from the former layout; for example their `evidence/logs/` references now live under `project/evidence/logs/`. A failed measured AP-03 or a task crash produces a nonzero runner exit; this is not an assertion that unmeasured tasks or human review passed.

## Data splits
Separate by creator/project, not just page. Do not retrieve heldout examples into the prompt. Rights clearance controls which use types are allowed. Synthetic fixtures are only engineering checks.
