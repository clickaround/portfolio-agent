from typing import Any, Optional

from pydantic import BaseModel, Field


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


class AttemptInfo(BaseModel):
    attempt: str
    gate_pass: Optional[bool] = None
    blocking: list[Any] = []
    advisory: list[Any] = []
    page_scores: Optional[Any] = None
    pages: list[str] = []
    files: dict[str, bool] = {}
    reference_basis: Optional[Any] = None
