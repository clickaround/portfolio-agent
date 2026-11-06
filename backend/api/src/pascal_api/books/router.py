"""portfolioAgent: compose a book from the plan; look at attempts (pages, scenes, PDF/PPTX)."""
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from ..dependencies import get_jobs, get_store, project_dir
from ..exceptions import not_found
from ..jobs.schemas import Accepted
from ..storage.jobs import JobStore
from ..storage.projects import ProjectStore
from . import service
from .schemas import AttemptInfo, ComposeRequest

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
    if ext not in ("pdf", "pptx") or not p.is_file():
        raise not_found(f"book.{ext}")
    return FileResponse(p, filename=f"{pid}-{nn}.{ext}")


@router.get("/projects/{pid}/attempts/{nn}/scenes/{page}")
def get_scene(pid: str, nn: str, page: int, store: ProjectStore = Depends(get_store)):
    return service.scene(store.attempt_dir(pid, nn), page)
