from pathlib import Path

from fastapi import APIRouter, Depends

from ..books import service as books
from ..config import Settings
from ..dependencies import get_jobs, get_llm, get_settings, project_dir
from ..jobs.schemas import Accepted
from ..storage.jobs import JobStore
from . import service
from .schemas import PlanGenerateRequest, PlanSaved

router = APIRouter(tags=["plans"])


@router.get("/projects/{pid}/book-plan")
def get_plan(d: Path = Depends(project_dir)):
    return service.read(d)


@router.put("/projects/{pid}/book-plan", response_model=PlanSaved)
def put_plan(plan: dict, d: Path = Depends(project_dir)):
    """Validated against contracts/book-plan.schema.json and the planned author's asset rules (422 with the author's message); the previous plan is kept under plans/."""
    return service.write(d, plan)


@router.post("/projects/{pid}/book-plan/generate", status_code=202, response_model=Accepted)
def generate_plan(pid: str, body: PlanGenerateRequest, d: Path = Depends(project_dir), jobs: JobStore = Depends(get_jobs),
                  settings: Settings = Depends(get_settings), runner=Depends(get_llm)):
    """The host LLM writes the book plan; optionally composes right after."""
    def job(log):
        out = service.generate(d, runner, settings.llm_timeout_s, body.instructions, log)
        if body.compose:
            out["compose"] = books.compose(d, body.compose, log)
        return out
    return Accepted.of(jobs.submit("plan", pid, job))
