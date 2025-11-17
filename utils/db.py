import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Sequence, Any, Optional

import psycopg2
from psycopg2.extras import execute_values
import logging


@contextmanager
def get_connection():
    conn = psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        dbname=os.getenv("PGDATABASE", "gw2tp"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "1234"),
    )
    try:
        yield conn
    finally:
        conn.close()


def load_sql(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"SQL file not found: {p}")

    return p.read_text(encoding="utf-8")


def execute_values_batch(
    sql: str,
    rows: Iterable[Sequence[Any]],
    page_size: int = 200,
    logger: Optional[logging.Logger] = None,
):
    rows = list(rows)
    if not rows:
        return

    with get_connection() as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SET LOCAL statement_timeout = '30s'")
                execute_values(cur, sql, rows, page_size=page_size)

    if logger:
        logger.debug(f"execute_values_batch: executed {len(rows)} rows.")
