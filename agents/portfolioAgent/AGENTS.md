# portfolioAgent — the book

The host LLM decides editorial things (sequence, roles, assets, words, flags `bleed` `dark` `strip` `photoset` `focus`) in a **book plan**; rules execute: modular grid -> composition -> guardrails -> export. It never writes coordinates.

- Code: `src/portfolio_agent/{layout, authors, cli.py, engine/{pipeline,catalogue,grid,guides,spec,candidates,edit,ingest_view,registry}.py}`; exporters `backends/{local,designcraft}`.
- Data (not code): `knowledge/patterns/` (grid systems, compositions, pascal boards, photosets), `knowledge/editorial/` (craft rules, grammar), `knowledge/domains/`.
- Contract in: `../../backend/packages/portfolio-core/src/portfolio_agent/core/schemas/book-plan.schema.json`. Out: `attempts/NN/{book.pdf,book.pptx,preview,scenes,qa.json,episode.json}`.
- Tests: `tests/` (`uv run pytest agents/portfolioAgent/tests`); fixtures `examples/synthetic_projects/`.
- Rules: layers `core <- layout <- authors/*, backends/* <- engine <- cli` (`../../backend/packages/portfolio-core/tests/test_architecture.py`); new page device = `layout/<device>.py` + gate rule + schema field + test; arrangements are JSON.
