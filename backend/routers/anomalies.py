from pathlib import Path
from fastapi import APIRouter
from db import query_rows
import pandas as pd

router   = APIRouter()
MODELS   = Path(__file__).parent.parent.parent / "models"


def _load_parquet(name: str) -> list[dict]:
    p = MODELS / name
    if not p.exists():
        return []
    df = pd.read_parquet(p)
    return df.to_dict(orient="records")


@router.get("/dormancy")
def dormancy():
    rows = query_rows("""
        SELECT dd.dealer_id, dd.dealer_name, dd.tier, dd.region, dd.state_name,
               MAX(fs.transaction_date) AS last_txn,
               CAST(julianday('now') - julianday(MAX(fs.transaction_date)) AS INTEGER) AS days_inactive
        FROM dim_dealers dd
        JOIN fact_sales fs ON fs.dealer_id = dd.dealer_id
        WHERE dd.is_active = 1 AND dd.tier IN ('A', 'B')
        GROUP BY dd.dealer_id
        HAVING days_inactive > 30
        ORDER BY days_inactive DESC
    """)
    for r in rows:
        r["severity"] = "Critical" if r["days_inactive"] > 60 else "Warning"
    return rows


@router.get("/price-errors")
def price_errors():
    return query_rows("""
        SELECT fs.dealer_id, dd.dealer_name, dd.tier,
               fs.product_id, p.product_name,
               ROUND(p.unit_price, 0) AS list_price,
               ROUND(fs.unit_price, 0) AS actual_price,
               ROUND((fs.unit_price - p.unit_price) / p.unit_price * 100, 1) AS pct_diff,
               fs.transaction_date
        FROM fact_sales fs
        JOIN dim_dealers dd  ON fs.dealer_id  = dd.dealer_id
        JOIN dim_products p  ON fs.product_id = p.product_id
        WHERE ABS((fs.unit_price - p.unit_price) / p.unit_price) > 0.20
        ORDER BY ABS((fs.unit_price - p.unit_price) / p.unit_price) DESC
        LIMIT 100
    """)


@router.get("/zscore")
def zscore(severity: str = "All"):
    rows = _load_parquet("zscore_anomalies.parquet")
    if severity != "All":
        rows = [r for r in rows if r.get("severity") == severity]
    return rows[:200]


@router.get("/isolation-forest")
def isolation_forest(severity: str = "All"):
    rows = _load_parquet("iso_anomalies.parquet")
    if severity != "All":
        rows = [r for r in rows if r.get("severity") == severity]
    return rows[:200]


@router.get("/heatmap")
def heatmap():
    rows = _load_parquet("zscore_anomalies.parquet")
    if not rows:
        return {"states": [], "months": [], "matrix": {}}

    df = pd.DataFrame(rows)
    if "state_name" not in df.columns or "month" not in df.columns:
        return {"states": [], "months": [], "matrix": {}}

    pivot = df.groupby(["state_name", "month"]).size().unstack(fill_value=0)
    states  = pivot.index.tolist()
    months  = [str(m)[:7] for m in pivot.columns.tolist()]
    matrix  = {str(s): pivot.loc[s].tolist() for s in states}
    return {"states": states, "months": months, "matrix": matrix}
