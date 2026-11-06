"""Long-running steps are jobs (202 + job id); quick ones answer directly."""
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse

from .. import services
from ..errors import not_found
from ..models import ComposeRequest, CutoutRequest, Job, PlanGenerateRequest, PrepareRequest, ReviewRecord

router = APIRouter(tags=["workflow"])


# ---- jobs -----------------------------------------------------------------------------------------------------------
@router.get("/jobs", response_model=list[Job])
def list_jobs(request: Request, project: str | None = None):
    return request.app.state.jobs.list(project)


@router.get("/jobs/{jid}", response_model=Job)
def get_job(jid: str, request: Request):
    j = request.app.state.jobs.get(jid)
    if not j:
        raise not_found(f"job {jid!r}")
    return j


def _accepted(job):
    return JSONResponse(status_code=202, content={"job": job["id"], "status": job["status"], "poll": f"/jobs/{job['id']}"})


# ---- sourcePrepAgent ------------------------------------------------------------------------------------------------
@router.post("/projects/{pid}/prepare", status_code=200)
def prepare(pid: str, body: PrepareRequest, request: Request):
    """Trim proposals (approve=false) or write trimmed copies; optional levels / knockout. Originals stay in sources/, every step in derived.json."""
    return services.prepare(request.app.state.store.dir(pid), body)


@router.post("/projects/{pid}/cutout", status_code=202)
def cutout(pid: str, body: CutoutRequest, request: Request):
    d = request.app.state.store.dir(pid)
    return _accepted(request.app.state.jobs.submit("cutout", pid, lambda log: services.cutout(d, body)))


# ---- book plan --------------------------------------------------------------------------------------------------------
@router.get("/projects/{pid}/book-plan")
def get_plan(pid: str, request: Request):
    return services.read_plan(request.app.state.store.dir(pid))


@router.put("/projects/{pid}/book-plan")
def put_plan(pid: str, plan: dict, request: Request):
    """Validated against contracts/book-plan.schema.json and the planned author's asset rules; the previous plan is kept under plans/."""
    return services.write_plan(request.app.state.store.dir(pid), plan)


@router.post("/projects/{pid}/book-plan/generate", status_code=202)
def generate_plan(pid: str, body: PlanGenerateRequest, request: Request):
    """The host LLM (Claude Code CLI on the subscription) writes the book plan; optionally composes right after."""
    s = request.app.state
    d = s.store.dir(pid)

    def job(log):
        out = services.generate_plan(d, s.llm_runner, s.settings.llm_timeout_s, body.instructions, log)
        if body.compose:
            out["compose"] = services.compose(d, body.compose, log)
        return out
    return _accepted(s.jobs.submit("plan", pid, job))


# ---- portfolioAgent -------------------------------------------------------------------------------------------------
@router.post("/projects/{pid}/compose", status_code=202)
def compose(pid: str, body: ComposeRequest, request: Request):
    d = request.app.state.store.dir(pid)
    return _accepted(request.app.state.jobs.submit("compose", pid, lambda log: services.compose(d, body, log)))


@router.get("/projects/{pid}/attempts")
def list_attempts(pid: str, request: Request):
    base = request.app.state.store.attempts_dir(pid)
    if not base.is_dir():
        return []
    return [services.attempt_detail(a) for a in sorted(base.glob("[0-9][0-9]"))]


@router.get("/projects/{pid}/attempts/{nn}")
def get_attempt(pid: str, nn: str, request: Request):
    return services.attempt_detail(request.app.state.store.attempt_dir(pid, nn))


@router.get("/projects/{pid}/attempts/{nn}/pages/{page}.png")
def get_page(pid: str, nn: str, page: int, request: Request):
    p = request.app.state.store.attempt_dir(pid, nn) / "preview" / f"page-{page:02d}.png"
    if not p.is_file():
        raise not_found(f"page {page}")
    return FileResponse(p, media_type="image/png")


@router.get("/projects/{pid}/attempts/{nn}/book.{ext}")
def get_book(pid: str, nn: str, ext: str, request: Request):
    if ext not in ("pdf", "pptx"):
        raise not_found(f"book.{ext}")
    p = request.app.state.store.attempt_dir(pid, nn) / f"book.{ext}"
    if not p.is_file():
        raise not_found(f"book.{ext}")
    return FileResponse(p, filename=f"{pid}-{nn}.{ext}")


@router.get("/projects/{pid}/attempts/{nn}/scenes/{page}")
def get_scene(pid: str, nn: str, page: int, request: Request):
    import json
    p = request.app.state.store.attempt_dir(pid, nn) / "scenes" / f"page-{page:02d}.json"
    if not p.is_file():
        raise not_found(f"scene {page}")
    return json.loads(p.read_text(encoding="utf-8"))


# ---- reviewAgent ------------------------------------------------------------------------------------------------------
@router.post("/projects/{pid}/review/context")
def review_context(pid: str, request: Request):
    """Binds the latest attempt's frames + scenes + rubric (hashes) for a FRESH reviewer."""
    return services.review_context(request.app.state.store.dir(pid))


@router.post("/projects/{pid}/review/record")
def review_record(pid: str, body: ReviewRecord, request: Request):
    return services.record_review(request.app.state.store.dir(pid), body.review)


@router.post("/projects/{pid}/review/finalize")
def review_finalize(pid: str, request: Request):
    """Promotes the latest attempt to out/final only if blocking gates passed AND a fresh review passed."""
    return services.finalize(request.app.state.store.dir(pid))
