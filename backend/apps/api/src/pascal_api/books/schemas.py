from typing import Any, Literal

from pydantic import BaseModel, Field


class ComposeRequest(BaseModel):
    width_mm: float = 297
    height_mm: float = 210
    margin_mm: float = 12
    bleed_mm: float = 0
    paper_color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    accent_color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    text_color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    header: bool = True
    footer: bool | None = None
    band: dict[str, Any] | None = Field(None, description='{"side": "left|top", "color": "#hex", "width_mm": 6, "every_page": true}')
    domain: str | None = None
    also: list[str] = Field(default_factory=list, description='extra exporter backends, e.g. ["designcraft"]')


class DesignCraftStatus(BaseModel):
    status: Literal["unverified"] = Field(description="Native DesignCraft output has not been independently rendered and verified; gate_pass applies to the local output.")
    notes: list[str] = Field(default_factory=list, description="Exporter warnings such as unsupported crop or font substitution.")


class AttemptInfo(BaseModel):
    attempt: str
    gate_pass: bool | None = None
    blocking: list[Any] = []
    advisory: list[Any] = []
    page_scores: Any | None = None
    pages: list[str] = []
    files: dict[str, bool] = {}
    reference_basis: Any | None = None
    designcraft: DesignCraftStatus | None = None


class EditorOpened(BaseModel):
    opened: bool
    edit_path: str
    message: str
