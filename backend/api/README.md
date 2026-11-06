# backend/api - Pascal API

FastAPI service over the agents. **Thin on purpose**: routes -> `services.py` -> one agent call each. No layout/engine logic here.

```
python backend/api/run.py --port 8000          # docs: http://127.0.0.1:8000/docs   contract: backend/api/openapi.json
python -m pytest backend/api/tests -q          # 10 end-to-end tests on the synthetic fixtures (no LLM, no real sources)
python backend/api/scripts/export_openapi.py   # regenerate openapi.json after changing models/routes (a test fails when it is stale)
```
Env: `PASCAL_DATA_DIR` (default `<workspace>/.cache/pascal-data`), `PASCAL_CLAUDE_BIN`, `PASCAL_MAX_UPLOAD_MB` (100), `PASCAL_LLM_TIMEOUT_S` (900), `PASCAL_WORKERS` (2), `PASCAL_CORS_ORIGINS`. No auth yet: bind to localhost only.

## Workflow (what the frontend drives)
| step | endpoint | agent |
|---|---|---|
| create project, brief (`project.md` = the only source of quotable facts) | `POST /projects`, `PUT /projects/{id}/brief` | - |
| upload sources | `POST /projects/{id}/assets/{images\|drawings\|diagrams}` (multipart `file`) | - |
| what the agents see | `GET /projects/{id}/manifest` | portfolioAgent (ingest) |
| prepare scans (trim proposals / levels / knockout), cut-outs | `POST .../prepare`, `POST .../cutout` (job) | sourcePrepAgent |
| book plan: write it | `PUT /projects/{id}/book-plan` (schema + asset rules -> 422 with the author's message) | portfolioAgent |
| book plan: host LLM writes it | `POST .../book-plan/generate` (job; `claude -p` on the subscription, one retry with the rejection reason; optional `compose`) | host LLM |
| compose | `POST .../compose` (job) -> attempt | portfolioAgent |
| look | `GET .../attempts`, `.../attempts/{nn}`, `.../pages/{n}.png`, `.../scenes/{n}`, `.../book.pdf\|pptx` | - |
| what a plan may use | `GET /catalog` (roles, page flags, grid systems, compositions, photo sets, backends) | portfolioAgent |
| independent review | `POST .../review/context` -> fresh reviewer -> `POST .../review/record` -> `POST .../review/finalize` | reviewAgent |
| jobs | `GET /jobs`, `GET /jobs/{id}` (status, log, result, error; persisted, survive restarts) | - |

Errors are `{"error": {"code", "message"}}`. A failed job is data (`status: failed`, `error`), never a crashed worker.

## Rules
- Routes import `services.py` only; `services.py` is the only module that imports `portfolio_agent` (tested).
- The API never calls a paid HTTP LLM API. The host LLM is the Claude Code CLI via `llm.py` (injectable runner: tests, Codex).
- File names are sanitised, extensions allow-listed, paths resolved inside the project folder, uploads size-limited and cleaned up on overflow.
- The book plan carries editorial decisions and flags, never coordinates (same contract as the CLI).
