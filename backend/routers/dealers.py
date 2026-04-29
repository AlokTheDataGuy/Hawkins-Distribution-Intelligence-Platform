from fastapi import APIRouter
from db import query_rows
import pandas as pd

router = APIRouter()


def _load_scored(tiers: list[str], regions: list[str]) -> list[dict]:
    tier_ph  = ",".join("?" * len(tiers))
    reg_ph   = ",".join("?" * len(regions))
    rows = query_rows(f"""
        SELECT vdp.dealer_id, vdp.dealer_name, vdp.tier, vdp.region,
               vdp.state_name, vdp.city_name,
               vdp.total_transactions, vdp.total_units,
               ROUND(vdp.total_revenue_inr / 1e5, 2) AS revenue_lakh,
               ROUND(vdp.avg_basket_inr, 0) AS avg_basket,
               dd.monthly_capacity_units, dd.years_active
        FROM v_dealer_performance vdp
        JOIN dim_dealers dd ON vdp.dealer_id = dd.dealer_id
        WHERE dd.is_active = 1
          AND vdp.tier IN ({tier_ph})
          AND vdp.region IN ({reg_ph})
    """, tuple(tiers + regions))

    df = pd.DataFrame(rows)
    if df.empty:
        return []

    for col, w in [("revenue_lakh", 0.60), ("avg_basket", 0.20), ("total_transactions", 0.20)]:
        df[f"_pct_{col}"] = df.groupby("tier")[col].rank(pct=True)
    df["score"] = (
        df["_pct_revenue_lakh"] * 0.60 +
        df["_pct_avg_basket"]   * 0.20 +
        df["_pct_total_transactions"] * 0.20
    ) * 100
    df["score"] = df["score"].round(1)

    drop = [c for c in df.columns if c.startswith("_pct_")]
    df = df.drop(columns=drop)
    return df.to_dict(orient="records")


@router.get("/scored")
def scored(
    tiers: str = "A,B,C",
    regions: str = "North,South,East,West,Central,Northeast"
):
    t = [x.strip() for x in tiers.split(",")]
    r = [x.strip() for x in regions.split(",")]
    return _load_scored(t, r)


@router.get("/movers")
def movers():
    rows = query_rows("""
        SELECT fs.dealer_id, dd.dealer_name, dd.tier, dd.region,
               ROUND(SUM(CASE
                   WHEN fs.transaction_date >= date('now', '-90 days')
                   THEN fs.gross_amount ELSE 0 END) / 1e5, 2) AS rev_last90,
               ROUND(SUM(CASE
                   WHEN fs.transaction_date >= date('now', '-180 days')
                    AND fs.transaction_date <  date('now', '-90 days')
                   THEN fs.gross_amount ELSE 0 END) / 1e5, 2) AS rev_prior90
        FROM fact_sales fs
        JOIN dim_dealers dd ON fs.dealer_id = dd.dealer_id
        GROUP BY fs.dealer_id
        HAVING rev_prior90 > 0
    """)
    result = []
    for r in rows:
        r["growth_ratio"] = round(r["rev_last90"] / r["rev_prior90"], 3) if r["rev_prior90"] else None
        result.append(r)
    return result


@router.get("/cohorts")
def cohorts():
    return query_rows("""
        SELECT CAST(strftime('%Y', dd.onboarded_date) AS INTEGER) AS onboard_year,
               dd.tier,
               COUNT(dd.dealer_id) AS dealer_count,
               ROUND(AVG(COALESCE(vdp.total_revenue_inr, 0)) / 1e5, 2) AS avg_revenue_lakh
        FROM dim_dealers dd
        LEFT JOIN v_dealer_performance vdp ON dd.dealer_id = vdp.dealer_id
        WHERE dd.is_active = 1 AND dd.onboarded_date IS NOT NULL
        GROUP BY onboard_year, dd.tier
        ORDER BY onboard_year, dd.tier
    """)


@router.get("/{dealer_id}/monthly")
def dealer_monthly(dealer_id: str):
    return query_rows("""
        SELECT substr(transaction_date, 1, 7) AS month,
               ROUND(SUM(gross_amount) / 1e5, 2) AS revenue_lakh,
               COUNT(*) AS transactions
        FROM fact_sales
        WHERE dealer_id = ?
        GROUP BY month
        ORDER BY month
    """, (dealer_id,))


@router.get("/{dealer_id}/top-skus")
def dealer_top_skus(dealer_id: str):
    return query_rows("""
        SELECT p.product_name, p.category,
               ROUND(SUM(fs.gross_amount) / 1e5, 2) AS revenue_lakh
        FROM fact_sales fs
        JOIN dim_products p ON fs.product_id = p.product_id
        WHERE fs.dealer_id = ?
        GROUP BY fs.product_id
        ORDER BY revenue_lakh DESC
        LIMIT 10
    """, (dealer_id,))
