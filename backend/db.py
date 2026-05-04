import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "hawkins.db"


def query_df(sql: str, params: tuple = ()):
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        return conn.execute(sql, list(params)).df()
    finally:
        conn.close()


def query_rows(sql: str, params: tuple = ()) -> list[dict]:
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        result = conn.execute(sql, list(params))
        cols = [d[0] for d in result.description]
        return [dict(zip(cols, row)) for row in result.fetchall()]
    finally:
        conn.close()
