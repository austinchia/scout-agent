import time

from app.agent import gemini_client, search
from app.db import queries
from app.db.connection import get_connection
from app.models.profile import ScoutProfile
from app.models.service_line import ServiceLine

MAX_SEARCH_ATTEMPTS = 3
LOW_CONFIDENCE_THRESHOLD = 0.5


def decide_next_search(company_name: str, note: str | None, attempt: int) -> str:
    if attempt == 0:
        return f"{company_name} company overview industry size"
    if attempt == 1:
        return f"{company_name} recent news"
    focus = note or "business challenges"
    return f"{company_name} {focus} pain points"


def run_scout(company_name: str, note: str | None = None) -> ScoutProfile:
    start = time.monotonic()

    with get_connection() as conn:
        service_line_rows = queries.get_active_service_lines(conn)
    service_lines = [ServiceLine(**row) for row in service_line_rows]

    search_results: list[list[search.SearchResult]] = []
    search_queries: list[str] = []
    sufficient = False
    attempts = 0

    while not sufficient and attempts < MAX_SEARCH_ATTEMPTS:
        query = decide_next_search(company_name, note, attempts)
        search_queries.append(query)
        try:
            results = search.web_search(query)
        except Exception:
            results = []
        search_results.append(results)
        sufficient = gemini_client.evaluate_sufficiency(search_results)
        attempts += 1

    classification = gemini_client.classify(search_results, service_lines)

    query_embedding = gemini_client.embed_text(f"{company_name} {classification.service_line}")
    with get_connection() as conn:
        reference_rows = queries.vector_search(conn, "reference_docs", query_embedding, top_k=5)
    reference_chunks = [row["content"] for row in reference_rows]
    reference_doc_ids = [str(row["id"]) for row in reference_rows]

    brief, rationale = gemini_client.synthesize_brief(search_results, classification, reference_chunks)
    talking_points = gemini_client.generate_talking_points(brief, classification, reference_chunks)

    low_confidence = classification.confidence < LOW_CONFIDENCE_THRESHOLD

    profile = ScoutProfile(
        company_name=company_name,
        note=note,
        classification=classification,
        brief=brief,
        talking_points=talking_points,
        rationale=rationale,
        reference_doc_ids=reference_doc_ids,
        low_confidence=low_confidence,
    )

    profile_embedding = gemini_client.embed_text(f"{company_name} {note or ''} {brief}")
    with get_connection() as conn:
        profile_id = queries.upsert_profile(
            conn,
            {
                "company_name": profile.company_name,
                "note": profile.note,
                "classification": profile.classification.service_line,
                "brief": profile.brief,
                "talking_points": profile.talking_points,
                "rationale": profile.rationale,
                "reference_doc_ids": profile.reference_doc_ids,
                "low_confidence": profile.low_confidence,
            },
            profile_embedding,
        )
        queries.insert_scout_run(
            conn,
            {
                "profile_id": profile_id,
                "search_queries": search_queries,
                "search_results_raw": [[r.__dict__ for r in batch] for batch in search_results],
                "attempts": attempts,
                "duration_ms": int((time.monotonic() - start) * 1000),
            },
        )

    profile.id = str(profile_id)
    return profile
