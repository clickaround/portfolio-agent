# portfolioAgent Guardrail Enforcement

Which guardrail is checked by code, and where. Rule numbers refer to `GUARDRAILS.md`. The rows were read from the code, not proven by running a violation.

| rule | enforced by |
|---|---|
| 2 grounding in manifest | portfolio-core `core/guardrails/grounding.py` |
| 5 blocking gates | portfolio-core `core/guardrails/gates.py`, `policy.py`, `repair.py` (ADR-0009) |
| 7 layers | `backend/packages/portfolio-core/tests/test_architecture.py`, import-linter |
| 6 edit changes its target only | `src/portfolio_agent/engine/edit.py` (pixels outside the target unchanged, other pages byte-identical) |
| 4 bleed and margins | bleed/margin extent in `core/guardrails/gates.py`; that every layout STATES medium and units is prose only |
| 3 no write into `sources/` | `hooks/scripts/guard.sh` -> `guard.py` + `hooks/guard.json` (gitagent `pre_tool_use`; runs only under a gitagent runtime; a shell command is matched by pattern, so it can be evaded) |
| 1, 8 | prose only |
