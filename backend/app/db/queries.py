import json
import uuid
from typing import Any

import psycopg


def _to_pgvector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(str(x) for x in embedding) + "]"


def get_active_service_lines(conn: psycopg.Connection) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, key, label, description FROM service_lines WHERE active = TRUE ORDER BY key"
        )
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]


def vector_search(
    conn: psycopg.Connection,
    table: str,
    embedding: list[float],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    if table not in ("profiles", "reference_docs"):
        raise ValueError(f"unsupported table for vector_search: {table}")
    vector_literal = _to_pgvector_literal(embedding)
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT * FROM {table} WHERE embedding IS NOT NULL "
            f"ORDER BY embedding <=> %s::vector LIMIT %s",
            (vector_literal, top_k),
        )
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]


def upsert_profile(conn: psycopg.Connection, profile: dict[str, Any], embedding: list[float]) -> uuid.UUID:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO profiles (
                company_name, note, classification, brief, talking_points,
                rationale, reference_doc_ids, low_confidence, embedding
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
            ON CONFLICT (lower(company_name)) DO UPDATE SET
                note = EXCLUDED.note,
                classification = EXCLUDED.classification,
                brief = EXCLUDED.brief,
                talking_points = EXCLUDED.talking_points,
                rationale = EXCLUDED.rationale,
                reference_doc_ids = EXCLUDED.reference_doc_ids,
                low_confidence = EXCLUDED.low_confidence,
                embedding = EXCLUDED.embedding,
                created_at = now()
            RETURNING id
            """,
            (
                profile["company_name"],
                profile.get("note"),
                profile["classification"],
                profile["brief"],
                json.dumps(profile["talking_points"]),
                profile["rationale"],
                json.dumps(profile["reference_doc_ids"]),
                profile["low_confidence"],
                _to_pgvector_literal(embedding),
            ),
        )
        return cur.fetchone()[0]


def insert_scout_run(conn: psycopg.Connection, run: dict[str, Any]) -> uuid.UUID:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO scout_runs (
                profile_id, search_queries, search_results_raw, attempts, duration_ms
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                run["profile_id"],
                json.dumps(run["search_queries"]),
                json.dumps(run["search_results_raw"]),
                run["attempts"],
                run["duration_ms"],
            ),
        )
        return cur.fetchone()[0]
