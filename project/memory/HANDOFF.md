# Handoff to Codex (and any next session) — written 2026-11-06

## 2026-11-07 DesignCraft edit round trip and agent connection
- Book embeds the pinned official DesignCraft WASM editor. A best-effort same-origin Save observer retains the browser download and offers importing that saved file; manually upload the downloaded `.designcraft` if observation fails. Import renders the actual edited native file with the local DesignCraft CLI into a separate numbered attempt, PDF and previews. A failed ledger append leaves a blocking pending marker with a retry action/API. Original source attempt is only a comparison reference; native derivation from it is not proven.
- reviewAgent binds the edited native/PDF/previews and source-manifest hashes, rechecks source files, blocks pending ledgers and requires explicit human attestations after page/source comparison before finalizing. Neither automated visual/source fidelity nor aesthetic quality is proven. Font substitution can occur.
- An explicit Book UI action asks the portfolio/Claude agent for text-only page suggestions on the edited attempt. It sends extracted PDF text, instructions and source references/hashes to Claude, not images or native/PDF bytes. It cannot inspect layout, crops, fonts, or original asset content; results do not change the native document or substitute for human review. Suggestions are bound to the input hashes and become stale if evidence changes. Model identity and cost are unknown with text-only CLI output.
- Synthetic browser edit/save/import was checked with the actual WASM editor and DesignCraft CLI (5 pages, marker and original source hashes). Synthetic native import plus actual tool-disabled Claude suggestion succeeded; no real user project was sent. Review human attestations were not claimed for that browser run. Remote CI and live design quality still require separate verification.

## 2026-11-07 DesignCraft web integration and structure audit
- Official DesignCraft v0.17.0 Rust/WASM web UI is installed with `python project/scripts/install_designcraft_web.py` (pinned official archive hash, untracked public assets). Book UI can select native export, open the embedded editor, and send a selected attempt by same-origin synthetic drop. On this machine, synthetic arch_03 compose and real browser opening were reproduced; screenshot is `.cache/designcraft-ui-smoke-20261107/frontend-editor-final.png`.
- Historical status (superseded by the round trip above): Web Save downloaded a file and did not sync edits back to the project. The web editor may substitute fonts; DesignCraft crop differences and notes are surfaced as unverified in the UI. Desktop editor opens a separate editable copy. Existing local-output gates do not validate DesignCraft output. Native documents are kept per attempt and bound to new review hashes.
- Benchmark AP-08 schema path and AP-03 page-count decision repaired; runner outputs are isolated and failed checks return nonzero. Only an AP subset with synthetic input was executed; human design-quality review remains open. Optional pascal-agents checkout is pinned and documented in `docs/PASCAL_AGENTS_SETUP.md`; `.github/workflows/ci.yml` added, remote CI execution not yet verified.
- Experimental separate runtime-data wheel supports a synthetic standalone local compose; see `packaging/README.md`. Full API/plugin/DesignCraft installed-wheel parity and reproducible dependency pinning remain unverified. Third-party web bundle stays out of Git, and the parent-to-editor synthetic drag event is not an official DesignCraft bridge.
- Verification: full `uv run pytest -q` 111 passed, 1 skipped (7 subtests); backend 34 passed; benchmark/installer 7 passed; frontend typecheck, lint, 10 tests and build passed; Ruff and import-linter passed. Browser verified the actual embedded editor opens the synthetic file and close cancellation retains it.

## 2026-11-07 review fixes
- Duplicate asset names now return 409 without overwriting originals; TIFF is ingested; plan backups use unique names. Backend regression tests cover these cases.
- Review contexts bind preview, scenes, PDF/PPTX, QA and rubric hashes; recording/finalization reject changes. Old contexts need a new bind and review. Finalization removes formats absent from the new attempt.
- Review UI requires explicit confirmation for every frame; job polling retries transient errors. JobStore serializes background jobs per project in one process. Synchronous API writes and multiple server processes are not covered by that lock; review-to-copy atomicity remains open.
- Verification: `uv run pytest backend -q` 29 passed; `uv run pytest agents/reviewAgent/tests -q` 11 passed; frontend typecheck, lint, 8 tests and build passed. Human review remains necessary for editorial quality. See git status for current commit and push state.

