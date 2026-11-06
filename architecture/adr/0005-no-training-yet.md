# ADR: No model fine-tuning until gap proven

**Status:** PROPOSED (not accepted/implemented)

## Decision hypothesis
Why: reference retrieval/rules/constraints may solve early failures. Alternative: train layout/ranking model. Test: B0-B3 ablation; if good candidates misranked, collect preference pairs; if all candidates bad, improve proposal generator.

## Required evidence
Reproduction reports, design benchmark deltas, measured cost, license audit, owner approval.

## Revisit criterion
Change as soon as bounded falsification experiment contradicts the hypothesis.
