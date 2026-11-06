from typing import Any

from pydantic import BaseModel, Field


class ReviewRecord(BaseModel):
    review: dict[str, Any] = Field(description="review JSON as described in reviewAgent (hashes copied verbatim from review-context)")