Audience: Codex CLI continuing this workspace after a Claude Code session. Read this file fully, then `AGENTS.md`, `project/AGENTS.md`, `memory/NOW.md`, and the `AGENTS.md` of the folder you work in. The owner speaks Korean and wants short, direct answers (execution over explanation); code, identifiers and contracts stay English.

## 1. Product in one paragraph
**Portfolio Agent ("Pascal")**: a person puts in sources (photos, drawings, diagrams, a brief). Agents arrange and beautify them into a professional portfolio. The **host LLM decides editorial things** and writes a *book plan* (page roles, asset ids, words, flags). **Deterministic rules lay everything out** (grids, type scale, bleed, gates). The LLM never writes coordinates. A beautiful but inaccurate portfolio is a failure: dimensions, overlaps, missing elements, provenance and export readability are hard gates. Originals are never altered (`sources/` keeps them; every transform is logged in `derived.json`).

## 2. State at hand-off (what is DONE and how it was verified)
| area | state | evidence |
|---|---|---|
| Core + 3 agents (portfolioAgent, sourcePrepAgent, reviewAgent) | working, one uv workspace | `uv run pytest` 92 passed, 1 skipped (about 5 min) |
| Backend API `backend/apps/api` | 24 paths, domain packages, jobs, host LLM via `claude -p` | 25 API/backend tests pass; `ruff` clean; `lint-imports` 3 contracts kept |
| Frontend `frontend/` | wemake-based shell on React Router 8, Vite 8, Tailwind 4, React 19; every workflow step has a page | `npm run typecheck && npm run lint && npm test && npm run build` all green (5 tests) |
| End-to-end through the browser | upload → plan (real `claude -p`) → compose → pages/PDF → review → finalize (correctly refused at mean 0.7) | REPRODUCED 2026-11-06 on synthetic `arch_01` (5 pages, 0 blocking gates). Screens in `C:/DK/portfolio_gallery/pascal-*.png` |
| Governance package | `python project/scripts/validate_package.py` PASS, `project/tests` 18 pass | |

**Not verified / not done (be honest about these):**
- **Design quality is not proven.** On the real Robie House project the best blind-critic scores are ours ~0.67 vs plain-host baseline B0 0.65–0.76 (single critic noise about ±0.07; nobody passes 0.75). The next real evidence must be **human blind pairwise review** (`agents/reviewAgent/benchmarks/HUMAN_REVIEW.md`). Synthetic fixtures unblock engineering, not quality claims.
- `cases/approved` is EMPTY: no rights-cleared external cases, so no "learned from real portfolios" claim. The owner's two real example portfolios are private (`C:/DK/real_sources/cases_private/`), never copied or committed.
- API runner is Claude only (`gateways/llm.py` `make_claude_runner`). A Codex runner is *injectable* (same signature) but **not written**. Codex ran `compose` end-to-end through the CLI earlier, so the plan path is host-agnostic; the API wrapper is not.
- No authentication on the API (localhost, CORS limited to `localhost:5173`). No Docker/CI. No LICENSE file. Commit author is the placeholder `User/user@example.com`.
- `claude` CLI sign-in warned it **ends between 2026-11-10 and 2026-11-13**; run `claude auth login` or plan generation fails.
- Frontend gaps (intended, small): `GET /catalog`, `GET /jobs` (list), `GET /health`, attempt `scenes/{page}` and `attempts/{nn}` endpoints have no UI. Plan editing is a page list plus a raw JSON editor (no drag/drop). Review is a manual scoring form (a human or a fresh session fills it).
- Git: The repo is public at `clickaround/portfolio-agent` (main). Check git status and origin for the current state. Commit and push only when the owner requests them.

