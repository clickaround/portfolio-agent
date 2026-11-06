# Blind 3-way: B0 vs B4 (scene v0.1) vs B4 (scene v0.2 typography) - 2026-11-04
Question: does adding typography tokens (scene v0.2) close the B4-vs-B0 gap? Same project (arch_01), same host, same rubric. n=1 per condition, one LLM critic, synthetic assets/filler text.
Labels randomised (key in .cache/_unblind_key3.json): X=B4 v1, Y=B0, Z=B4 v2.

| condition | blind mean | verdict | cost | gates |
|---|---|---|---|---|
| B0 host direct (re-scored, was 0.76) | 0.71 | revise | $0.39 (earlier run) | none |
| B4 v1 (scene 0.1.0) | 0.39 | fail | $0.41 | pass, 0 repairs |
| B4 v2 (scene 0.2.0 style tokens) | 0.57 | revise | $0.33, 12 turns, 86 s | pass first try, 0 issues |

Result: typography tokens lifted B4 by +0.18 (fail -> revise). Gap to B0 remains 0.14. HYPOTHESIS "typography vocabulary was the main limit" is PARTLY supported (REPRODUCED once, n=1), not closed.
B0 changed 0.76 -> 0.71 between two critic sessions with the same PDF: critic noise is about 0.05, so differences below that mean nothing.
Remaining B4 v2 weaknesses (critic): fragmented page 2 composition, heading/caption contradiction on page 3, under-scaled captions, repeated title-rule-text pattern. Those are composition, not vocabulary: the host places boxes by hand.
Invalid run: first B4 v2 attempt wrote 0 pages because the host tried a generator script outside the tool allow-list; excluded and logged (evidence/logs/b4v2-invalid-run1.json).
Not shown: Codex host, more projects, more runs, human review, real cases (cases/approved is empty; NO_EXTERNAL_REFERENCE).
Artifacts: evidence/logs/b4v2-*, blind3b-b0-b4v1-b4v2.txt, benchmarks/reports/b0-b4v1-b4v2-arch01-20261104.json.
