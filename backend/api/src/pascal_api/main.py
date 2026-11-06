"""FastAPI app factory. Run: `python backend/api/run.py` (or `uvicorn pascal_api.main:app` with PYTHONPATH=backend/api/src)."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import _boot  # noqa: F401
from .errors import ApiError
from .jobs import JobStore
from .llm import make_claude_runner
from .routes import projects, workflow
from .settings import Settings, get_settings
from .store import ProjectStore

VERSION = "0.1.0"


def create_app(settings: Settings | None = None, llm_runner=None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Pascal API", version=VERSION, description="HTTP service over the portfolio agents: sources -> book plan -> composed book -> fresh review.")
    app.state.settings = settings
    app.state.store = ProjectStore(settings.data_dir)
    app.state.jobs = JobStore(settings.data_dir, settings.workers)
    app.state.llm_runner = llm_runner or make_claude_runner(settings.claude_bin)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_methods=["*"], allow_headers=["*"])

    @app.exception_handler(ApiError)
    async def api_error(_: Request, e: ApiError):
        return JSONResponse(status_code=e.status, content={"error": {"code": e.code, "message": e.message}})

    @app.get("/health", tags=["meta"])
    def health():
        from portfolio_agent.core import paths as P
        return {"status": "ok", "version": VERSION, "data_dir": str(settings.data_dir), "backends": sorted(p.parent.name for p in P.BACKENDS_DIR.glob("*/adapter.py"))}

    app.include_router(projects.router)
    app.include_router(workflow.router)
    return app

