# Blind 3-way comparison: B0 vs B4 vs rule-based engine (2026-11-04) - n=1, synthetic, one LLM critic
Same project (arch_01), A4 landscape. Labels randomised (X=B0, Y=B4, Z=engine; key in .cache, revealed after scoring).
- B0 host direct (Python/PDF, no repo): $0.392, 17 turns, 82 s. Blind mean 0.76 (`revise`).
- B4 host-authored scenes + our gates/export (check-scenes): $0.413, 25 turns, 115 s; engine reported gate_pass true, 0 issues, 4 pages, no repair needed. Blind mean 0.39 (`fail`).
- Rule-based engine (cand_C): $0, ~4 s. Blind mean 0.45 (`revise`).
Ranking by critic: B0 > engine > B4. Raw: evidence/logs/blind3-b0-b4-engine.txt. B4 artifacts: evidence/logs/b4-arch01-book.pdf, b4-scenes/, b4-design-plan.json, b4-prompt.txt.
Critic on B4: default bold sans + tiny body, no running header, same image-left/text-right pattern on every page, big empty areas, placeholder text (fixture artifact, told to ignore).
Interpretation: gate-passing != good design. B4 was safe and clean but plain. Likely cause (HYPOTHESIS, untested): our scene model/backends are typographically poor - one font family (regular/bold only), single text colour, no italic, no per-element font/colour/alignment, no tints/rules beyond a rectangle - so the host cannot express what B0 did with free Python (serif display, italic, accent labels, panels). B0 also had no gate or editability: one-shot PDF.
Hypotheses NOT supported: "host-authored + engine gates beats B0 on aesthetics". Supported only: B4 passes our hard gates with no repair on the first run (n=1) and yields editable scene JSON + PPTX/DesignCraft export; B0 has none of that.
Limits: 1 project, 1 run per condition (LLM variance unknown), 1 critic (possible serif/editorial bias), synthetic images and filler text, B4 prompt told the host to use generous boxes and plain constraints, Codex host not run, no human review.
