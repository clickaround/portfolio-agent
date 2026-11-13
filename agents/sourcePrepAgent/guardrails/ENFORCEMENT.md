# sourcePrepAgent Guardrail Enforcement

Which guardrail is checked by code, and where. Rule numbers refer to `GUARDRAILS.md`. The rows were read from the code, not proven by running a violation.

| rule | enforced by |
|---|---|
| 1, 2 originals kept, transforms recorded | `src/portfolio_agent/engine/prepare.py` (`derived.json`), portfolio-core `core/sources` |
| 1 no write into `sources/` | `hooks/scripts/guard.sh` -> `guard.py` + `hooks/guard.json` (gitagent `pre_tool_use`; runs only under a gitagent runtime; a shell command is matched by pattern, so it can be evaded) |
| 3 approval before writing | `prepare --approve` in `src/portfolio_agent/engine/prepare.py` |
| 4 cut-out only on named files | `cutout --files` is required (`cli.py`) |
| 6 core-only imports | `backend/packages/portfolio-core/tests/test_architecture.py` |
| 5, 7 | prose only |
