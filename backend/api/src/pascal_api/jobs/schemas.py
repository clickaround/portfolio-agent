from typing import Any, Literal

from pydantic import BaseModel


class Job(BaseModel):
    id: str
    kind: str
    project: str
    status: Literal["queued", "running", "succeeded", "failed"]
    created: str
    started: str | None = None
    finished: str | None = None
    log: list[str] = []
    result: Any | None = None
    error: str | None = None


class Accepted(BaseModel):
    job: str
    status: str
    poll: str

    @classmethod
    def of(cls, j: dict) -> "Accepted":
        return cls(job=j["id"], status=j["status"], poll=f"/jobs/{j['id']}")
