"""Request / response bodies (pydantic). The OpenAPI document generated from these is the contract the frontend codes against (backend/api/openapi.json)."""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$", description="lowercase letters, digits, - and _")
    title: str = ""
    brief: str = Field("", description="project.md markdown (facts the book may quote); default template if empty")


class BriefBody(BaseModel):
    markdown: str


class PrepareRequest(BaseModel):
    approve: bool = Field(False, description="false = only propose sheet trims; true = write the trimmed copies (originals stay in sources/)")
    levels: bool = False
    knockout: bool = Field(False, description="make the drawings' paper transparent")
    knockout_files: list[str] = Field(default_factory=list, description="extra files relative to the project, e.g. diagrams/overlay_plan.png")


class CutoutRequest(BaseModel):
    files: list[str] = Field(min_length=1, description="file names under images/ chosen by the host/person")
    engine: Literal["rembg", "photocraft"] = "rembg"


class ComposeRequest(BaseModel):
    width_mm: float = 297
    height_mm: float = 210
    margin_mm: float = 12
    bleed_mm: float = 0
    paper_color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    accent_color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    text_color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    header: bool = True
    footer: Optional[bool] = None
    band: Optional[dict[str, Any]] = Field(None, description='{"side": "left|top", "color": "#hex", "width_mm": 6, "every_page": true}')
    domain: Optional[str] = None
    also: list[str] = Field(default_factory=list, description='extra exporter backends, e.g. ["designcraft"]')


class PlanGenerateRequest(BaseModel):
    instructions: str = Field("", description="extra direction for the host LLM (tone, page count, what to emphasise)")
    compose: Optional[ComposeRequest] = Field(None, description="when set, compose right after the plan is written")


class ReviewRecord(BaseModel):
    review: dict[str, Any] = Field(description="review JSON as described in reviewAgent (hashes copied verbatim from review-context)")


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


class Problem(BaseModel):
    code: str
    message: str
