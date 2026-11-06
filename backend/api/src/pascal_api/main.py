"""FastAPI app factory (a fresh app per call keeps tests isolated). Run: `python backend/api/run.py`.

Layout (domain packages, each with router.py / schemas.py / service.py; shared things at this level):
    config.py exceptions.py dependencies.py main.py     global
    gateways/   adapters to the outside world: agents.py (the ONLY importer of portfolio_agent), llm.py (host-LLM runner)
    storage/    projects.py (project folders), jobs.py (background jobs)
    projects/ sources/ plans/ books/ reviews/ jobs/ catalog/    one package per domain
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from . import _boot  # noqa: F401
from .books.router import router as books_router
from .catalog.router import router as catalog_router
from .config import Settings, get_settings
from .exceptions import ApiError
from .gateways import agents
from .gateways.llm import make_claude_runner
from .jobs.router import router as jobs_router
from .plans.router import router as plans_router
from .projects.router import router as projects_router
from .reviews.router import router as reviews_router
from .sources.router import router as sources_router
from .storage.jobs import JobStore
from .storage.projects import ProjectStore

VERSION = "0.2.0"


def _operation_id(route: APIRoute) -> str:
    """Stable client method names: <tag>_<function>, e.g. books_compose."""
    return f"{route.tags[0] if route.tags else 'api'}_{route.name}"


def create_app(settings: Settings | None = None, llm_runner=None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Pascal API", version=VERSION, generate_unique_id_function=_operation_id,
                  description="HTTP service over the portfolio agents: sources -> book plan -> composed book -> fresh review.")
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
        return {"status": "ok", "version": VERSION, "data_dir": str(settings.data_dir), "backends": agents.backends()}

    for r in (projects_router, sources_router, plans_router, books_router, reviews_router, jobs_router, catalog_router):
        app.include_router(r)
    return app
