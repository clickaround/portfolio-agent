# Independent critic, round 1 (2026-11-04) — arch_01, 3 candidates A/B/C (synthetic assets)
Method: fresh `claude -p` session (Read-only, no knowledge of generator settings or unblind key) applied knowledge/editorial/critic-rubric.md to cand_A/B/C sheets. Raw log: evidence/logs/critic-round1.txt. Single LLM critic = weak evidence, not a designer review.
Result: mean scores A 0.44, B 0.46, C 0.47; verdict `revise` for all (none >= 0.75, several `high` issues). Ranking C > B > A, low confidence.
Shared defects named by the critic (to fix, then re-run a NEW fresh critic):
1. p2: second image is a tiny faded thumbnail stranded bottom-left (tree solver gives the 2nd image too little area).
2. Captions become 3-5 line slivers in a corner (caption cell shape/size).
3. p4 (single image): big empty right/lower area; p3 and p4 share the same image+caption pattern (rhythm).
4. Cover: title/"Portfolio" subtitle weak, empty lower-right void.
5. Closing page nearly empty.
Status: layout NOT acceptable. Gate pass (hard gates) != design quality.
