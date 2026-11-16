# T1000 evidence — live editing, first slice (REPRODUCED)

- Date 2026-11-14. Commit `b7bef10` "Edit the DesignCraft document during a conversation", branch `wip-backup-20261114`, not pushed.
- Files: `agents/portfolioAgent/backends/designcraft/adapter.py` (objects named `<page_id>/<element_id>`), `backends/designcraft/live.py`
  (read-back, nine typed ops), `src/portfolio_agent/engine/live.py` (context, edit, sync, undo), `src/portfolio_agent/cli.py` (`live`),
  `tests/test_live.py`.
- Backend: DesignCraft 0.17.0 headless CLI under `.cache/bin/designcraft` (MIT / Apache-2.0). Windows 11.
- Command: `.venv/Scripts/python.exe -m pytest agents/portfolioAgent/tests/test_live.py -q` -> 7 passed (9 after T1001). ruff clean,
  import-linter 3 contracts kept.
- Observed: an op changes only its target; a move outside the margin is refused with `OUTSIDE_MARGIN`; one bad op does not cancel the
  good one; a file saved by the user is taken in and its elements are protected; text that stops fitting is refused; a picture keeps its
  aspect ratio; undo returns the previous step. One edit about 0.5 s.
- One real run with `claude -p --model sonnet` (18 s): three valid ops, gates passed, page not better. That gap is T1001.
- Not covered: the editor open in the browser (T1003, T1004), crop and new elements (T1007).
