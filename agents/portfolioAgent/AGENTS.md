# portfolioAgent — the book

Guide for people and coding agents working in this folder. Identity: `SOUL.md` (C1). Guardrails: `guardrails/GUARDRAILS.md` (C2). Harness² manifest: `harness.yaml`. `RULES.md` is generated from the guardrails and the tool guidance; never edit it. Layout follows `../baseAgent/MODULE.md` (gitagent + Harness²).

- Code: `src/portfolio_agent/{layout, authors, cli.py, engine/{pipeline,catalogue,grid,guides,spec,candidates,edit,ingest_view,registry}.py}`; exporters `backends/{local,designcraft}`.
- Data (not code): `knowledge/patterns/` (grid systems, compositions, pascal boards, photosets), `knowledge/editorial/` (craft rules, grammar), `knowledge/domains/`.
- Contract in: `../../backend/packages/portfolio-core/src/portfolio_agent/core/schemas/book-plan.schema.json`. Out: `attempts/NN/{book.pdf,book.pptx,preview,scenes,qa.json,episode.json}`.
- Tools: `tools/` declares the CLI commands; `tools/TOOL_GUIDANCE.md` says when to use which.
- Tests: `tests/` (`uv run pytest agents/portfolioAgent/tests`); fixtures `examples/synthetic_projects/`.
- Rules: layers `core <- layout <- authors/*, backends/* <- engine <- cli` (`../../backend/packages/portfolio-core/tests/test_architecture.py`); new page device = `layout/<device>.py` + gate rule + schema field + test; arrangements are JSON.
