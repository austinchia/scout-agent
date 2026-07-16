from datetime import datetime

from pydantic import BaseModel, Field

from app.models.classification import Classification


class ScoutProfile(BaseModel):
    id: str | None = None
    company_name: str = Field(min_length=1)
    note: str | None = None
    classification: Classification
    brief: str
    talking_points: list[str] = Field(min_length=1)
    rationale: str
    reference_doc_ids: list[str] = Field(default_factory=list)
    low_confidence: bool = False
    created_at: datetime | None = None
