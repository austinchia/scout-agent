import os
from contextlib import contextmanager
from typing import Iterator

import psycopg


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    conn = psycopg.connect(database_url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
