import os
import random

import pytest

from app.db.connection import get_connection
from app.db.migrate import run_migrations
from app.db import queries

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="requires a live DATABASE_URL")

_TEST_COMPANY_NAMES = [
    "Test Upsert Co",
    "Close Match Co",
    "Far Match Co",
    "Scout Run Link Co",
]


@pytest.fixture(autouse=True, scope="module")
def _migrated():
    run_migrations()
    with get_connection() as conn:
        with conn.cursor() as cur:
            names = [name.lower() for name in _TEST_COMPANY_NAMES]
            cur.execute(
                "DELETE FROM scout_runs WHERE profile_id IN "
                "(SELECT id FROM profiles WHERE lower(company_name) = ANY(%s))",
                (names,),
            )
            cur.execute("DELETE FROM profiles WHERE lower(company_name) = ANY(%s)", (names,))
    yield
    with get_connection() as conn:
        with conn.cursor() as cur:
            names = [name.lower() for name in _TEST_COMPANY_NAMES]
            cur.execute(
                "DELETE FROM scout_runs WHERE profile_id IN "
                "(SELECT id FROM profiles WHERE lower(company_name) = ANY(%s))",
                (names,),
            )
            cur.execute("DELETE FROM profiles WHERE lower(company_name) = ANY(%s)", (names,))


def test_get_active_service_lines_returns_seeded_rows():
    with get_connection() as conn:
        rows = queries.get_active_service_lines(conn)
    keys = {row["key"] for row in rows}
    assert keys == {"training", "consulting", "retainer", "certification", "other"}
    # ServiceLine.id is typed as str; psycopg deserializes Postgres uuid
    # columns as uuid.UUID objects, so this must be a real string, not a UUID.
    assert all(isinstance(row["id"], str) for row in rows)


def test_upsert_profile_updates_rather_than_duplicates():
    embedding = [0.1] * 1536
    profile = {
        "company_name": "Test Upsert Co",
        "note": "first run",
        "classification": "training",
        "brief": "First brief",
        "talking_points": ["Q1?"],
        "rationale": "First rationale",
        "reference_doc_ids": [],
        "low_confidence": False,
    }
    with get_connection() as conn:
        first_id = queries.upsert_profile(conn, profile, embedding)

    profile["note"] = "second run"
    profile["brief"] = "Updated brief"
    with get_connection() as conn:
        second_id = queries.upsert_profile(conn, profile, embedding)

    assert first_id == second_id

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM profiles WHERE lower(company_name) = lower(%s)", ("Test Upsert Co",))
            assert cur.fetchone()[0] == 1
            cur.execute("SELECT brief FROM profiles WHERE id = %s", (first_id,))
            assert cur.fetchone()[0] == "Updated brief"


def test_vector_search_orders_by_similarity():
    # Cosine distance (pgvector's `<=>`) only measures direction, not magnitude,
    # so uniform-constant vectors like [0.2]*1536 and [0.05]*1536 are perfectly
    # collinear (distance 0) regardless of scale. A seeded random vector avoids
    # ties against any other row's embedding, uniform or otherwise.
    rng = random.Random(1234)
    query_embedding = [rng.uniform(-1, 1) for _ in range(1536)]
    close_embedding = [v + 0.001 for v in query_embedding]
    far_embedding = [-v for v in query_embedding]

    with get_connection() as conn:
        queries.upsert_profile(
            conn,
            {
                "company_name": "Close Match Co",
                "note": None,
                "classification": "training",
                "brief": "b",
                "talking_points": ["Q?"],
                "rationale": "r",
                "reference_doc_ids": [],
                "low_confidence": False,
            },
            close_embedding,
        )
        queries.upsert_profile(
            conn,
            {
                "company_name": "Far Match Co",
                "note": None,
                "classification": "training",
                "brief": "b",
                "talking_points": ["Q?"],
                "rationale": "r",
                "reference_doc_ids": [],
                "low_confidence": False,
            },
            far_embedding,
        )
        results = queries.vector_search(conn, "profiles", query_embedding, top_k=2)

    assert results[0]["company_name"] == "Close Match Co"


def test_insert_scout_run_links_to_profile():
    with get_connection() as conn:
        profile_id = queries.upsert_profile(
            conn,
            {
                "company_name": "Scout Run Link Co",
                "note": None,
                "classification": "other",
                "brief": "b",
                "talking_points": ["Q?"],
                "rationale": "r",
                "reference_doc_ids": [],
                "low_confidence": True,
            },
            [0.05] * 1536,
        )
        run_id = queries.insert_scout_run(
            conn,
            {
                "profile_id": profile_id,
                "search_queries": ["Scout Run Link Co overview"],
                "search_results_raw": [[]],
                "attempts": 1,
                "duration_ms": 1200,
            },
        )
    assert run_id is not None
