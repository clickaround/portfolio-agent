# Repository structure (2026-11-06, agents / backend / frontend split)

```
.git  pyproject.toml (uv workspace root)  uv.lock  README.md AGENTS.md CLAUDE.md SPLIT_PLAN.md
agents/                            ONE FOLDER PER AGENT (each is a workspace member with its own pyproject.toml)
  portfolioAgent/    src/portfolio_agent/{layout,authors,cli.py,engine/{pipeline,catalogue,grid,guides,spec,candidates,edit,ingest_view,registry}.py}
                     backends/{local,designcraft,...}  knowledge/{patterns,editorial,domains}  examples/  tests/  AGENTS.md
  sourcePrepAgent/   src/portfolio_agent/engine/{prepare,levels,cutout}.py  tests/  AGENTS.md
  reviewAgent/       src/portfolio_agent/engine/review.py  knowledge/critic-rubric.md  benchmarks/  tests/  AGENTS.md
  pascal-agents/     pptAgent, DiagramAgent (+ diagram-design skill copy), drawingbookAgent (own nested repo, ignored here)
  portfolio-plugin/  plugin shell only: .claude-plugin .codex-plugin .agents/plugins plugin.json skills/ scripts/portfolio.py
backend/             (see backend/README.md and backend/docs/STRUCTURE_DECISION.md)
  packages/portfolio-core/   shared kernel: src/portfolio_agent/core/{model,sources,quality,guardrails,checks,schemas,geometry.py,workspace.py}, tests/
  apps/api/                  FastAPI: domain packages (projects sources plans books reviews jobs catalog) + gateways/ + storage/
frontend/            React Router 8 (framework mode, SPA) + Vite 8 + Tailwind 4 + shadcn: app/{common,features/<f>/{pages,components},lib}, routes.ts; typed client from backend/apps/api/openapi.json
project/             AGENTS GOALS PLANS CONTRIBUTING PATH_MAP docs architecture tasks research evidence memory cases formats integrations agent-roles scripts tests
.cache/ .venv/       ignored: vendor clones + signed binaries + blind keys; the uv environment
```
`portfolio_agent` is one import name over several packages (PEP 420 namespace): `portfolio-core` provides `portfolio_agent.core`, the agents provide `layout / authors / engine / cli`. `uv sync` installs them all editable; no `sys.path` code anywhere. Layers are enforced by `uv run lint-imports` (root `pyproject.toml`) and `backend/packages/portfolio-core/tests/test_architecture.py`.

| I want to add... | put it in | also |
|---|---|---|
| a page arrangement | `portfolioAgent/knowledge/patterns/*.json` | `catalogue` sheet + test |
| a new page device (like bleed) | `portfolioAgent/src/portfolio_agent/layout/<device>.py` | gate rule, schema field, skill paragraph, test |
| a source transform | `sourcePrepAgent/src/portfolio_agent/engine/<transform>.py` | `derived.json` record, CLI flag, test that the original is untouched |
| a guardrail | `backend/packages/portfolio-core/src/portfolio_agent/core/guardrails/` | policy code + falsifying test |
| a diagram producer | `agents/pascal-agents/DiagramAgent` | `diagram-set/v1` output |
| an export format | `portfolioAgent/backends/<name>/adapter.py` | capability declaration |
| a review/benchmark | `reviewAgent/benchmarks/`, `reports/<run>.json` | blind key in `.cache` |
| a whole new agent | `agents/<name>Agent/` with `AGENTS.md`, `src/`, `tests/` | own `pyproject.toml`, depend on `portfolio-core` (`workspace = true`), list it in the root workspace `members` |

Old paths: `project/PATH_MAP.md`.
