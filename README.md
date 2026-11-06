# Workspace map

Four product folders. Start here, then open the one you need.

| folder | what it is | who touches it |
|---|---|---|
| `agents/` | **One folder per agent.** `portfolio-agents/` = the Claude/Codex plugin hub: `sourcePrepAgent/` (sources -> clean assets), `portfolioAgent/` (the book: plan -> layout -> gates -> export), `reviewAgent/` (fresh review, blind runs, benchmarks), plus `skills/`, `.claude-plugin/`, `scripts/portfolio.py`. `pascal-agents/` = the owner's other hub (`pptAgent`, `DiagramAgent`, `drawingbookAgent`; own nested repo). | agent owners |
| `backend/` | Code and contracts shared by every agent: `common/` (`portfolio_agent.core`, JSON `contracts/`, `checks/`, layer rules + architecture test). Later: HTTP wrapper over the agents' CLIs. | everyone (careful: breaks all agents) |
| `frontend/` | The portfolio editor (later). Talks to `backend/` only. | UI owners |
| `project/` | Governance, not code: mission (`AGENTS.md`), goals/plans, `docs/`, `architecture/` (ADRs), `tasks/` (DAG), `research/` (pinned repos, REUSE_MAP, paper notes), `evidence/` (what was run and seen), `memory/NOW.md` (handoff), `cases/` rights protocol, task/package tooling + tests, `PATH_MAP.md`. | everyone |

Also: `.cache/` (ignored: vendor clones, signed binaries, blind keys), `_bmad*` (planning tool output, ignored).

## Data that is NOT in the repo (by design)
| path | content |
|---|---|
| `C:/DK/real_sources/<project>/` | a person's project folder: `images/ drawings/ diagrams/ project.md` (+ `sources/` originals, `derived.json` transform log) |
| `C:/DK/real_sources/cases_private/` | third-party example portfolios (PDF): reference only, never copied or redistributed |
| `C:/DK/portfolio_gallery/` | rendered contact sheets for looking at results |

A teammate needs only `agents/portfolio-agents/portfolioAgent/examples/` (synthetic fixtures) to run and test everything.

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
cd agents/portfolio-agents
python scripts/portfolio.py compose <project> <book-plan.json> <out> --width-mm 297 --height-mm 210 --bleed-mm 3
python -m pytest ../../backend/common/tests portfolioAgent/tests sourcePrepAgent/tests reviewAgent/tests -q
cd ../../project && python -m pytest tests -q && python scripts/validate_package.py
```
Contributing rules and ownership: `project/CONTRIBUTING.md`. Where things live: `project/docs/STRUCTURE.md`. Old paths -> new: `project/PATH_MAP.md`.
