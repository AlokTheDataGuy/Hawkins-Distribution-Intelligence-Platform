import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "hawkins.db"
MIN_DB_SIZE = 50 * 1024 * 1024  # 50 MB


class DBNotReady(Exception):
    pass


def _connect():
    if not DB_PATH.exists() or DB_PATH.stat().st_size < MIN_DB_SIZE:
        raise DBNotReady("Database is still initializing (~5 min on first boot). Please refresh shortly.")
    return duckdb.connect(str(DB_PATH), read_only=True)


def query_df(sql: str, params: tuple = ()):
    conn = _connect()
    try:
        return conn.execute(sql, list(params)).df()
    finally:
        conn.close()


def query_rows(sql: str, params: tuple = ()) -> list[dict]:
    conn = _connect()
    try:
        result = conn.execute(sql, list(params))
        cols = [d[0] for d in result.description]
        return [dict(zip(cols, row)) for row in result.fetchall()]
    finally:
        conn.close()
