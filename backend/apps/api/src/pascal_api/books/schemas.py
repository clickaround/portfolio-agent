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
    native_edit: bool = False
    ledger_pending: bool = False
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


class SuggestionRequest(BaseModel):
    instructions: str = Field(default="", max_length=4000)
    source_kind: Literal["synthetic", "real", "unknown"] = "unknown"


class EditorTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    instructions: str = Field(default="", max_length=1000)


class SuggestionSummary(BaseModel):
    suggestion_id: str
    created_at: str
    source_kind: Literal["synthetic", "real", "unknown"]
    status: Literal["fresh", "stale"]


class AnalysisIssue(BaseModel):
    issue: str
    recommendation: str
    evidence: str


class AnalysisPage(BaseModel):
    page: int
    suggestions: list[AnalysisIssue]


class AnalysisOutput(BaseModel):
    summary: str
    pages: list[AnalysisPage]


class SuggestionRecord(BaseModel):
    suggestion_id: str
    attempt: str
    created_at: str
    source_kind: Literal["synthetic", "real", "unknown"]
    source_kind_basis: Literal["user_reported"]
    analysis_mode: Literal["text_only"]
    limitations: list[str]
    text_truncated: bool
    model: str
    cost_usd: float | None
    input_hashes: dict[str, Any]
    instructions_sha256: str
    prompt_sha256: str
    output_sha256: str
    output: AnalysisOutput
    raw_output: str
