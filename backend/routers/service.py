from fastapi import APIRouter
from db import query_rows

router = APIRouter()

BASE_QUERY = """
    SELECT sr.request_id, sr.issue_type, sr.severity, sr.status,
           substr(sr.request_date, 1, 7) AS month,
           sr.resolution_days, sr.cost_inr, sr.is_under_warranty,
           p.product_name, p.category, p.sub_category,
           ds.state_name, ds.region
    FROM fact_service_requests sr
    JOIN dim_products p          ON sr.product_id  = p.product_id
    JOIN dim_service_centres sc  ON sr.centre_id   = sc.centre_id
    JOIN dim_states ds           ON sc.state_code  = ds.state_code
"""


@router.get("/kpis")
def kpis():
    rows = query_rows("""
        SELECT COUNT(*) AS total_requests,
               SUM(CASE WHEN severity='Critical' THEN 1 ELSE 0 END) AS critical,
               ROUND(AVG(resolution_days), 1) AS avg_resolution_days,
               ROUND(SUM(CASE WHEN is_under_warranty=0 THEN cost_inr ELSE 0 END) / 1e7, 2) AS warranty_cost_cr
        FROM fact_service_requests
    """)
    return rows[0]


@router.get("/monthly-trend")
def monthly_trend():
    return query_rows("""
        SELECT substr(request_date, 1, 7) AS month,
               severity,
               COUNT(*) AS count
        FROM fact_service_requests
        GROUP BY month, severity
        ORDER BY month
    """)


@router.get("/issue-breakdown")
def issue_breakdown():
    return query_rows("""
        SELECT issue_type, COUNT(*) AS count
        FROM fact_service_requests
        GROUP BY issue_type
        ORDER BY count DESC
    """)


@router.get("/sku-heatmap")
def sku_heatmap():
    rows = query_rows("""
        SELECT p.product_name, sr.issue_type, COUNT(*) AS count
        FROM fact_service_requests sr
        JOIN dim_products p ON sr.product_id = p.product_id
        WHERE p.product_name IN (
            SELECT p2.product_name FROM fact_service_requests sr2
            JOIN dim_products p2 ON sr2.product_id = p2.product_id
            GROUP BY p2.product_name ORDER BY COUNT(*) DESC LIMIT 15
        )
        GROUP BY p.product_name, sr.issue_type
        ORDER BY p.product_name, count DESC
    """)
    return rows


@router.get("/resolution-times")
def resolution_times():
    return query_rows("""
        SELECT severity, category,
               ROUND(AVG(resolution_days), 1) AS avg_days,
               ROUND(MIN(resolution_days), 1) AS min_days,
               ROUND(MAX(resolution_days), 1) AS max_days,
               COUNT(*) AS count
        FROM fact_service_requests sr
        JOIN dim_products p ON sr.product_id = p.product_id
        GROUP BY severity, category
        ORDER BY severity, avg_days DESC
    """)


@router.get("/quality-risk")
def quality_risk():
    return query_rows("""
        SELECT p.product_name, p.category,
               COUNT(sr.request_id) AS total_claims,
               SUM(CASE WHEN sr.severity='Critical' THEN 1 ELSE 0 END) AS critical_claims,
               ROUND(AVG(sr.resolution_days), 1) AS avg_resolution_days,
               ROUND(COUNT(sr.request_id) * 1000.0 /
                     NULLIF((SELECT SUM(quantity) FROM fact_sales WHERE product_id=p.product_id), 0), 2) AS claim_rate_per_1k
        FROM fact_service_requests sr
        JOIN dim_products p ON sr.product_id = p.product_id
        GROUP BY p.product_id
        ORDER BY claim_rate_per_1k DESC
        LIMIT 20
    """)


@router.get("/state-load")
def state_load():
    return query_rows("""
        SELECT ds.state_name,
               COUNT(sr.request_id) AS total_requests,
               SUM(CASE WHEN sr.severity='Critical' THEN 1 ELSE 0 END) AS critical_count
        FROM fact_service_requests sr
        JOIN dim_service_centres sc ON sr.centre_id = sc.centre_id
        JOIN dim_states ds ON sc.state_code = ds.state_code
        GROUP BY ds.state_name
        ORDER BY total_requests DESC
        LIMIT 20
    """)
