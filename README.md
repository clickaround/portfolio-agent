# Workspace map

Product folders. Start here, then open the one you need.

| folder | what it is | who touches it |
|---|---|---|
| `agents/` | **One folder per agent**: `portfolioAgent/` (the book: plan -> layout -> gates -> export), `sourcePrepAgent/` (sources -> clean assets), `reviewAgent/` (fresh review, blind runs, benchmarks), `pascal-agents/` (the owner's other hub: `pptAgent`, `DiagramAgent`, `drawingbookAgent`; own nested repo), and `portfolio-plugin/` (plugin shell: `.claude-plugin`, `skills/`, `scripts/portfolio.py`). Each agent folder follows `agents/baseAgent/` (gitagent + Harness² C1..C8: `agent.yaml`, `harness.yaml`, `SOUL.md`, `guardrails/`, `memory/`, `tools/`, `agents/`, `skills/`, `scripts/`, `hooks/`); check with `python agents/baseAgent/scripts/check_base.py agents/<agent>`. | agent owners |
| `backend/` | `packages/portfolio-core/` = code and contracts shared by every agent (`portfolio_agent.core`: model, sources, quality, guardrails, checks, schemas; layer rules + architecture test); `apps/api/` = FastAPI service over the agents. | everyone (careful: breaks all agents) |
| `frontend/` | The portfolio workbench: React Router 8 (framework mode, SPA) + Vite 8 + Tailwind 4 + shadcn, structure `app/{common,features,lib}` (owner's convention). Talks to `backend/apps/api` only. `npm run dev`; scope + conventions in `frontend/README.md`. | UI owners |
| `editor/` | Our editable DesignCraft-derived Rust source and WebAssembly editor build. See `editor/README.md` for attribution, integration scope and build instructions. | editor owners |
| `supabase/` | Conversation data layer (in progress): SQL drafts under `drafts/`, local RLS checks under `tests/`. Not applied to any cloud project; see `supabase/README.md`. | backend owners |
| `project/` | Governance, not code: mission (`AGENTS.md`), goals/plans, `docs/`, `architecture/` (ADRs), `tasks/` (DAG), `research/` (pinned repos, REUSE_MAP, paper notes), `evidence/` (what was run and seen), `memory/NOW.md` (handoff), `cases/` rights protocol, task/package tooling + tests, `PATH_MAP.md`. | everyone |

Also: `.cache/` (ignored: vendor clones, signed binaries, blind keys), `_bmad*` (planning tool output, ignored).

The frontend depends on the private `@dk/dui` GitHub repository. Fresh installs and CI require Git credentials authorized to read `akfldk1028/dui`; this public repository alone does not provide that package.

`agents/pascal-agents/` is a separate, optional repository and is not present in a fresh clone. See [pinned setup and verification](project/docs/PASCAL_AGENTS_SETUP.md); an existing checkout and its changes are never reset by this project.

The Book page uses our DesignCraft-derived editor built from source; see [editor build instructions](editor/README.md). Select DesignCraft when composing, then use **웹 편집기 열기** on an attempt to open its full-screen workspace; the selected file is sent after the editor loads. The right-hand Claude panel can discuss the selected attempt's saved PDF text and propose text for insertion. It cannot see unsaved edits, images, or layout. Save and import the downloaded file into a new attempt; the page also offers a best-effort automatic save capture. Its fonts and crop behavior can differ, so inspect the exporter notes and review the actual result.

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
