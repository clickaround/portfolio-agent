# Codex / Claude task runner (low-context, fast, evidence-based)

## Fast path
1. `python scripts/validate_package.py`, `python -m unittest discover -s tests -v`, `python scripts/task_status.py --ready`.
2. Read `AGENTS.md`, `memory/NOW.md`, `tasks/cards/<id>.md`. Do **not** load 100 files.
3. For each ready task: identify permitted paths and exact validation before editing. Execute one bounded task, write evidence, independent review.
4. When task is truly done, set `status=done`, `pass_state=PASS`, `finished_at` ISO UTC, `evidence_path` file. Run validation again.
5. If missing rights/models/network: `status=blocked`, with reason in evidence. Work on another ready task. Do not invent pass or blindly wait.
6. Only integration owner edits `memory/NOW.md`, `memory/HANDOFF.md`, `docs/adr`, `tasks/backlog.json`. Other agents write to task-owned evidence path.

## State transition
`pending → in_progress → done | blocked | skipped`.
- `done` requires existing proof plus expected validation; record measured checks, not just narrative.
- `blocked` means permission/input/dependency missing; evidence says exactly what was attempted and why, can retry.
- `skipped` requires approved waiver, explicit downstream impact; not counted as completed dependency unless a separate alternative gate is accepted.
- A failed backend experiment is **valuable evidence** but not the same as a successfully integrated backend. Record a `NO_GO` ADR and test the fallback.

## Working in parallel
- Start domain/case and source-code audits as separate read-only/subagent tasks after P00.
- Branch/worktree per independent task; do not edit shared memory concurrently.
- Root integration owner reviews and merges only proven diffs.
- No background promises. End each session with evidence paths and next task.

## Approval policy (speed without unsafe side effects)
No need for confirmation on routine local read-only analysis or test code changes inside approved workspace. Ask before buying model credits, copying copyrighted portfolios, uploading private projects, changing account/cloud infrastructure, installing large dependencies outside an isolated directory, or publishing/releasing.

## Handoff example
```
TASK: T302
STATUS: BLOCKED (not PASS)
COMMAND: python scripts/check_layout.py examples/SYNTHETIC_scene_invalid.json
EXIT: 1 (EXPECTED)
EVIDENCE: evidence/T302-geometry-2026-11-04.md
NEXT: T300 / T303 ready (independent)
```
