# Layout v2 (craft rules), LLM book-plan path, harness guardrails - 2026-11-05

## What changed (all tests: 81 OK, validator PASS)
1. **Research first** (knowledge/editorial/layout-craft.md, cited): 12-column grid with gutters/flowlines/markers (UW grid handout), margins canon (Van de Graaf 2:3:4:6 principle), body 10-12 pt and leading 120-145 % (Butterick), measure 45-75 chars (Bringhurst), modular scale 1.25, portfolio practice (illustrarch: one grid for the whole book, captions in a fixed marker, 2-3 page templates). Credits/claims: Georgia Tech guidance.
2. **New layer `runtime/portfolio_agent/layout/`** (core <- layout <- authors): `typesystem.py` (tokens -> per-role style, CJK-safe display font), `compositions.py` (cover, feature column/banner, hero full/column, plate column/band, pair row/stack/side, grid, text, closing; every page hangs from one flowline, snaps to columns, keeps markers fixed), `book.py`. Rule-based author keeps only editorial rules (`plan.py`: section walk, credits -> closing statement, page-shaped photos reserved for cover/hero).
3. **LLM path**: `authors/planned` + `contracts/book-plan.schema.json` + CLI `compose`: the host decides sequence/roles/assets/words/variants/tokens and never writes coordinates. Duplicate assets refused unless declared.
4. **Harness guardrails (ADR-0009, from AutoDesign)**: `core/guardrails/{policy,gates,grounding,repair,references}`; blocking vs advisory; TYPE_TOO_SMALL; TEXT_UNGROUNDED (lexical G4 proxy); `attempts/NN` + `ledger.jsonl`; `engine/review.py` fresh-review binding (`review-context` -> independent reviewer -> `record-review` -> `finalize`).
5. **DesignCraft** now receives scene v0.2 typography: font family/style, colour swatches, alignment, leading, shape fills (verified render: evidence/logs/layout-v2-sheets/look_dc.png).

## Blind critic, same project, one critic, synthetic assets (noise ~ +-0.07)
| candidate | mean | note |
|---|---|---|
| B0 host direct | 0.74 | stable across 5 sessions (0.71-0.76) |
| rule-based engine v2 (this layout layer) | **0.64** | was 0.45 before the craft rewrite (+0.19) |
| B4-plan (LLM book plan -> same layout layer) | 0.60 | $3.02, 41 turns, 268 s; critic: repeated assets, off-grid column, padded to 6 pages |
Critic issues on engine v2 that were fixed after scoring (unscored): banner text band now spans the width; plate switches to band form when width-limited; display title 38 pt; hero-column type stays on the left margin. Pending re-score.
Interpretation: the gap to B0 narrowed from 0.29 to 0.10 with cited craft rules and no LLM. The LLM plan did not beat the rule plan on n=1; its failures were editorial (repeats, padding), now guarded (duplicate-asset refusal). Still NOT professional-quality evidence: synthetic images, one LLM critic, no human review, NO_EXTERNAL_REFERENCE.

