# T1001 evidence — judge step and preference record (REPRODUCED)

- Date 2026-11-15. Working tree on `wip-backup-20261114`, not committed at the time of writing.
- Files: `agents/portfolioAgent/src/portfolio_agent/engine/live.py` (`edit(..., instruction=)`, `judge_context`, `verdict`, `undo(by=)`,
  `_empty_band`), `src/portfolio_agent/cli.py` (`live OUT edit --instruction`, `judge`, `verdict SCORE --notes`), `tests/test_live.py`.
- Command (from `agents/portfolioAgent`): `python -m pytest -q` -> 78 passed, 7 subtests passed, 187 s; `tests/test_live.py` 9 passed.
  ruff: all checks passed. import-linter: 3 kept, 0 broken. The other folders' tests were not re-run.
- Record: every attempt in `<out>/live/state.json` history carries `at`, `instruction`, `marked`, `ops`, `results`, `changed`,
  `accepted`, `reason` / `critique`, `judge {score, notes}`, `undone_by` (user | judge).
- Real replay: the 2026-11-14 edit ("이 사진 위 빈 공간이 너무 휑해. 사진을 위로 키우고 본문도 좀 크게 해줘.") judged by a fresh
  `claude -p --model sonnet`. Empty band before `[79.2, 9.6]` mm, after `[177.2, 20.8]` mm. Judge: score 3, "photo was only shifted up
  20.8mm and not enlarged ... a 20.8mm empty band now sits below it". Below 4, so the edit would be taken back.
- Limit seen: the judge's proposed fix (taller picture) cannot be made with the current ops (full width, aspect kept). See T1007.
- Not covered: the loop that runs edit -> judge -> retry by itself (T1006).
