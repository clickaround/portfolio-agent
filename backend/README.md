# backend

Python workspace (uv) for everything server-side that is shared or runnable. Agents live in `../agents/*` and are workspace members too; one lockfile (`../uv.lock`), one virtualenv (`../.venv`), all members installed editable - no `sys.path` tricks.

```
backend/
  packages/
    portfolio-core/            SHARED KERNEL (dist `portfolio-core`, import `portfolio_agent.core`)
      src/portfolio_agent/core/
        model/                 Plan / Scene contracts, element-id conventions
        sources/               asset ingestion, hashing, brief parsing
        geometry.py            fit / columns
        quality/               diagnostics, page metrics
        guardrails/            gates, grounding, policy, references, repair (blocking vs advisory)
        checks/                stdlib validators (layout, edit_diff, asset_hash) - were loose scripts
        schemas/               JSON schemas (book plan, scene document, ...) ship with the code that validates them
        workspace.py           the only module that knows where folders live
      tests/                   architecture rules (layers, folders, namespace)
  apps/
    api/                       FastAPI service (dist `pascal-api`): domain packages + gateways + storage
```
Rules: `packages/*` are libraries (no I/O entry points); `apps/*` are runnable services. Dependencies point inward: `apps -> agents -> packages/portfolio-core`. The kernel imports no agent and no app (checked by import-linter, `uv run lint-imports`).

```
uv sync                          # once; add --extra cutout (rembg) when you need cut-outs
uv run pytest                    # every Python suite (core, api, 3 agents)
uv run lint-imports              # layer contracts across all packages
uv run ruff check .
uv run pascal-api --port 8000    # or: python backend/apps/api/run.py
uv run portfolio compose ...     # the CLI of the book agent
```
Why this shape (uv workspace, shared kernel kept small, per-responsibility sub-packages, import contracts): `docs/STRUCTURE_DECISION.md`.
