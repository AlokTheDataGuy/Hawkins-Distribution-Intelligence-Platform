from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path
from db import query_rows

router = APIRouter()

GEOJSON_PATH = Path(__file__).parent.parent.parent / "data" / "india_states.geojson"


@router.get("/geojson")
def geojson():
    return FileResponse(GEOJSON_PATH, media_type="application/json")


@router.get("/states")
def states(metric: str = "revenue"):
    return query_rows("""
        SELECT state_code, state_name, region,
               active_dealers, service_centres,
               ROUND(total_revenue_inr / 1e7, 2) AS revenue_cr,
               total_units,
               population_cr, market_potential,
               latitude, longitude
        FROM v_state_summary
        ORDER BY state_name
    """)


@router.get("/dealers")
def dealers(region: str = "All"):
    conditions = ["d.is_active = 1", "d.latitude IS NOT NULL"]
    params: list = []
    if region != "All":
        conditions.append("d.region = ?")
        params.append(region)
    where_sql = "WHERE " + " AND ".join(conditions)
    return query_rows(f"""
        SELECT d.dealer_id, d.dealer_name, d.tier, d.region,
               d.state_name, d.city_name,
               d.latitude, d.longitude,
               d.monthly_capacity_units,
               ROUND(COALESCE(v.total_revenue_inr, 0) / 1e7, 3) AS revenue_cr
        FROM dim_dealers d
        LEFT JOIN v_dealer_performance v ON d.dealer_id = v.dealer_id
        {where_sql}
    """, tuple(params))


@router.get("/factories")
def factories():
    return query_rows("""
        SELECT factory_id, factory_name, city_name, state_code,
               latitude, longitude, monthly_capacity_units,
               primary_product_line, employees
        FROM dim_factories
    """)


@router.get("/service-centres")
def service_centres():
    return query_rows("""
        SELECT sc.centre_id, sc.city_name, ds.state_name,
               sc.latitude, sc.longitude,
               sc.monthly_capacity_requests
        FROM dim_service_centres sc
        JOIN dim_states ds ON sc.state_code = ds.state_code
        WHERE sc.latitude IS NOT NULL
    """)


@router.get("/whitespace")
def whitespace():
    rows = query_rows("""
        SELECT state_name, region,
               active_dealers,
               market_potential,
               ROUND(total_revenue_inr / 1e7, 2) AS revenue_cr
        FROM v_state_summary
        ORDER BY market_potential DESC
    """)
    if not rows:
        return []
    max_pot = max(r["market_potential"] for r in rows) or 1
    max_deal = max(r["active_dealers"] for r in rows) or 1
    for r in rows:
        r["opportunity_score"] = round(
            (r["market_potential"] / max_pot * 0.6) +
            (1 - r["active_dealers"] / max_deal) * 0.4, 3
        )
    return sorted(rows, key=lambda x: x["opportunity_score"], reverse=True)
