# P10 — page DSL v2 and the gates as one reward (T1016), 2026-11-16

Status: REPRODUCED for what is listed under "Run"; the soft terms are HYPOTHESIS. No model was trained or scored with this yet.

## What exists
- `research/p10_train/page_dsl.py` (sha256 5af5e2a797d39501...): problem lines (kind + aspect ratio, or type size + characters), layout lines `<id> x y w` + `end`, strict parser, decode (picture height from aspect ratio, text height from the product measurer), mirror, layout hash (BLAKE2b, 128 bit).
- `research/p10_train/reward.py` (sha256 ac6d33ce7dcf771f...): hard = geometric mean of margin and overlap; soft = mean of caption distance, tallest empty band, shared left edges; total = hard * (1 + soft) / 2; unparseable = 0; `passed` = no blocking gate from `core/guardrails/gates.qa_scene`.

## Run (Windows 11, repo .venv, exit 0)
`.venv/Scripts/python.exe project/research/p10_train/page_dsl.py .cache/bench/<book>/<format>/B3_full` on the 9 bench runs (3 books x 3 formats, 40 pages):
- 38 of 40 pages keep their gates after scene -> DSL -> scene at a 1 mm grid. The 2 that do not: a box snapped across the margin (arch_01 A4-landscape page-03, OUTSIDE_MARGIN) and one in arch_02 A4-landscape (not looked at).
- At a 3 mm grid, arch_01 A4-landscape page-05 breaks: two caption rows 5.2 mm apart snap onto each other (BBOX_OVERLAP). So the default is 1 mm, and the design's "grid units" idea is not adopted as written.
- Size: 107 to 341 characters per page for problem + layout together.

Reward on the same 40 pages (scratch script, not kept):
- as laid out: mean 0.866, min 0.743; 38 pass.
- everything stacked in one column at the margin: mean 0.007, max 0.098; lower than the real layout on 40 of 40.
- a truncated answer (`0 1 1` + `end`): 0.

## Limits
- All 40 pages come from our own rule engine. They test the code, not taste, and are not training data.
- The reward was not checked against pages a person judged. A page can score high and look poor.
- Not in the format: type step, crop, layer order. Pages with furniture that overlaps content on purpose were not tried.
- No unit tests in the repo test suite yet; the checks above are the two CLIs.
- Samples that fail the round trip are to be dropped when a training set is built; that filter is not written.

## Set C first run (2026-11-16, later) — `research/p10_train/gen_c.py`
Teacher: `claude -p --model sonnet`, one call per page, text only (problem lines + first words of each text; the engine's layout is not shown).
- First run, 5 pages: 4 dropped for BBOX_OVERLAP while the reward said overlap 1.0. Cause: the teacher did not know the running header exists and the reward did not count it. Fixed: `fixed x y w h` lines in the problem, furniture counted in the overlap term.
- Second run, 13 pages (arch_01 A4-landscape, arch_02 A4-portrait, arch_03 square): 13 of 13 parse, pass every blocking gate and are kept at total >= 0.8. Teacher mean 0.936, engine mean 0.866 on the same pages (scores from the run output).
- Looked at as wireframes (`.cache/p10_setc/sheet.png`, six pages, boxes only, not rendered pages): the teacher's pages are valid but plain. Title on top, one picture under it, caption under the picture, nearly the same on every page; on portrait pages the lower third stays empty, as in the engine's layout. A score of 1.0 went to such a page.
What this shows: the reward separates broken from not broken and nothing more; one text-only call per page gives layouts with little variety, so 2,000 of them would teach one layout. Before volume: several candidates per page with different stated intents, the teacher seeing the pictures, and the judge on rendered pages.
Not done: judge step, rendering of teacher layouts, the 100-sample look, unit tests.
