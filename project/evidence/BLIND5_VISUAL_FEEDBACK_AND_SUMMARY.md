# Blind 3-way: B0 vs B4 v2 vs B4 v4 (visual feedback loop) + summary of all B4 variants - 2026-11-04
Key (.cache/_unblind_key5.json): X=B4 v4, Y=B0, Z=B4 v2. n=1 project, synthetic assets, ONE LLM critic.
| condition | blind mean | verdict |
|---|---|---|
| B0 host direct | 0.74 | revise |
| B4 v2 (typography tokens) | 0.60 | revise |
| B4 v4 (v2 + host reads PNG previews, 2-3 self-critique rounds) | 0.50 | revise |

Result: visual feedback did NOT help (0.50 vs 0.60; within ~+-0.07 critic noise it is at best equal). Hypothesis "host blindness to its own render" is NOT supported. Caveat: log does not prove the host opened the previews.

## All host-authored (B4) variants vs B0 (blind critic means, each session scores 3 candidates)
- B0: 0.76, 0.71, 0.75, 0.74 (stable ~0.74)
- B4 v1 (scene 0.1.0): 0.39 fail
- B4 v2 (+ typography tokens): 0.57, 0.64, 0.60  -> only change that helped (+~0.2 over v1)
- B4 v3 (+ grid helper): 0.53 fail
- B4 v4 (+ visual loop): 0.50
Conclusion (n=1 project, one critic): the claim "host-authored scenes + our engine beat a plain host on aesthetics" is NOT supported; B4 plateaus ~0.5-0.6 vs B0 ~0.74. Typography vocabulary mattered; grid and visual feedback did not. The engine's demonstrated value is hard gates (0 issues first try), editable output (scene JSON, PPTX, DesignCraft), provenance/rights tags and local-edit proof - not better taste. Cost per B4 run $0.32-0.45 vs B0 $0.39.
Possible remaining causes (HYPOTHESES, untested): B0 plans the whole book in one script (running header, section numbering, warm ground) while B4 writes pages as separate JSON; B0 may use richer fonts/colours freely; critic may prefer serif editorial look.

## Non-architecture mechanical check (same day)
ux_01 / brand_01 / photo_01 synthetic fixtures pass the same hard gates with domain-specific patterns (ux-flow, brand-system, photo-series), no domain code (tests/test_domains.py). Looking at the PDFs (C:/DK/dom_*_sheet.png): they are weak - large empty areas, a near-empty closing "Credits & Notes" page, photo p3 half empty, UI screens placed without narrative. Gates pass; design quality is NOT demonstrated.
