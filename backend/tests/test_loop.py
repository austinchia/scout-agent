from contextlib import contextmanager
from unittest.mock import MagicMock

from app.agent import loop
from app.agent.search import SearchResult
from app.models.classification import Classification


@contextmanager
def _fake_connection():
    yield MagicMock()


def test_decide_next_search_progresses_through_focus_areas():
    assert loop.decide_next_search("Acme", None, 0) == "Acme company overview industry size"
    assert loop.decide_next_search("Acme", None, 1) == "Acme recent news"
    assert loop.decide_next_search("Acme", "Power BI training", 2) == "Acme Power BI training pain points"
    assert loop.decide_next_search("Acme", None, 2) == "Acme business challenges pain points"


def _patch_common(monkeypatch, classification, talking_points=("Question one?", "Question two?")):
    monkeypatch.setattr(loop, "get_connection", _fake_connection)
    monkeypatch.setattr(
        loop.queries,
        "get_active_service_lines",
        lambda conn: [{"id": "1", "key": classification.service_line, "label": "L", "description": "D"}],
    )
    monkeypatch.setattr(loop.gemini_client, "classify", lambda results, lines: classification)
    monkeypatch.setattr(loop.gemini_client, "embed_text", lambda text: [0.1, 0.2])
    monkeypatch.setattr(loop.queries, "vector_search", lambda conn, table, embedding, top_k=5: [])
    monkeypatch.setattr(
        loop.gemini_client, "synthesize_brief", lambda results, classification, grounding: ("Brief text", "Rationale text")
    )
    monkeypatch.setattr(
        loop.gemini_client, "generate_talking_points", lambda brief, classification, grounding: list(talking_points)
    )
    monkeypatch.setattr(loop.queries, "upsert_profile", lambda conn, profile, embedding: "profile-123")
    monkeypatch.setattr(loop.queries, "insert_scout_run", lambda conn, run: "run-456")


def test_run_scout_orchestrates_full_pipeline(monkeypatch):
    classification = Classification(service_line="training", confidence=0.9, rationale="Fits BI training")
    _patch_common(monkeypatch, classification)
    monkeypatch.setattr(loop.search, "web_search", lambda query: [SearchResult(title="t", url="u", snippet=query)])
    monkeypatch.setattr(loop.gemini_client, "evaluate_sufficiency", lambda results: True)
    monkeypatch.setattr(
        loop.queries, "vector_search", lambda conn, table, embedding, top_k=5: [{"id": "ref-1", "content": "Past proposal excerpt"}]
    )

    profile = loop.run_scout("Groupe Clarins", "inbound via HR contact")

    assert profile.id == "profile-123"
    assert profile.classification.service_line == "training"
    assert profile.brief == "Brief text"
    assert profile.rationale == "Rationale text"
    assert profile.talking_points == ["Question one?", "Question two?"]
    assert profile.reference_doc_ids == ["ref-1"]
    assert profile.low_confidence is False


def test_run_scout_flags_low_confidence(monkeypatch):
    classification = Classification(service_line="other", confidence=0.2, rationale="Very little public info")
    _patch_common(monkeypatch, classification, talking_points=("Any question?",))
    monkeypatch.setattr(loop.search, "web_search", lambda query: [])
    monkeypatch.setattr(loop.gemini_client, "evaluate_sufficiency", lambda results: False)

    profile = loop.run_scout("Tiny Obscure Co")

    assert profile.low_confidence is True


def test_run_scout_survives_a_failed_search_attempt(monkeypatch):
    classification = Classification(service_line="training", confidence=0.7, rationale="x")
    _patch_common(monkeypatch, classification, talking_points=("Q?",))

    call_count = {"n": 0}

    def flaky_web_search(query):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("search provider timeout")
        return [SearchResult(title="t", url="u", snippet=query)]

    monkeypatch.setattr(loop.search, "web_search", flaky_web_search)
    monkeypatch.setattr(loop.gemini_client, "evaluate_sufficiency", lambda results: bool(results[-1]))

    profile = loop.run_scout("Groupe Clarins")

    assert call_count["n"] == 2
    assert profile.brief == "Brief text"


def test_run_scout_stops_after_max_attempts_even_if_never_sufficient(monkeypatch):
    classification = Classification(service_line="other", confidence=0.3, rationale="x")
    _patch_common(monkeypatch, classification, talking_points=("Q?",))
    call_count = {"n": 0}

    def counting_web_search(query):
        call_count["n"] += 1
        return []

    monkeypatch.setattr(loop.search, "web_search", counting_web_search)
    monkeypatch.setattr(loop.gemini_client, "evaluate_sufficiency", lambda results: False)

    loop.run_scout("Never Enough Co")

    assert call_count["n"] == loop.MAX_SEARCH_ATTEMPTS
