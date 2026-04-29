"""
SARIMA demand forecasting — trains one model per top-15 SKU.
Saves each model to models/forecast_{product_id}.pkl

Usage:
    python scripts/ml/train_forecasts.py
"""
import sqlite3
import pickle
import warnings
import json
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings("ignore")

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "hawkins.db"
MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

SARIMA_ORDER = (1, 1, 1)
SARIMA_SEASONAL = (1, 1, 1, 12)
TEST_MONTHS = 6


def load_monthly_series(conn, product_id: str) -> pd.Series:
    sql = """
        SELECT substr(transaction_date, 1, 7) AS month,
               ROUND(SUM(gross_amount), 2) AS revenue_inr
        FROM fact_sales
        WHERE product_id = ?
        GROUP BY month
        ORDER BY month
    """
    df = pd.read_sql_query(sql, conn, params=(product_id,))
    if df.empty:
        return pd.Series(dtype=float)
    df["month"] = pd.to_datetime(df["month"] + "-01")
    df = df.set_index("month").asfreq("MS")
    df["revenue_inr"] = df["revenue_inr"].fillna(0)
    return df["revenue_inr"]


def fit_sarima(series: pd.Series):
    model = SARIMAX(
        series,
        order=SARIMA_ORDER,
        seasonal_order=SARIMA_SEASONAL,
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    result = model.fit(disp=False, maxiter=200)
    return result


def evaluate_smape(actual, predicted) -> float:
    """Symmetric MAPE — bounded 0-200%, handles near-zero values gracefully."""
    denom = (np.abs(actual) + np.abs(predicted)) / 2
    mask = denom > 0
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.abs(actual[mask] - predicted[mask]) / denom[mask]) * 100)


def fit_best(train: pd.Series):
    """Try SARIMA first; fall back to simpler ARIMA if it diverges."""
    try:
        result = fit_sarima(train)
        return result, SARIMA_ORDER, SARIMA_SEASONAL
    except Exception:
        pass
    # Fallback: ARIMA(1,1,1) no seasonal
    from statsmodels.tsa.arima.model import ARIMA
    result = ARIMA(train, order=(1, 1, 1)).fit()
    return result, (1, 1, 1), (0, 0, 0, 0)


def train_and_save(product_id: str, product_name: str, series: pd.Series):
    if len(series) < 18:
        print(f"  Skipping {product_id}: only {len(series)} months of data")
        return None

    train = series.iloc[:-TEST_MONTHS]
    test = series.iloc[-TEST_MONTHS:]

    try:
        result, order_used, seasonal_used = fit_best(train)
        forecast_test = result.forecast(steps=TEST_MONTHS)
        smape = evaluate_smape(test.values, forecast_test.values)

        # Refit on full series for production forecasting
        try:
            result_full = fit_sarima(series)
        except Exception:
            from statsmodels.tsa.arima.model import ARIMA
            result_full = ARIMA(series, order=(1, 1, 1)).fit()

        forecast_12 = result_full.forecast(steps=12)
        conf_int = result_full.get_forecast(steps=12).conf_int()

        payload = {
            "product_id": product_id,
            "product_name": product_name,
            "series": series,
            "result": result_full,
            "forecast_12": forecast_12,
            "conf_int": conf_int,
            "mape": smape,       # stored as "mape" key for dashboard compatibility
            "order": order_used,
            "seasonal_order": seasonal_used,
        }

        out_path = MODELS_DIR / f"forecast_{product_id}.pkl"
        with open(out_path, "wb") as f:
            pickle.dump(payload, f)

        print(f"  ✓ {product_id} ({product_name[:30]}) | sMAPE={smape:.1f}% | saved {out_path.name}")
        return smape

    except Exception as exc:
        print(f"  ✗ {product_id}: {exc}")
        return None


def main():
    print("=== SARIMA Forecast Training ===")
    conn = sqlite3.connect(DB_PATH)

    # Top 15 SKUs by total revenue
    top_skus = pd.read_sql_query("""
        SELECT fs.product_id, p.product_name,
               ROUND(SUM(fs.gross_amount), 2) AS total_revenue
        FROM fact_sales fs
        JOIN dim_products p ON fs.product_id = p.product_id
        GROUP BY fs.product_id, p.product_name
        ORDER BY total_revenue DESC
        LIMIT 15
    """, conn)

    print(f"Training on {len(top_skus)} top SKUs…")
    mapes = []
    for _, row in top_skus.iterrows():
        series = load_monthly_series(conn, row["product_id"])
        mape = train_and_save(row["product_id"], row["product_name"], series)
        if mape is not None:
            mapes.append(mape)

    conn.close()

    if mapes:
        print(f"\nDone. Models saved to {MODELS_DIR}")
        print(f"Avg sMAPE across {len(mapes)} SKUs: {np.mean(mapes):.1f}%")

    # Save index of trained models for dashboard
    index = top_skus.to_dict(orient="records")
    with open(MODELS_DIR / "forecast_index.json", "w") as f:
        json.dump(index, f, indent=2)
    print("Saved forecast_index.json")


if __name__ == "__main__":
    main()

