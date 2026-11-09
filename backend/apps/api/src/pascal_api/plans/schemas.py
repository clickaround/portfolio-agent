
from pydantic import BaseModel, Field

from ..books.schemas import ComposeRequest


class PlanSaved(BaseModel):
    pages: int
    versions: int


class PlanGenerateRequest(BaseModel):
    instructions: str = Field("", max_length=4000, description="extra direction for the host LLM (tone, page count, what to emphasise)")
    compose: ComposeRequest | None = Field(None, description="when set, compose right after the plan is written")
