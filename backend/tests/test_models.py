import pytest
from pydantic import ValidationError

from app.models.classification import Classification
from app.models.profile import ScoutProfile


def test_classification_accepts_valid_service_line():
    c = Classification(service_line="training", confidence=0.8, rationale="Matches Power BI training pattern")
    assert c.service_line == "training"


def test_classification_rejects_invalid_service_line():
    with pytest.raises(ValidationError):
        Classification(service_line="not_a_real_line", confidence=0.8, rationale="x")


def test_classification_rejects_confidence_out_of_range():
    with pytest.raises(ValidationError):
        Classification(service_line="training", confidence=1.5, rationale="x")


def test_scout_profile_requires_at_least_one_talking_point():
    with pytest.raises(ValidationError):
        ScoutProfile(
            company_name="Groupe Clarins",
            classification=Classification(service_line="training", confidence=0.8, rationale="x"),
            brief="...",
            talking_points=[],
            rationale="...",
        )


def test_scout_profile_valid_construction_defaults_low_confidence_false():
    profile = ScoutProfile(
        company_name="Groupe Clarins",
        classification=Classification(service_line="training", confidence=0.8, rationale="Matches Power BI pattern"),
        brief="Clarins is a cosmetics company.",
        talking_points=["What BI tools do you currently use?"],
        rationale="Power BI training fits their HR-driven inbound interest.",
    )
    assert profile.low_confidence is False
    assert profile.id is None
