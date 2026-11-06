from fastapi import APIRouter, Depends

from ..dependencies import get_jobs
from ..exceptions import not_found
from ..storage.jobs import JobStore
from .schemas import Job

router = APIRouter(tags=["jobs"])


@router.get("/jobs", response_model=list[Job])
def list_jobs(project: str | None = None, jobs: JobStore = Depends(get_jobs)):
    return jobs.list(project)


@router.get("/jobs/{jid}", response_model=Job)
def get_job(jid: str, jobs: JobStore = Depends(get_jobs)):
    j = jobs.get(jid)
    if not j:
        raise not_found(f"job {jid!r}")
    return j
