# reviewAgent Guardrail Enforcement

Which guardrail is checked by code, and where. Rule numbers refer to `GUARDRAILS.md`. The rows were read from the code, not proven by running a violation.

| rule | enforced by |
|---|---|
| 1 hash-bound review | `src/portfolio_agent/engine/review.py`, `tests/test_review_integrity.py` |
| 3 finalize needs gates and fresh review | `src/portfolio_agent/engine/review.py` |
| 7 core-only imports | `backend/packages/portfolio-core/tests/test_architecture.py` |
| 2 fresh reviewer | partly: `review.py` rejects a `reviewer_mode` outside `fresh_subagent`, `fresh_session`, `human`. The mode is self-declared; nothing proves the reviewer was fresh |
| 3 nothing but `finalize` writes `final/` | `hooks/scripts/guard.sh` -> `guard.py` + `hooks/guard.json` (gitagent `pre_tool_use`; runs only under a gitagent runtime; a shell command is matched by pattern, so it can be evaded) |
| 5 unblind key kept from agents | the same guard in sourcePrepAgent, portfolioAgent and `agents/fresh-reviewer/` blocks any call that names `_unblind_key`; memory contents are not checked |
| 4, 6, 8 | prose only |