## 3. Workspace map (one git repo)
```
agents/portfolioAgent/     book: plan -> layout -> gates -> PDF/PPTX/PNG   (src/portfolio_agent/{layout,authors,engine,cli})
agents/sourcePrepAgent/    prepare / levels / knockout / cutout (rembg; photocraft optional)
agents/reviewAgent/        fresh-review binding, blind runs, benchmarks
agents/pascal-agents/      owner's other hub (pptAgent, DiagramAgent, drawingbookAgent); NESTED REPO, git-ignored, do not edit
agents/portfolio-plugin/   plugin shell: .claude-plugin, skills/, scripts/portfolio.py
backend/packages/portfolio-core/   shared kernel: portfolio_agent.core.{model,sources,quality,guardrails,checks,schemas,geometry,workspace}
backend/apps/api/          FastAPI service (the only thing the frontend talks to); openapi.json = contract
frontend/                  the workbench (React Router 8 SPA)
frontend/frontend/         owner's ORIGINAL wemake copy. Git-ignored. NEVER delete, edit or commit (third-party course code)
project/                   governance: AGENTS.md, CONTRIBUTING.md, docs/STRUCTURE.md, PATH_MAP.md, memory/, tasks/, evidence/, research/
.cache/                    ignored: vendor clones, binaries, API data (.cache/pascal-data), logs
portfolio-agent/           EMPTY folder locked by Windows; ignore it (the owner deletes it by hand)
```
Outside the repo by design: `C:/DK/real_sources/` (people's projects, private cases), `C:/DK/portfolio_gallery/` (contact sheets and screenshots).

## 4. Architecture rules you must keep
1. **Layers** (enforced by `uv run lint-imports`, contracts in root `pyproject.toml`): `core <- layout <- authors/backends <- engine <- cli`. The kernel imports no agent or app. The API reaches agent code **only** through `backend/apps/api/src/pascal_api/gateways/agents.py`.
2. **PEP 420 namespace**: `portfolio_agent` spans portfolio-core and the three agents. **Never add `__init__.py`** to `portfolio_agent/` or `portfolio_agent/engine/` (an architecture test fails).
3. **API structure** (checked against zhanymkanov/fastapi-best-practices, see `backend/docs/STRUCTURE_DECISION.md`): one package per domain with `router.py`, `schemas.py`, `service.py`; routers never import another domain's router; a new capability = a new domain package registered in `main.py`. Long work returns `202 {job}` and is polled at `GET /jobs/{id}`; job status values are `queued|running|succeeded|failed`.
4. **Contract flow**: change a Pydantic model or route → `uv run python backend/apps/api/scripts/export_openapi.py` → `cd frontend && npm run api:types`. A test fails when `openapi.json` is stale. Note `separate_input_output_schemas=False`, so fields with defaults are optional in the TS types (use `?? []`).
5. **Frontend conventions** (owner's wemake structure; `frontend/AGENTS.md`): `app/features/<feature>/{pages,components,layouts,queries.ts,mutations.ts,schema.ts}`. Reads in `queries.ts`, writes in `mutations.ts`; pages call them from `clientLoader`/`clientAction` and never call `api.GET/POST` inline. Features never import features (ESLint `import-x/no-restricted-paths`); shared code (`common`, `lib`, `hooks`, `types`) never imports features. Shared job polling lives in `common/components/job-progress.tsx` + `lib/api/jobs.ts`. `react-router` only (no `react-router-dom`), Tailwind 4 CSS-first (`app/app.css`; no tailwind.config/postcss).
6. **Routes** (`frontend/app/routes.ts`): `/projects`, then `route(":projectId", project-layout, [overview, sources, plan, book, review])`. The layout must own the `:projectId` segment, otherwise its relative tab links resolve to `/plan` (this was a real bug; regression test `project-layout.test.tsx`). Static hosting needs an `index.html` fallback for deep links.

## 5. How to run and check
```
uv sync                                                        # once; one .venv, one uv.lock
uv run pascal-api --port 8000                                  # API; docs at http://127.0.0.1:8000/docs
cd frontend && npm install && npm run dev -- --port 5173      # UI (VITE_API_URL overrides http://127.0.0.1:8000)
uv run pytest            # all Python suites (~5 min)   | uv run pytest backend -q   (API, ~15 s)
uv run ruff check .      | uv run lint-imports
cd frontend && npm run typecheck && npm run lint && npm test && npm run build
python project/scripts/validate_package.py                     # governance package check
uv run portfolio compose <project> <book-plan.json> <out> --width-mm 297 --height-mm 210 --bleed-mm 3   # CLI path
```
Env (API): `PASCAL_DATA_DIR`, `PASCAL_CLAUDE_BIN`, `PASCAL_MAX_UPLOAD_MB`, `PASCAL_LLM_TIMEOUT_S` (900), `PASCAL_WORKERS`, `PASCAL_CORS_ORIGINS`. Run Python with `PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1`; never `python -I`.
Synthetic fixtures for any test or smoke run: `agents/portfolioAgent/examples/synthetic_projects/arch_01` (also `arch_02/03`, ux/brand/photo fixtures). Real sources are private; do not send them to any service you were not told to use.

## 6. API surface (what each frontend step calls)
| step | endpoints |
|---|---|
| projects | `GET/POST /projects`, `GET/DELETE /projects/{pid}`, `GET/PUT /projects/{pid}/brief` |
| sources | `POST /projects/{pid}/assets/{kind}` (multipart; kind images/drawings/diagrams), `DELETE .../assets/{kind}/{name}`, `GET /manifest`, `POST /prepare` (sync), `POST /cutout` (job), `GET /files/{kind}/{name}` (bytes) |
| plan | `GET/PUT /book-plan` (404 `no_plan` when none; PUT validates against the schema and the planned author's asset rules; old plan kept under `plans/`), `POST /book-plan/generate` (job; host LLM via `claude -p`; optional compose after) |
| book | `POST /compose` (job), `GET /attempts`, `GET /attempts/{nn}`, `/attempts/{nn}/pages/{n}.png`, `/book.pdf|pptx`, `/scenes/{n}` |
| review | `POST /review/context` → fresh reviewer → `POST /review/record` → `POST /review/finalize` (promotes only if blocking gates passed AND a fresh review passed; verdict rule: pass needs no blockers and mean ≥ 0.75, fail if blockers or mean < 0.5, else revise) |
| misc | `GET /catalog` (grid systems, compositions), `GET /jobs`, `GET /jobs/{jid}`, `GET /health` |
Errors are `{error: {code, message}}`; the frontend turns them into `ApiError`.

## 7. Pitfalls already paid for (do not repeat)
- **Never delete the owner's files.** The session was once stopped with "또라이야?" after `rm -rf` of `frontend/frontend` (restored from `C:\DK\wemake-master\wemake-master`, verified identical). Ignore or rename; ask before deleting.
- Bash heredocs with quotes or special characters break in the Claude Code shell; write files with the file-write tool.
- `npx @tailwindcss/upgrade` also rewrites nested copies (it touched `frontend/frontend`); do not rerun it at the workspace root.
- React Router flattens action-data unions: use `actionData?.job`, not `"job" in actionData`. openapi-fetch captures `globalThis.fetch` at creation, so the client binds fetch late (tests stub it). Keep TypeScript at ~5.9 (openapi-typescript and typescript-eslint peers).
- Vite dev may answer 504 "Outdated Optimize Dep" on first load after installs; reload once.
- Playwright screenshots must be saved inside the workspace; move them to `C:/DK/portfolio_gallery/` afterwards.
- Do not use an Agent/sub-process for web research; search directly. Look at rendered output (contact sheets), not only scores; single-critic differences below 0.1 are noise.
- `GET /projects/{pid}/files/{kind}/{name}` serves bytes though OpenAPI labels it JSON; use URL helpers in `lib/api/urls.ts`, not fetch.

## 8. Permissions and limits (from `project/AGENTS.md`, still binding)
No push, deploy, purchase, secret access or large-scale scraping without explicit permission. Public GitHub clones only, into the ignored `.cache/vendor`, pinned SHAs from `project/research/repos.lock.json`; do not install or run third-party code before the licence gate (`project/evidence/T210-license-gate.md`: MIT/Apache may be adopted with attribution; GPL/AGPL/no licence are read-only). Third-party case PDFs stay private. No Anthropic API billing: LLM work goes through the CLI on the owner's subscription. Evidence labels: `REPRODUCED`, `CODE_INSPECTED`, `DOC_REPORTED`, `HYPOTHESIS`, `BLOCKED`. Every completion report lists task id, changed paths, commands with exit codes, output hashes, evidence status, failed tests and unknowns, ADR/plan changes, next ready task, and separates static tests from real host/backend experiments.

## 9. Suggested next work, in priority order (each with a falsifying check)
1. **Commit the current work when the owner says so** (also decide LICENSE, commit author, whether `pascal-agents` becomes a submodule). Check: `git status` clean except ignored paths; CI-equivalent commands above pass on a fresh clone with `uv sync`.
2. **Codex runner for the API**: implement `make_codex_runner` in `gateways/llm.py` with the same `(prompt, cwd, timeout_s, allowed_tools) -> (rc, text)` signature, select by env `PASCAL_HOST=claude|codex`, keep the Claude default. Codex has no Read tool and breaks with piped stdin (earlier failures; see `project/evidence/logs/codex-plan/`), so write the prompt for its tools. Check: the existing fake-runner tests plus one real `generate` job on `arch_01` that yields a schema-valid plan and a compose with 0 blocking gates.
3. **Human blind pairwise review** (the real quality evidence): follow `agents/reviewAgent/benchmarks/HUMAN_REVIEW.md`, Robie House attempts vs plain-host baseline, with the owner and ideally a domain reviewer. Check: preference counts, not critic scores. Do not claim quality before this.
4. **Frontend completeness**: use `GET /catalog` to offer grid system and composition choices in the plan editor; show scenes per page in the book view; list jobs (`GET /jobs`) so a reload does not lose a running job; replace the JSON plan editor with per-page editing (reorder, change asset or role, flags `bleed|dark|strip|photoset|crop|focus`) that still sends only editorial fields and lets the backend validate. Check: Vitest route tests plus a browser run on `arch_01`.
5. **Source intake UX**: per-asset `role`, `rights` and title/caption editing (the manifest already carries them) and show provenance (`derived.json`) next to each source. Check: manifest round trip test; originals unchanged (hash).
6. **Hardening**: API auth (token or reverse proxy) before anything leaves localhost; upload type/size checks already exist, add per-project quotas; Dockerfile and a CI workflow running the commands in section 5.
7. **Domains beyond architecture** (T100/T101): domain packs for UX/product, branding, photography with non-synthetic fixtures; only then claim multi-domain quality.
8. Open governance items: T209 PyMuPDF AGPL decision (it is imported by the agents), photocraft cut-out option (`uv sync --extra cutout`), DesignCraft local-edit work, pending task DAG in `project/tasks` (`python project/scripts/task_status.py --ready`).

## 10. Where to look
Design intent: `project/AGENTS.md`, `project/GOALS.md`, `project/PLANS.md`, `project/architecture/` (ADRs, notably ADR-0008, ADR-0009). Folder decisions: `backend/docs/STRUCTURE_DECISION.md`, `project/docs/STRUCTURE.md`, `project/PATH_MAP.md`. Agent instructions: `agents/portfolio-plugin/AGENTS.md`, each `agents/*/AGENTS.md`, `frontend/AGENTS.md`, `frontend/README.md`, `backend/apps/api/README.md`. Evidence: `project/evidence/` (notably `BLEED_AND_CUTOUT_2026-11-05.md`), blind-run reports in `agents/reviewAgent/benchmarks/reports/`, history in `project/memory/NOW.md`.
