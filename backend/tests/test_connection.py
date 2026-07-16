import os

import pytest

from app.db.connection import get_connection


def test_get_connection_raises_without_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        with get_connection():
            pass


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="requires a live DATABASE_URL")
def test_get_connection_connects_to_real_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone() == (1,)
