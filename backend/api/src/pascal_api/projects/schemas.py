from typing import Any, Optional

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$", description="lowercase letters, digits, - and _")
    title: str = ""
    brief: str = Field("", description="project.md markdown (facts the book may quote); default template if empty")


class BriefBody(BaseModel):
    markdown: str


class ProjectInfo(BaseModel):
    id: str
    title: str = ""
    created: Optional[str] = None
    assets: dict[str, int]
    has_plan: bool
    attempts: int


class AssetInfo(BaseModel):
    kind: str
    file: str
    id: str


class ManifestOut(BaseModel):
    manifest: dict[str, Any]
    brief: dict[str, Any]
