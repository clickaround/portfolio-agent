"""portfolioAgent: compose a book from the plan; look at attempts (pages, scenes, PDF/PPTX)."""
import ipaddress
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse

from ..config import Settings
from ..dependencies import get_jobs, get_settings, get_store, project_dir
from ..exceptions import ApiError, not_found
from ..gateways import agents
from ..jobs.schemas import Accepted
from ..storage.jobs import JobStore
from ..storage.projects import ProjectStore
from . import service
from .schemas import AttemptInfo, ComposeRequest, EditorOpened

router = APIRouter(tags=["books"])


@router.post("/projects/{pid}/compose", status_code=202, response_model=Accepted)
def compose(pid: str, body: ComposeRequest, d: Path = Depends(project_dir), jobs: JobStore = Depends(get_jobs)):
    return Accepted.of(jobs.submit("compose", pid, lambda log: service.compose(d, body, log)))


@router.get("/projects/{pid}/attempts", response_model=list[AttemptInfo])
def list_attempts(pid: str, store: ProjectStore = Depends(get_store)):
    base = store.attempts_dir(pid)
    return [service.attempt_info(a) for a in sorted(base.glob("[0-9][0-9]"))] if base.is_dir() else []


@router.get("/projects/{pid}/attempts/{nn}", response_model=AttemptInfo)
def get_attempt(pid: str, nn: str, store: ProjectStore = Depends(get_store)):
    return service.attempt_info(store.attempt_dir(pid, nn))


@router.get("/projects/{pid}/attempts/{nn}/pages/{page}.png", response_class=FileResponse)
def get_page(pid: str, nn: str, page: int, store: ProjectStore = Depends(get_store)):
    p = store.attempt_dir(pid, nn) / "preview" / f"page-{page:02d}.png"
    if not p.is_file():
        raise not_found(f"page {page}")
    return FileResponse(p, media_type="image/png")


@router.get("/projects/{pid}/attempts/{nn}/book.{ext}", response_class=FileResponse)
def get_book(pid: str, nn: str, ext: str, store: ProjectStore = Depends(get_store)):
    p = store.attempt_dir(pid, nn) / f"book.{ext}"
    if ext not in ("pdf", "pptx", "designcraft") or not p.is_file():
        raise not_found(f"book.{ext}")
    return FileResponse(p, filename=f"{pid}-{nn}.{ext}")


@router.post("/projects/{pid}/attempts/{nn}/open-designcraft", response_model=EditorOpened)
def open_designcraft(pid: str, nn: str, request: Request, body: dict, store: ProjectStore = Depends(get_store), settings: Settings = Depends(get_settings)):
    """Launch the local editor on a separate copy, only from the configured local web UI."""
    try:
        local = bool(request.client and ipaddress.ip_address(request.client.host).is_loopback)
    except ValueError:
        local = False
    if not local or request.headers.get("origin") not in settings.cors_origins:
        raise ApiError(403, "local_only", "Editor launch requires the configured local UI")
    source = store.attempt_dir(pid, nn) / "book.designcraft"
    if not source.is_file():
        raise not_found("DesignCraft document")
    return agents.open_designcraft(source, store.dir(pid))


@router.get("/projects/{pid}/attempts/{nn}/scenes/{page}")
def get_scene(pid: str, nn: str, page: int, store: ProjectStore = Depends(get_store)):
    return service.scene(store.attempt_dir(pid, nn), page)
