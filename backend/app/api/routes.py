from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.loop import run_scout
from app.models.profile import ScoutProfile

router = APIRouter()


class ScoutRunRequest(BaseModel):
    company_name: str = Field(min_length=1)
    note: str | None = None


@router.post("/scout/run", response_model=ScoutProfile)
def scout_run(request: ScoutRunRequest) -> ScoutProfile:
    try:
        return run_scout(request.company_name, request.note)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Scout run failed: {exc}") from exc
