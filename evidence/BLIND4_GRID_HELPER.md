# Blind 3-way: B0 vs B4 v2 vs B4 v3 (grid helper) - 2026-11-04
Question: does the `grid` helper (12 columns + aspect-exact boxes) fix B4's composition problems? n=1, synthetic, one LLM critic. Key in .cache/_unblind_key4.json: X=B0, Y=B4 v3, Z=B4 v2.

| condition | blind mean | verdict |
|---|---|---|
| B0 host direct | 0.75 | revise |
| B4 v2 (typography tokens) | 0.64 | revise |
| B4 v3 (typography + grid helper) | 0.53 | fail |

Result: grid helper did NOT help (0.53 vs 0.64; B4 v2 was 0.57 in the previous critic session, so critic noise is about +-0.07; v3 is at best equal to v2). Hypothesis "hand arithmetic causes the composition problems" is NOT supported.
B0 across three critic sessions: 0.76, 0.71, 0.75 (stable ~0.74). B4 v2 across two: 0.57, 0.64. Gap to B0 ~0.1-0.18 persists.
Critic on v3: unbalanced cover (title far from label), mismatched image sizes/misalignment on p2, orphaned captions, mixed fonts (Georgia italic + sans + CJK sans), no running system.
Observation (HYPOTHESIS): in B4 the host never SEES the rendered page; it only reads gate codes. Gates catch geometry/provenance errors, not visual imbalance. B0 may have the same blindness, so this is untested. Next experiment: give the host PNG previews of its own render and a critique-and-fix loop (B5-style).
Artifacts: evidence/logs/b4v3-*, blind4-b0-b4v2-b4v3.txt, benchmarks/reports/b0-b4v2-b4v3-arch01-20261104.json.
