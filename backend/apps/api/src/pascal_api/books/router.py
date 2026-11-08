"""portfolioAgent: compose a book from the plan; look at attempts (pages, scenes, PDF/PPTX)."""
import ipaddress
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import FileResponse

from ..config import Settings
from ..dependencies import get_analysis_llm, get_jobs, get_settings, get_store, project_dir
from ..exceptions import ApiError, not_found
from ..gateways import agents
from ..jobs.schemas import Accepted
from ..storage.jobs import JobStore
from ..storage.projects import ProjectStore
from . import native_import, service, suggestions
from .schemas import AttemptInfo, ComposeRequest, EditorChatRequest, EditorOpened, EditorTextRequest, SuggestionRecord, SuggestionRequest, SuggestionSummary

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


@router.post("/projects/{pid}/attempts/{nn}/import-designcraft", status_code=202, response_model=Accepted)
def import_designcraft(pid: str, nn: str, request: Request, file: UploadFile = File(...), store: ProjectStore = Depends(get_store),
                       settings: Settings = Depends(get_settings), jobs: JobStore = Depends(get_jobs)):
    """Create a separate attempt from a user-supplied edited DesignCraft file."""
    origin = request.headers.get("origin")
    if origin is not None and origin not in settings.cors_origins:
        raise ApiError(403, "origin_not_allowed", "Browser origin is not configured for this API")
    project = store.dir(pid)
    if not (store.attempt_dir(pid, nn) / "book.designcraft").is_file():
        raise not_found("DesignCraft document")
    if Path(file.filename or "").suffix.lower() != ".designcraft":
        raise ApiError(400, "bad_filename", "Expected a .designcraft file")
    base = project / "out" / ".native-imports"
    base.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="upload-", dir=base))
    try:
        size = 0
        with (staging / "book.designcraft").open("xb") as output:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.max_upload_mb * (1 << 20):
                    raise ApiError(413, "too_large", "Edited document exceeds the upload limit")
                output.write(chunk)
        if size == 0:
            raise ApiError(400, "empty_file", "Edited document is empty")
        return Accepted.of(jobs.submit("import-designcraft", pid, lambda log: native_import.import_attempt(project, nn, staging, log)))
    except BaseException:
        if staging.exists() and staging.resolve().parent == base.resolve():
            shutil.rmtree(staging)
        raise


@router.post("/projects/{pid}/attempts/{nn}/recover-ledger", status_code=202, response_model=Accepted)
def recover_ledger(pid: str, nn: str, request: Request, store: ProjectStore = Depends(get_store),
                   settings: Settings = Depends(get_settings), jobs: JobStore = Depends(get_jobs)):
    """Reconcile a saved import's pending ledger entry using the per-project job lock."""
    origin = request.headers.get("origin")
    if origin is not None and origin not in settings.cors_origins:
        raise ApiError(403, "origin_not_allowed", "Browser origin is not configured for this API")
    project = store.dir(pid)
    store.attempt_dir(pid, nn)
    return Accepted.of(jobs.submit("recover-ledger", pid, lambda log: {"attempt": nn, "status": native_import.recover_pending_ledger(project, nn)}))


@router.post("/projects/{pid}/attempts/{nn}/suggestions", status_code=202, response_model=Accepted)
def create_suggestions(pid: str, nn: str, body: SuggestionRequest, request: Request, store: ProjectStore = Depends(get_store),
                       settings: Settings = Depends(get_settings), jobs: JobStore = Depends(get_jobs), runner=Depends(get_analysis_llm)):
    origin = request.headers.get("origin")
    if origin is not None and origin not in settings.cors_origins:
        raise ApiError(403, "origin_not_allowed", "Browser origin is not configured for this API")
    project, attempt = store.dir(pid), store.attempt_dir(pid, nn)
    return Accepted.of(jobs.submit("native-suggestions", pid,
                                   lambda log: suggestions.generate(project, attempt, body.instructions, body.source_kind, runner, settings.llm_timeout_s, log)))


@router.post("/projects/{pid}/editor-text", status_code=202, response_model=Accepted)
def editor_text(pid: str, body: EditorTextRequest, request: Request, store: ProjectStore = Depends(get_store),
                settings: Settings = Depends(get_settings), jobs: JobStore = Depends(get_jobs), runner=Depends(get_analysis_llm)):
    origin = request.headers.get("origin")
    if origin is not None and origin not in settings.cors_origins:
        raise ApiError(403, "origin_not_allowed", "Browser origin is not configured for this API")
    store.dir(pid)
    return Accepted.of(jobs.submit("editor-text", pid,
                                   lambda log: suggestions.rewrite_editor_text(body.text, body.instructions, runner, settings.llm_timeout_s, log)))


@router.post("/projects/{pid}/attempts/{nn}/editor-chat", status_code=202, response_model=Accepted)
def chat_editor(pid: str, nn: str, body: EditorChatRequest, request: Request, store: ProjectStore = Depends(get_store),
                settings: Settings = Depends(get_settings), jobs: JobStore = Depends(get_jobs), runner=Depends(get_analysis_llm)):
    origin = request.headers.get("origin")
    if origin is not None and origin not in settings.cors_origins:
        raise ApiError(403, "origin_not_allowed", "Browser origin is not configured for this API")
    attempt = store.attempt_dir(pid, nn)
    if not (attempt / "book.pdf").is_file():
        raise not_found("saved PDF")
    if body.messages[-1].role != "user":
        raise ApiError(400, "bad_message", "The last message must come from the user")
    messages = [item.model_dump() for item in body.messages]
    return Accepted.of(jobs.submit("editor-chat", pid,
                                   lambda log: suggestions.editor_chat(attempt, messages, runner, settings.llm_timeout_s, log)))


@router.get("/projects/{pid}/attempts/{nn}/suggestions", response_model=list[SuggestionSummary])
def list_attempt_suggestions(pid: str, nn: str, store: ProjectStore = Depends(get_store)):
    return suggestions.list_suggestions(store.dir(pid), store.attempt_dir(pid, nn))


@router.get("/projects/{pid}/attempts/{nn}/suggestions/{suggestion_id}", response_model=SuggestionRecord)
def get_attempt_suggestion(pid: str, nn: str, suggestion_id: str, store: ProjectStore = Depends(get_store)):
    return suggestions.get_suggestion(store.dir(pid), store.attempt_dir(pid, nn), suggestion_id)


@router.get("/projects/{pid}/attempts/{nn}/scenes/{page}")
def get_scene(pid: str, nn: str, page: int, store: ProjectStore = Depends(get_store)):
    return service.scene(store.attempt_dir(pid, nn), page)
