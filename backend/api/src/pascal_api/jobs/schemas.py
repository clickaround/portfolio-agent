from typing import Any, Literal, Optional

from pydantic import BaseModel


class Job(BaseModel):
    id: str
    kind: str
    project: str
    status: Literal["queued", "running", "succeeded", "failed"]
    created: str
    started: Optional[str] = None
    finished: Optional[str] = None
    log: list[str] = []
    result: Optional[Any] = None
    error: Optional[str] = None


class Accepted(BaseModel):
    job: str
    status: str
    poll: str

    @classmethod
    def of(cls, j: dict) -> "Accepted":
        return cls(job=j["id"], status=j["status"], poll=f"/jobs/{j['id']}")
