# Split plan: agents / backend / frontend (approved 2026-11-06, DONE)

Owner rule: **one agent = one folder** (like `agents/pascal-agents/pptAgent`). Baseline commit `62e8714` (in `portfolio-agent/.git`) is the rollback point.

## Target
```
.git                                  ONE repo for the workspace (history of portfolio-agent moved up)
agents/
  pascal-agents/                      existing hub (own nested repo): pptAgent, DiagramAgent, drawingbookAgent - untouched
  portfolio-agents/                   NEW hub = the Claude/Codex plugin root (.claude-plugin .codex-plugin skills/ scripts/ AGENTS.md)
    portfolioAgent/   book: layout, authors, pipeline, backends, patterns, craft rules, fixtures, tests
    sourcePrepAgent/  sources: prepare, levels (knockout), cutout (rembg/photocraft), tests
    reviewAgent/      review: fresh-review gate, critic rubric, benchmarks, blind-run reports, tests
backend/
  common/             shared by every agent: portfolio_agent.core (geometry, assets, guardrails), contracts/, legacy checkers, tests
frontend/             editor (later): README only
project/              governance, not code: AGENTS GOALS PLANS docs architecture plans prompts tasks research evidence memory cases formats integrations + task/package tooling + their tests
.cache/               ignored: vendor clones, signed binaries, blind keys
```
Python import name stays `portfolio_agent` (PEP 420 namespace across `backend/common/src` + each agent's `src`), so layering rules and ~90 imports stay valid. Every entry point and test calls one bootstrap (`backend/common/src/pascal_bootstrap.py`) that puts all source roots on `sys.path`.

## Steps (tests green after each)
1. Move `.git` to the workspace root; flatten `portfolio-agent/*` into the root (index paths unchanged) - tests run as before.
2. `project/`: governance docs, design-package folders, tooling + tests.
3. `backend/common/`: `core/`, `contracts/`, legacy checkers; fix `core/paths.py` (named roots) and the bootstrap.
4. `agents/portfolio-agents/`: plugin root (manifests, skills, entry scripts) + `portfolioAgent/`.
5. `sourcePrepAgent/` and `reviewAgent/` carved out of `engine/`; cutout test split from `test_bleed.py`.
6. Rewrite path references (skills, AGENTS/CONTRIBUTING/STRUCTURE, scripts, tests, evidence pointers via a rewrite table), update `.gitignore`, architecture tests for the new layout.
7. Full test run, commit "Split into agents/backend/frontend", memory + docs.
