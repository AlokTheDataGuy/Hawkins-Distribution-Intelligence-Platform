from fastapi import APIRouter
from db import query_rows

router = APIRouter()


@router.get("/kpis")
def kpis():
    rows = query_rows("""
        SELECT COUNT(DISTINCT competitor) AS competitors_tracked,
               COUNT(DISTINCT product_id) AS skus_tracked,
               ROUND(AVG(price_gap_pct), 1) AS avg_gap_pct
        FROM fact_competitor_pricing
    """)
    r = rows[0]
    posture = "Value Leader" if (r["avg_gap_pct"] or 0) > 0 else "Premium"
    return {**r, "posture": posture}


@router.get("/gap-trend")
def gap_trend(competitors: str = "All", categories: str = "All"):
    comp_filter = ""
    cat_filter  = ""
    params: list = []

    if competitors != "All":
        cl = competitors.split(",")
        comp_filter = "AND cp.competitor IN (" + ",".join("?" * len(cl)) + ")"
        params.extend(cl)
    if categories != "All":
        cat_list = categories.split(",")
        cat_filter = "AND p.category IN (" + ",".join("?" * len(cat_list)) + ")"
        params.extend(cat_list)

    return query_rows(f"""
        SELECT substr(cp.snapshot_date, 1, 7) AS month,
               cp.competitor,
               ROUND(AVG(cp.price_gap_pct), 2) AS avg_gap_pct
        FROM fact_competitor_pricing cp
        JOIN dim_products p ON cp.product_id = p.product_id
        WHERE 1=1 {comp_filter} {cat_filter}
        GROUP BY month, cp.competitor
        ORDER BY month
    """, tuple(params))


@router.get("/posture-summary")
def posture_summary():
    rows = query_rows("""
        SELECT competitor,
               ROUND(AVG(price_gap_pct), 2) AS avg_gap_pct,
               ROUND(SUM(CASE WHEN hawkins_price < competitor_price THEN 1.0 ELSE 0 END)
                     / COUNT(*) * 100, 1) AS pct_hawkins_cheaper
        FROM fact_competitor_pricing
        GROUP BY competitor
        ORDER BY avg_gap_pct DESC
    """)
    for r in rows:
        g = r["avg_gap_pct"] or 0
        if g < -5:
            r["posture"] = "Costlier"
        elif g > 5:
            r["posture"] = "Value Leader"
        else:
            r["posture"] = "Parity"
    return rows


@router.get("/sku-heatmap")
def sku_heatmap():
    return query_rows("""
        SELECT p.product_name, cp.competitor,
               ROUND(AVG(cp.price_gap_pct), 1) AS avg_gap_pct
        FROM fact_competitor_pricing cp
        JOIN dim_products p ON cp.product_id = p.product_id
        WHERE p.product_name IN (
            SELECT p2.product_name FROM fact_competitor_pricing cp2
            JOIN dim_products p2 ON cp2.product_id = p2.product_id
            GROUP BY p2.product_name
            ORDER BY AVG(ABS(cp2.price_gap_pct)) DESC LIMIT 20
        )
        GROUP BY p.product_name, cp.competitor
        ORDER BY p.product_name
    """)


@router.get("/vulnerable-skus")
def vulnerable_skus():
    rows = query_rows("""
        SELECT p.product_name, cp.competitor,
               ROUND(AVG(CASE WHEN cp.snapshot_date < date('now', '-90 days')
                              THEN cp.price_gap_pct END), 1) AS older_gap,
               ROUND(AVG(CASE WHEN cp.snapshot_date >= date('now', '-90 days')
                              THEN cp.price_gap_pct END), 1) AS recent_gap
        FROM fact_competitor_pricing cp
        JOIN dim_products p ON cp.product_id = p.product_id
        GROUP BY p.product_name, cp.competitor
        HAVING recent_gap IS NOT NULL AND older_gap IS NOT NULL
    """)
    result = []
    for r in rows:
        r["gap_change"] = round((r["recent_gap"] or 0) - (r["older_gap"] or 0), 1)
        if r["gap_change"] < -2:
            result.append(r)
    return sorted(result, key=lambda x: x["gap_change"])[:20]
