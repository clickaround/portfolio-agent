from typing import Literal

from pydantic import BaseModel, Field


class PrepareRequest(BaseModel):
    approve: bool = Field(False, description="false = only propose sheet trims; true = write the trimmed copies (originals stay in sources/)")
    levels: bool = False
    knockout: bool = Field(False, description="make the drawings' paper transparent")
    knockout_files: list[str] = Field(default_factory=list, description="extra files relative to the project, e.g. diagrams/overlay_plan.png")


class CutoutRequest(BaseModel):
    files: list[str] = Field(min_length=1, description="file names under images/ chosen by the host/person")
    engine: Literal["rembg", "photocraft"] = "rembg"


class PrepareResult(BaseModel):
    proposals: int
    approved: bool
    derived: int
    sheet: str | None = None
    levels: list[str] | None = None
    knockout: list[str] | None = None
