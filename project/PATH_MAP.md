# PATH_MAP: pre-split (2026-11-05, "portfolio-agent/") -> now

Old documents and evidence logs keep the old paths in their text; use this table to translate. Baseline commit before the split: `62e8714`.

| old (under portfolio-agent/) | now |
|---|---|
| `runtime/portfolio_agent/core/**` | `backend/common/src/portfolio_agent/core/**` |
| `runtime/portfolio_agent/layout/**`, `authors/**`, `cli.py` | `agents/portfolioAgent/src/portfolio_agent/...` |
| `runtime/portfolio_agent/engine/{pipeline,catalogue,grid,guides,spec,candidates,edit,ingest_view,registry}.py` | `agents/portfolioAgent/src/portfolio_agent/engine/` |
| `runtime/portfolio_agent/engine/{prepare,levels,cutout}.py` | `agents/sourcePrepAgent/src/portfolio_agent/engine/` |
| `runtime/portfolio_agent/engine/review.py` | `agents/reviewAgent/src/portfolio_agent/engine/review.py` |
| `runtime/ARCHITECTURE.md` | `backend/common/ARCHITECTURE.md` |
| `contracts/` | `backend/common/contracts/` |
| `scripts/check_{layout,edit_diff,asset_hash}.py` | `backend/common/checks/` |
| `scripts/portfolio.py`, `contact_sheet.py`, `guides_overlay.py`, `preview.py`, `import_pascal_layouts.py` | `agents/portfolio-plugin/scripts/` |
| `scripts/{task_status,task_update,validate_package,clone_repos,audit_repos,validate_contracts,format_check}.py` | `project/scripts/` |
| `skills/`, `.claude-plugin/`, `.codex-plugin/`, `plugin.json`, `.agents/plugins/` | `agents/portfolio-plugin/` |
| `backends/` (local, designcraft, ...), `knowledge/`, `examples/` | `agents/portfolioAgent/` |
| `knowledge/editorial/critic-rubric.md` | `agents/reviewAgent/knowledge/critic-rubric.md` |
| `benchmarks/` | `agents/reviewAgent/benchmarks/` |
| `tests/test_{architecture}.py` | `backend/common/tests/` |
| `tests/test_{bleed,domains,grid,harness,layout,layout_craft,modular,photoset,runtime,references,scene_v02}.py` | `agents/portfolioAgent/tests/` |
| (cut-out test, split from test_bleed) | `agents/sourcePrepAgent/tests/test_cutout.py` |
| `tests/test_{package,v2,v3,task_evidence}.py` | `project/tests/` |
| `AGENTS.md CLAUDE.md GOALS.md PLANS.md README*.md VALIDATION_REPORT_*.md CONTRIBUTING.md docs/ architecture/ plans/ prompts/ tasks/ research/ evidence/ memory/ cases/ formats/ integrations/` | `project/` |
| `agents/` (roles, contracts) | `project/agent-roles/` |
| `core/` (docs only) | `project/core-ir/` |
| `.cache/` | `.cache/` at the workspace root |
