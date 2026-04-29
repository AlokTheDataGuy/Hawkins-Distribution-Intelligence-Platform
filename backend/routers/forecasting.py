import json
import pickle
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter()

MODELS_DIR  = Path(__file__).parent.parent.parent / "models"
INDEX_PATH  = MODELS_DIR / "forecast_index.json"


@router.get("/skus")
def list_skus():
    if not INDEX_PATH.exists():
        return []
    with open(INDEX_PATH) as f:
        idx = json.load(f)
    # idx is a list of {product_id, product_name, total_revenue}
    return [{"product_id": item["product_id"], "product_name": item["product_name"]} for item in idx]


@router.get("/{product_id}")
def get_forecast(product_id: str, horizon: int = 6, boost_pct: float = 0.0):
    pkl_path = MODELS_DIR / f"forecast_{product_id}.pkl"
    if not pkl_path.exists():
        raise HTTPException(404, "Model not found")

    with open(pkl_path, "rb") as f:
        payload = pickle.load(f)

    series     = payload["series"]
    fc12       = payload["forecast_12"]
    ci         = payload["conf_int"]
    mape       = payload.get("mape", None)

    # Historical
    historical = [
        {"month": str(idx)[:7], "revenue_lakh": round(float(v) / 1e5, 2)}
        for idx, v in series.items()
    ]

    # Detect CI column names (statsmodels uses 'lower X' / 'upper X')
    ci_lo_col = ci.columns[0]
    ci_hi_col = ci.columns[1]

    # Forecast (apply boost)
    mult = 1 + boost_pct / 100
    forecast = []
    for i, (idx, v) in enumerate(fc12.items()):
        if i >= horizon:
            break
        lo = float(ci.iloc[i][ci_lo_col]) * mult
        hi = float(ci.iloc[i][ci_hi_col]) * mult
        forecast.append({
            "month":    str(idx)[:7],
            "forecast": round(float(v) * mult / 1e5, 2),
            "ci_low":   round(lo / 1e5, 2),
            "ci_high":  round(hi / 1e5, 2),
        })

    recent_avg = round(float(series.iloc[-6:].mean()) / 1e5, 2) if len(series) >= 6 else None
    fc_avg     = round(float(fc12.iloc[:3].mean()) / 1e5, 2) if len(fc12) >= 3 else None
    trend_pct  = round((fc_avg - recent_avg) / recent_avg * 100, 1) if recent_avg else None

    return {
        "product_id":   product_id,
        "product_name": payload.get("product_name", product_id),
        "mape":         round(float(mape), 1) if mape is not None else None,
        "recent_avg_lakh": recent_avg,
        "trend_pct":    trend_pct,
        "historical":   historical,
        "forecast":     forecast,
    }