## Artifacts
Contact sheets: evidence/logs/layout-v2-sheets/*.png (arch_01/02, ux_01, photo_01, brand_01, B4-plan, DesignCraft render, B0). Critic: evidence/logs/blind6-b0-enginev2-b4plan.txt; report benchmarks/reports/b0-enginev2-b4plan-arch01-20261105.json. B4-plan inputs/outputs: evidence/logs/b4plan/. AutoDesign notes: research/PAPER_NOTES_AUTODESIGN_HARNESS.md.

## Regression bench (benchmarks/engine_regression_bench.py, 3 projects x 3 specs x 4 conditions, 2026-11-05)
crashed 0 (a pagination KeyError was fixed). B3_full: 8/9 blocking-pass; the one failure (arch_03 A4-portrait: caption column too narrow -> TEXT_OVERFLOW at the 8 pt floor) was fixed afterwards by two portrait rules: hero column form only when >= 3 text columns remain; a width-limited cover hero hangs from the bottom flowline; mixed pairs stack when both rows stay readable. B0/B1/B2 failures are expected ablations (REPEATED_LAYOUT advisory in B0; unpaginated overflow with review off). Portrait sheets: evidence/logs/layout-v2-sheets/look_arch_01_portrait.png, look_arch_03_portrait.png.

## Re-score (blind7, same critic protocol): B0 0.78 (pass) > B4-plan 0.66 > engine v2.1 0.59
Identical B4-plan and B0 PDFs moved +0.06 / +0.04 between sessions: single-LLM-critic noise is about +-0.07, so the post-score engine fixes (0.64 -> 0.59) are within noise, NOT a regression or an improvement. Critic on engine v2.1: heading scale too flat (headings ~ body size), banner page leaves the bottom third empty, plate hugs the left with an orphaned caption top-right, "assets reused" (false: synthetic images of the same generator look alike - critic limitation). Acted on: heading 3 scale steps above body, banner text on the hang line with the image on the bottom flowline, plate centred with the caption under the heading. Conclusion stands: more critics or humans are needed before any score difference < 0.1 means anything.

## Blind8: B0 0.78 (pass) > B4-plan2 0.65 > engine v2.2 0.59
Series on the same project (one critic per session): B0 0.74/0.78/0.78; rule engine v2/v2.1/v2.2 0.64/0.59/0.59; LLM book plan v1/v2 0.60-0.66/0.65.
Reading: the rule engine plateaus near 0.6 (its 0.64 was within noise); the LLM plan sits ~0.65 with the grounding/duplicate guards now firing in practice; B0 stays ~0.76. The remaining gap is editorial voice (display type contrast, statement pages, running heads as a system) - the critic praises B0's "Didone display + italic" and penalises our "eyebrow + small heading on every page". Next lever is the type system (bigger display/heading contrast, fewer identical page tops), not more geometry rules.

Fixture caveat (affects every candidate equally): the synthetic plan PDF and section images carry large internal white margins, so any "plate" or "banner" built from them reads as floating or half-empty to the critic; gates forbid cropping (allow_crop false). Real drawings would not have this. Post-blind8 changes: plate prefers column form (drawing leads) unless clearly short; pair/grid pages get fallback captions ("Drawing 01", "View 02") when sections are exhausted.

## Codex host (codex-cli 0.166.0, `codex exec --approve-for-me`) ran the SAME `compose` path - REPRODUCED
3 attempts, all gate_pass with 0 blocking / 0 advisory, 57.9k tokens, ~4 min; the host read previews and revised sequence/variants/closing statement. Two earlier attempts failed for harness-prompt reasons, not engine reasons: (1) my TOOL RULES forbade all shell commands except the engine CLI, and Codex has no separate file-read tool -> it stopped and asked for `Get-Content`; (2) `codex exec` blocked on a piped stdin. Fixes: skill text now allows read-only shell reads; run with `< /dev/null`. Artifacts: evidence/logs/codex-plan/ (plan, pdf, ledger, blocked log), sheet evidence/logs/layout-v2-sheets/look_codex_plan.png. Not blind-scored yet.

## First REAL sources (2026-11-05 afternoon): Frederick C. Robie House, HABS ILL-1005 (public domain)
Sources: 8 measured-drawing sheets + 3 photographs from Wikimedia Commons (HABS 1963; license "Public domain" per extmetadata; PROVENANCE.json records title, source URL, sha256). New `prepare` step: proposes a crop per scanned sheet (inner frame minus title block; photographs never trimmed), writes a proposal sheet for approval, then keeps originals byte-identical in `sources/` and records every crop in `derived.json` -> manifest `source_transform`.
- Rule engine: 8 pages, gates pass, ~9 s. Weak spots: generic "Drawings I/II/III" headings and asset-id captions when sections run out; a 3-asset guillotine page with two tiny elevation sheets.
- LLM book plan (Claude Code, `compose`): $4.55, 78 turns, 6 min, 3 attempts (REPEATED_LAYOUT then TEXT_UNGROUNDED advisories fired and were fixed by the host), 10 pages; used grid_system swiss-12 and compositions plate-caption-left / pair-row-heading-top / plate-centred-notes-right / margin-notes-plate; every caption names the sheet content (floor, scale, what is shown) from the previews + project.md. Visibly the best output so far; not blind-scored yet.
Artifacts: evidence/logs/robie/ (plan, pdfs, ledger, provenance), sheets evidence/logs/layout-v2-sheets/robie_*.png, catalogue_robie_guides.png.

## Blind9 on REAL sources (Robie): B0 0.76 (pass w/ caveats) > LLM plan 0.60 > engine 0.51 (fail)
Engine was scored with the first diagram-page bug (a SYNTHETIC diagram strip under the heading "Plan" -> blocker, fixed after). B0 ($0.4252519) did what our two paths still do not: a coloured spine on the cover, sentence headings ("Bedrooms above"), bold-lead captions ("First (ground) floor plan. The garage..."), an index-of-sheets page, accent italic pull quotes. Those are the next features for the layout layer and the book-plan vocabulary (caption lead, index page, spine/accent band), not more grid rules.

## Predictions (AHE decision observability) — to be checked by blind10 (B0 vs engine v3 vs LLM plan v3 on Robie)
- P1: the brick-red cover band + warm pptAgent palette raise the critic's `anti_template` for engine/LLM by >= 0.1 vs blind9.
- P2: real conceptual diagrams (diagram-design skill) remove the "synthetic placeholder" blocker on the engine's process page; `domain_fit` >= 0.6.
- P3: index-of-sheets + bold-lead captions lift LLM plan `sequence_narrative` >= 0.7.
- P4: engine still trails the LLM plan by >= 0.05 on `hierarchy` because its headings are section names, not claims.

## Blind10 (Robie, real diagrams, pptAgent palette + spine): B0 0.76 > LLM plan v3 0.65 > engine v3 0.52
Predictions: P1 half (LLM +0.10 on anti_template, engine +0.05), P2 yes, P3 yes, P4 yes. LLM plan is 0.05 better than its v2 (0.60) and 0.11 below B0; the critic's remaining high issue on the LLM plan is the diagram page (one diagram huge, three tiny: it chose a large-small composition) and on the engine the generic headings/captions. Decision: keep the engine as fallback; put effort into the host skill (headings as claims, diagram page = 2x2 block) and real human review.
