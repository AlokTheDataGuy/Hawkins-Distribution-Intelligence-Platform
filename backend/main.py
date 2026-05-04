import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from db import DBNotReady
from routers import executive, gis, dealers, forecasting, anomalies, service, competitive

app = FastAPI(title="HDIP API", version="1.0.0")


@app.exception_handler(DBNotReady)
async def db_not_ready_handler(request: Request, exc: DBNotReady):
    return JSONResponse(status_code=503, content={"detail": str(exc)})

_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(executive.router, prefix="/api/executive", tags=["executive"])
app.include_router(gis.router,       prefix="/api/gis",       tags=["gis"])
app.include_router(dealers.router,   prefix="/api/dealers",   tags=["dealers"])
app.include_router(forecasting.router, prefix="/api/forecasting", tags=["forecasting"])
app.include_router(anomalies.router, prefix="/api/anomalies", tags=["anomalies"])
app.include_router(service.router,   prefix="/api/service",   tags=["service"])
app.include_router(competitive.router, prefix="/api/competitive", tags=["competitive"])


@app.get("/api/kpis")
def get_kpis():
    from db import query_rows
    rows = query_rows("""
        SELECT COUNT(*) AS transactions,
               SUM(quantity) AS units_sold,
               ROUND(SUM(gross_amount), 0) AS revenue_inr,
               COUNT(DISTINCT dealer_id) AS active_dealers,
               COUNT(DISTINCT product_id) AS skus_sold
        FROM fact_sales
    """)
    r = rows[0]
    return {
        "transactions":   r["transactions"],
        "units_sold":     r["units_sold"],
        "revenue_cr":     round(r["revenue_inr"] / 1e7, 1),
        "active_dealers": r["active_dealers"],
        "skus_sold":      r["skus_sold"],
    }
