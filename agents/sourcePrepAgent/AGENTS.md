# sourcePrepAgent — people's sources, made ready

Turns what people hand over (scanned sheets with borders, photos with busy backgrounds, scan paper that should be transparent) into clean assets. **Source bytes are never modified**: the original stays in `sources/`, the working copy replaces it, every step is a record in `derived.json` (engine, hashes, parameters) so `core/assets.py` shows it as `source_transform`.

- Code: `src/portfolio_agent/engine/{prepare.py (trim proposals + approval), levels.py (percentile levels, paper->alpha knockout), cutout.py (rembg MIT default, photocraft Apache via signed binary in .cache/bin)}`.
- CLI: `python scripts/portfolio.py prepare <project> [--approve] [--levels] [--knockout]`, `cutout <project> --files a.jpg,b.jpg [--engine rembg|photocraft] [--sheet out.png]`. The host LLM chooses WHICH photos get a cut-out (skills/portfolio-cutout).
- Depends on `backend/common` (core) only; enforced by `backend/common/tests/test_architecture.py`.
- Tests: `tests/` (cut-out needs rembg + cached u2net model; skipped otherwise).
