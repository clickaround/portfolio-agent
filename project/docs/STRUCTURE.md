# Repository structure (2026-11-06, agents / backend / frontend split)

```
.git  README.md AGENTS.md CLAUDE.md SPLIT_PLAN.md
agents/                            ONE FOLDER PER AGENT
  portfolioAgent/    src/portfolio_agent/{layout,authors,cli.py,engine/{pipeline,catalogue,grid,guides,spec,candidates,edit,ingest_view,registry}.py}
                     backends/{local,designcraft,...}  knowledge/{patterns,editorial,domains}  examples/  tests/  AGENTS.md
  sourcePrepAgent/   src/portfolio_agent/engine/{prepare,levels,cutout}.py  tests/  AGENTS.md
  reviewAgent/       src/portfolio_agent/engine/review.py  knowledge/critic-rubric.md  benchmarks/  tests/  AGENTS.md
  pascal-agents/     pptAgent, DiagramAgent (+ diagram-design skill copy), drawingbookAgent (own nested repo, ignored here)
  portfolio-plugin/  plugin shell only: .claude-plugin .codex-plugin .agents/plugins plugin.json skills/ scripts/portfolio.py
backend/
  common/            src/portfolio_agent/core (geometry, assets, guardrails ...), src/pascal_bootstrap.py, contracts/, checks/, tests/
  api/               FastAPI service over the agents (jobs, projects, runs, review)
frontend/            README only (editor later)
project/             AGENTS GOALS PLANS CONTRIBUTING PATH_MAP docs architecture tasks research evidence memory cases formats integrations agent-roles scripts tests
.cache/              ignored: vendor clones, signed binaries (.cache/bin), blind keys
```
`portfolio_agent` is one import name over several source roots (PEP 420). `pascal_bootstrap.setup()` puts them all on `sys.path`; `agents/portfolio-plugin/scripts/portfolio.py` and every `conftest.py` call it.

| I want to add... | put it in | also |
|---|---|---|
| a page arrangement | `portfolioAgent/knowledge/patterns/*.json` | `catalogue` sheet + test |
| a new page device (like bleed) | `portfolioAgent/src/portfolio_agent/layout/<device>.py` | gate rule, schema field, skill paragraph, test |
| a source transform | `sourcePrepAgent/src/portfolio_agent/engine/<transform>.py` | `derived.json` record, CLI flag, test that the original is untouched |
| a guardrail | `backend/common/src/portfolio_agent/core/guardrails/` | policy code + falsifying test |
| a diagram producer | `agents/pascal-agents/DiagramAgent` | `diagram-set/v1` output |
| an export format | `portfolioAgent/backends/<name>/adapter.py` | capability declaration |
| a review/benchmark | `reviewAgent/benchmarks/`, `reports/<run>.json` | blind key in `.cache` |
| a whole new agent | `agents/<name>Agent/` with `AGENTS.md`, `src/`, `tests/` | import only `core`; add it to `pascal_bootstrap.SOURCE_ROOTS` and the architecture test |

Old paths: `project/PATH_MAP.md`.
