# ADR-0009: Harness guardrails (blocking/advisory gates, immutable attempts, fresh-review gate)

Status: ACCEPTED 2026-11-05. Source: research/PAPER_NOTES_AUTODESIGN_HARNESS.md (AutoDesign, arXiv 2608.13560; code-inspected skill).

## Decision
1. **Gates are split.** G1-G5 of benchmarks/SPEC.md are *blocking* (`core/gates.BLOCKING`); composition diagnostics (REPEATED_LAYOUT, HERO_TOO_SMALL) and the lexical grounding check (TEXT_UNGROUNDED) are *advisory*: always reported in `qa.json` and the attempts ledger, never a reason to refuse export, never silently dropped. Unknown codes fail closed. New blocking gate: TYPE_TOO_SMALL (body/title < 8 pt, other text < 6.5 pt).
2. **Attempts are immutable and numbered.** Every run into the same `out/` appends `attempts/NN/` (scenes, plan, qa, previews, pdf) and a `ledger.jsonl` line with the plan hash and gate outcome. Nothing in an attempt is rewritten.
3. **The engine never judges taste; a fresh reviewer does, and it is bound.** `review-context` hashes frames + scenes + rubric; `record-review` refuses a review that is self-authored (`reviewer_mode` not fresh), bound to another context, missing frames, or whose verdict contradicts the rule (zero blockers and mean >= 0.75 over the 8 rubric dimensions). `finalize` promotes the latest attempt to `final/` only with blocking gates passed AND a passing fresh review.
4. **Bounded repair stays, as a logged exception** to "scripts never edit the artifact": `core/repair.py` only shrinks fonts to the floor and nudges boxes inside margins; every touch is logged in `qa.json.repairs`. Semantic repairs (sequence, asset choice, words) are the author's job on a new attempt.

## Consequences
- `gate_pass` now means "no blocking issue"; a naive layout can pass gates and still carry advisories (tests/test_harness.py). Benchmarks must report blocking and advisory separately.
- Hosts (skills) must run review-context -> fresh subagent -> record-review -> finalize before calling a portfolio done.
- Not adopted: the meta-harness optimizer (our ablations are the manual loop); network-denied rendering (local compositor).
