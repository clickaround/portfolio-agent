# Workspace map

Four product folders. Start here, then open the one you need.

| folder | what it is | who touches it |
|---|---|---|
| `agents/` | **One folder per agent**: `portfolioAgent/` (the book: plan -> layout -> gates -> export), `sourcePrepAgent/` (sources -> clean assets), `reviewAgent/` (fresh review, blind runs, benchmarks), `pascal-agents/` (the owner's other hub: `pptAgent`, `DiagramAgent`, `drawingbookAgent`; own nested repo), and `portfolio-plugin/` (plugin shell: `.claude-plugin`, `skills/`, `scripts/portfolio.py`). | agent owners |
| `backend/` | `packages/portfolio-core/` = code and contracts shared by every agent (`portfolio_agent.core`: model, sources, quality, guardrails, checks, schemas; layer rules + architecture test); `apps/api/` = FastAPI service over the agents. | everyone (careful: breaks all agents) |
| `frontend/` | The portfolio workbench: React Router 8 (framework mode, SPA) + Vite 8 + Tailwind 4 + shadcn, structure `app/{common,features,lib}` (owner's convention). Talks to `backend/apps/api` only. `npm run dev`; scope + conventions in `frontend/README.md`. | UI owners |
| `project/` | Governance, not code: mission (`AGENTS.md`), goals/plans, `docs/`, `architecture/` (ADRs), `tasks/` (DAG), `research/` (pinned repos, REUSE_MAP, paper notes), `evidence/` (what was run and seen), `memory/NOW.md` (handoff), `cases/` rights protocol, task/package tooling + tests, `PATH_MAP.md`. | everyone |

Also: `.cache/` (ignored: vendor clones, signed binaries, blind keys), `_bmad*` (planning tool output, ignored).

`agents/pascal-agents/` is a separate, optional repository and is not present in a fresh clone. See [pinned setup and verification](project/docs/PASCAL_AGENTS_SETUP.md); an existing checkout and its changes are never reset by this project.

For the original DesignCraft web editor inside the Book page, run `python project/scripts/install_designcraft_web.py` before starting or building the frontend. The installer verifies the official v0.17.0 archive and keeps it out of Git. See [installation and limits](project/docs/DESIGNCRAFT_WEB_INSTALL.md). Select DesignCraft when composing, open the web editor, then send an attempt into it. The web editor downloads saved files; it does not yet sync changes back into the portfolio project. Its fonts and crop behavior can differ, so inspect the exporter notes and review the actual result.

## Data that is NOT in the repo (by design)
| path | content |
|---|---|
| `C:/DK/real_sources/<project>/` | a person's project folder: `images/ drawings/ diagrams/ project.md` (+ `sources/` originals, `derived.json` transform log) |
| `C:/DK/real_sources/cases_private/` | third-party example portfolios (PDF): reference only, never copied or redistributed |
| `C:/DK/portfolio_gallery/` | rendered contact sheets for looking at results |

A teammate needs only `agents/portfolioAgent/examples/` (synthetic fixtures) to run and test everything.

## Data flow
```
person's sources -> sourcePrepAgent  prepare / levels / knockout / cutout     (original kept in sources/, every step in derived.json)
                      |-- diagrams <- agents/pascal-agents/DiagramAgent        (diagram-set/v1: concept via diagram-design, overlays via engine)
                      |-- palette  <- agents/pascal-agents/pptAgent            (DESIGN.md / tokens.json)
                      v
          host LLM writes book-plan.json (never coordinates)
                      v
          portfolioAgent  compose -> layout -> gates -> PDF/PPTX/PNG (+ DesignCraft)
                      v
          reviewAgent  review-context -> fresh reviewer -> record-review -> finalize -> final/
```

## Run
```
uv sync                                   # once, at this folder (installs the core + agents + api editable, one .venv, one uv.lock)
uv run portfolio compose <project> <book-plan.json> <out> --width-mm 297 --height-mm 210 --bleed-mm 3
uv run pytest                             # every Python suite (core, api, 3 agents; ~6 min)  |  uv run lint-imports  |  uv run ruff check .
uv run pascal-api --port 8000             # API + docs at /docs
cd frontend && npm install && npm run dev
cd project && uv run pytest tests -q && uv run python scripts/validate_package.py
```
The Python packages currently depend on this checkout's data directories and are used as editable workspace installs; standalone wheel distribution has not been established. CI covers the tracked workspace, not the optional separate `pascal-agents` checkout or its uncommitted changes.
Contributing rules and ownership: `project/CONTRIBUTING.md`. Where things live: `project/docs/STRUCTURE.md`. Old paths -> new: `project/PATH_MAP.md`.
