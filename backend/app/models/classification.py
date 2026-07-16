from pydantic import BaseModel, Field

from app.models.service_line import ServiceLineKey


class Classification(BaseModel):
    service_line: ServiceLineKey
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
