import sqlite3
from pathlib import Path
from functools import lru_cache
import pandas as pd

DB_PATH = Path(__file__).parent.parent / "data" / "hawkins.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def query_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def query_rows(sql: str, params: tuple = ()) -> list[dict]:
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
