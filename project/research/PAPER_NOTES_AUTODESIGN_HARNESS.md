# AutoDesign (arXiv 2608.13560, Aug 2026) — the "design harness" paper, read for our harness design (2026-11-05)

Labels: DOC_REPORTED (paper HTML, first 100k chars) + CODE_INSPECTED (clone `.cache/vendor/autodesign` @ bd635851, Apache-2.0; `agent_skills/autodesign-poster/` SKILL.md, references/output-contract.md, references/review-rubric.md, scripts/poster_dom_audit.py). Nothing executed.

## What the paper says the harness IS (5 components x 4 stages)
Components (§2.1): **Context & Memory, Tools & Specifications, Execution Runtime, Orchestration, Evaluation & Feedback.**
Stages (§4): (1) ingestion -> content brief + artifact plan with source locations, built once; (2) a coding-agent *designer* writes/revises an editable artifact (HTML) with localized edits; (3) **validation + feedback**: deterministic *blocking* checks (unsafe/missing assets, broken provenance, severe overflow/overlap, typographic/layout constraints) and *non-blocking* checks (coverage, density, numeric consistency); a VLM critic runs only on candidates that fail; validator + critic are merged into one repair signal; at most K = 12 attempts, with fallback selection from the attempt history; (4) finalization.
Meta-harness optimizer (§3): a coding agent edits the harness itself (prompts/tools/feedback/loop policy), one component per iteration, accepted only if train improves and dev does not decline; 54 accepted updates over 7 days.

## Guardrails in the shipped skill (code-inspected; these are the parts that make it a *harness* and not a prompt)
1. **Scripts never edit the artifact.** `dom-audit` is strictly read-only and proves it: `artifact_tree_sha256_before == after`. All semantic repairs are made by the agent on a NEW attempt.
2. **Attempts are immutable and numbered**; a run has `attempts/NN/`, `provenance/`, catalog/plan *revisions*; a semantic repair opens a new attempt and keeps every previous attempt/review/receipt byte intact. `resume` returns the one safe `next_action`.
3. **Fresh review gate**: artifact review "may not be authored by the Agent pass that made the decisions being reviewed"; a review JSON must copy the exact hashes (artifact, previews, rubric, source map, review-context) or it is rejected; pass = zero blockers AND all frames reviewed AND mean >= 3.75/5 over 7 dimensions (impact, information architecture, evidence use, effort saved, typography craft, anti-template, editability/export).
4. **Two reviews, two moments**: source review BEFORE planning (which evidence is allowed), artifact review AFTER deterministic QA passes.
5. **Output contract as hard gates**: no scripts/remote assets/data URLs, exact dependency closure, one-page PDF at the planned physical size, minimum type sizes (title >= 56 px, body >= 24 px at poster scale), white canvas, every visible claim bound to a source id (claim/source map), native editable text (never a flattened screenshot).
6. **Deterministic DOM audit codes** (poster_dom_audit.py): root overflow, text overlap (>24 px^2), table overflow / small text, blank bands, sparse oversized panels, low effective image resolution, screen/print mismatch, template boxiness. Tolerances are explicit constants (4 px).
7. Validation renders in a **network-denied browser** and fails on any console/request error.

## Numbers worth keeping (self-reported)
PosterBench main: AutoDesign+Claude Code 78.32 vs native Claude Code 70.01 (+8.31 from the harness), Claude Design 70.87. Mini-track mean 54.99 -> 67.39 across 7 model configs (+12.4 points; the abstract's "%" is a unit slip). Human study: 11 reviewers, 933 rankings, Bradley-Terry top 64.0 %. **Benchmark-human correlation only r = 0.34**; agreement 51.9 % for score gaps 0-3 pts, 74.4 % for gaps >= 20. Cost $0.27-$10 per poster.

## What this means for *our* harness (gaps, in priority order)
| AutoDesign guardrail | Ours today | Gap / decision |
|---|---|---|
| blocking vs non-blocking checks | every gate blocks | split: provenance/geometry/export = blocking; REPEATED_LAYOUT, HERO_TOO_SMALL = advisory (reported, never silently dropped) |
| scripts never edit the artifact | `core/repair.py` shrinks fonts / nudges boxes (bounded, logged) | keep as an *explicit, logged, bounded* exception; add `--no-repair` for the agent path and record `touched` in attempts |
| immutable attempts + fallback | each run overwrites `out/` | `compose` writes `attempts/NN/` (plan hash, scenes, qa, previews) and `final/` = last passing attempt; fallback = fewest blocking issues |
| fresh review gate with hash binding | critic runs were ad-hoc shell commands | `review-context` + `record-review` in the engine; review JSON must bind scene/preview/rubric hashes; `finalize` refuses without a passing fresh review |
| claim/source map | asset sha256 + "facts from project.md only" (prompt rule) | advisory text-grounding check: every body/caption sentence must have >= 60 % lexical overlap with project.md (same lexical trick AutoDesign uses, `insufficient_lexical_overlap`) |
| minimum type sizes as hard gate | none | blocking: body >= 8 pt print, caption >= 6.5 pt (Butterick 10-12 pt body; portfolio practice 9-10) |
| network-denied render | n/a (local PyMuPDF) | n/a |
| meta-harness optimizer | manual: ablation benches + blind critic | not now; our B0..B5 ablations are the human-in-the-loop version |

Caveats: the paper's own evaluator correlates weakly with humans (r = 0.34), so harness gains measured by PosterBench are not proof of taste; it validates posters only. We copy *mechanisms*, not scores.
