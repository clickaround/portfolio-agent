"""sourcePrepAgent: people's raw sources -> clean assets. Originals stay in sources/, every step is recorded in derived.json."""
from pathlib import Path

from fastapi import APIRouter, Depends

from ..dependencies import get_jobs, project_dir
from ..gateways import agents
from ..jobs.schemas import Accepted
from ..storage.jobs import JobStore
from .schemas import CutoutRequest, PrepareRequest, PrepareResult

router = APIRouter(tags=["sources"])


@router.post("/projects/{pid}/prepare", response_model=PrepareResult)
def prepare(body: PrepareRequest, d: Path = Depends(project_dir)):
    """Trim proposals (approve=false) or write trimmed copies; optional levels / knockout."""
    return agents.prepare(d, body.approve, body.levels, body.knockout, body.knockout_files)


@router.post("/projects/{pid}/cutout", status_code=202, response_model=Accepted)
def cutout(pid: str, body: CutoutRequest, d: Path = Depends(project_dir), jobs: JobStore = Depends(get_jobs)):
    j = jobs.submit("cutout", pid, lambda log: agents.cutout(d, body.files, body.engine))
    return Accepted.of(j)
