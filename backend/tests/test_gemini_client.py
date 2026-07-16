from unittest.mock import MagicMock

import pytest

from app.agent.gemini_client import (
    classify,
    embed_text,
    evaluate_sufficiency,
    generate_talking_points,
    synthesize_brief,
)
from app.agent.search import SearchResult
from app.models.classification import Classification
from app.models.service_line import ServiceLine


def test_embed_text_returns_embedding_vector():
    fake_client = MagicMock()
    fake_embedding = MagicMock(values=[0.1, 0.2, 0.3])
    fake_client.models.embed_content.return_value = MagicMock(embeddings=[fake_embedding])
    result = embed_text("Groupe Clarins", client=fake_client)
    assert result == [0.1, 0.2, 0.3]
    _, kwargs = fake_client.models.embed_content.call_args
    assert kwargs["model"] == "gemini-embedding-001"
    assert kwargs["contents"] == "Groupe Clarins"
    assert kwargs["config"].output_dimensionality == 1536


def test_evaluate_sufficiency_true_on_yes():
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = MagicMock(text="Yes, enough detail.")
    results = [[SearchResult(title="t", url="u", snippet="s")]]
    assert evaluate_sufficiency(results, client=fake_client) is True
    _, kwargs = fake_client.models.generate_content.call_args
    assert kwargs["model"] == "gemini-flash-lite-latest"


def test_evaluate_sufficiency_false_on_no():
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = MagicMock(text="No")
    assert evaluate_sufficiency([], client=fake_client) is False


def test_classify_returns_parsed_classification():
    fake_client = MagicMock()
    expected = Classification(service_line="training", confidence=0.9, rationale="Power BI fit")
    fake_client.models.generate_content.return_value = MagicMock(parsed=expected)
    service_lines = [ServiceLine(id="1", key="training", label="Training", description="BI training")]
    result = classify([[SearchResult(title="t", url="u", snippet="s")]], service_lines, client=fake_client)
    assert result == expected
    _, kwargs = fake_client.models.generate_content.call_args
    assert kwargs["model"] == "gemini-flash-lite-latest"
    assert kwargs["config"].response_schema is Classification


def test_synthesize_brief_splits_brief_and_rationale():
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = MagicMock(text="Company overview here.\n---\nWhy this fits.")
    classification = Classification(service_line="training", confidence=0.9, rationale="x")
    brief, rationale = synthesize_brief([], classification, [], client=fake_client)
    assert brief == "Company overview here."
    assert rationale == "Why this fits."


def test_generate_talking_points_parses_lines():
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = MagicMock(text="- What tools do you use?\n- Who owns reporting?\n")
    classification = Classification(service_line="training", confidence=0.9, rationale="x")
    points = generate_talking_points("brief text", classification, [], client=fake_client)
    assert points == ["What tools do you use?", "Who owns reporting?"]


def test_classify_with_empty_search_results_sends_placeholder_contents():
    fake_client = MagicMock()
    expected = Classification(service_line="training", confidence=0.9, rationale="Power BI fit")
    fake_client.models.generate_content.return_value = MagicMock(parsed=expected)
    service_lines = [ServiceLine(id="1", key="training", label="Training", description="BI training")]
    result = classify([], service_lines, client=fake_client)
    assert result == expected
    _, kwargs = fake_client.models.generate_content.call_args
    assert kwargs["contents"] == "(no results yet)"


def test_evaluate_sufficiency_returns_false_on_none_text():
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = MagicMock(text=None)
    assert evaluate_sufficiency([], client=fake_client) is False


def test_classify_raises_value_error_on_none_parsed():
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = MagicMock(parsed=None)
    service_lines = [ServiceLine(id="1", key="training", label="Training", description="BI training")]
    with pytest.raises(ValueError):
        classify([[SearchResult(title="t", url="u", snippet="s")]], service_lines, client=fake_client)


def test_synthesize_brief_handles_none_text():
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = MagicMock(text=None)
    classification = Classification(service_line="training", confidence=0.9, rationale="x")
    brief, rationale = synthesize_brief([], classification, [], client=fake_client)
    assert brief == ""
    assert rationale == ""


def test_generate_talking_points_handles_none_text():
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = MagicMock(text=None)
    classification = Classification(service_line="training", confidence=0.9, rationale="x")
    points = generate_talking_points("brief text", classification, [], client=fake_client)
    assert points == ["Ask about their current priorities and what's driving this conversation now."]


def test_generate_talking_points_falls_back_when_no_usable_lines():
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = MagicMock(text="   \n  -  \n")
    classification = Classification(service_line="training", confidence=0.9, rationale="x")
    points = generate_talking_points("brief text", classification, [], client=fake_client)
    assert points == ["Ask about their current priorities and what's driving this conversation now."]
