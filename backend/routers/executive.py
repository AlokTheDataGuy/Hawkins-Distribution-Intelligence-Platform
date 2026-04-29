from fastapi import APIRouter
from db import query_rows

router = APIRouter()


@router.get("/monthly-revenue")
def monthly_revenue():
    return query_rows("""
        SELECT substr(transaction_date, 1, 7) AS month,
               COUNT(*) AS transactions,
               SUM(quantity) AS units,
               ROUND(SUM(gross_amount) / 1e7, 3) AS revenue_cr
        FROM fact_sales
        GROUP BY month
        ORDER BY month
    """)


@router.get("/region-breakdown")
def region_breakdown():
    return query_rows("""
        SELECT region,
               COUNT(DISTINCT dealer_id) AS dealers,
               COUNT(*) AS transactions,
               ROUND(SUM(gross_amount) / 1e7, 2) AS revenue_cr
        FROM v_sales_enriched
        GROUP BY region
        ORDER BY revenue_cr DESC
    """)


@router.get("/top-products")
def top_products(limit: int = 10):
    return query_rows(f"""
        SELECT product_id, product_name, category,
               transactions, units_sold,
               ROUND(revenue_inr / 1e7, 2) AS revenue_cr
        FROM v_product_performance
        ORDER BY revenue_inr DESC
        LIMIT {limit}
    """)


@router.get("/state-summary")
def state_summary(limit: int = 10):
    rows = query_rows("""
        SELECT state_name, region,
               active_dealers, service_centres,
               ROUND(total_revenue_inr / 1e7, 2) AS revenue_cr,
               total_units
        FROM v_state_summary
        ORDER BY total_revenue_inr DESC
    """)
    return rows[:limit]
