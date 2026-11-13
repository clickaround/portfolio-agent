# sourcePrepAgent — people's sources, made ready

Guide for people and coding agents working in this folder. Identity: `SOUL.md` (C1). Guardrails: `guardrails/GUARDRAILS.md` (C2). Harness² manifest: `harness.yaml`. `RULES.md` is generated from the guardrails and the tool guidance; never edit it. Layout follows `../baseAgent/MODULE.md` (gitagent + Harness²).

- Code: `src/portfolio_agent/engine/{prepare.py (trim proposals + approval), levels.py (percentile levels, paper->alpha knockout), cutout.py (rembg MIT default, photocraft Apache via signed binary in .cache/bin)}`.
- CLI: `python scripts/portfolio.py prepare <project> [--approve] [--levels] [--knockout]`, `cutout <project> --files a.jpg,b.jpg [--engine rembg|photocraft] [--sheet out.png]` (declared in `tools/`). The host LLM chooses WHICH photos get a cut-out (skills/portfolio-cutout).
- Depends on `backend/packages/portfolio-core` (core) only; enforced by `backend/packages/portfolio-core/tests/test_architecture.py`.
- Tests: `tests/` (cut-out needs rembg + cached u2net model; skipped otherwise).
