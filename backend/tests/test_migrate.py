import os

import pytest

from app.db.connection import get_connection
from app.db.migrate import run_migrations

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="requires a live DATABASE_URL")


def test_run_migrations_creates_tables_and_seeds_service_lines():
    run_migrations()
    run_migrations()  # idempotency: running twice must not error or duplicate

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' "
                "AND table_name IN ('profiles', 'reference_docs', 'scout_runs', 'service_lines')"
            )
            tables = {row[0] for row in cur.fetchall()}
            assert tables == {"profiles", "reference_docs", "scout_runs", "service_lines"}

            cur.execute("SELECT count(*) FROM service_lines")
            assert cur.fetchone()[0] == 5
