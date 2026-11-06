"""reviewAgent: the engine never judges taste. Bind frames + hashes -> a FRESH reviewer -> record -> finalize."""
import json
from pathlib import Path

from fastapi import APIRouter, Depends

from ..dependencies import project_dir
from ..gateways import agents
from .schemas import ReviewRecord

router = APIRouter(tags=["reviews"])


@router.post("/projects/{pid}/review/context")
def review_context(d: Path = Depends(project_dir)):
    """Binds the latest attempt's frames + scenes + rubric (hashes) for a fresh reviewer."""
    return agents.review_context(d / "out")


@router.post("/projects/{pid}/review/record")
def review_record(body: ReviewRecord, d: Path = Depends(project_dir)):
    tmp = d / "out" / "_review_in.json"
    tmp.parent.mkdir(exist_ok=True)
    tmp.write_text(json.dumps(body.review), encoding="utf-8")
    try:
        return agents.record_review(d / "out", tmp)
    finally:
        tmp.unlink(missing_ok=True)


@router.post("/projects/{pid}/review/finalize")
def review_finalize(d: Path = Depends(project_dir)):
    """Promotes the latest attempt to out/final only if blocking gates passed AND a fresh review passed."""
    return agents.finalize(d / "out")
