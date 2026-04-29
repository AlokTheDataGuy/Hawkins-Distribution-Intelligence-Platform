"""
Anomaly detection — two-layer approach:
  1. Z-score per dealer monthly revenue (univariate, explainable)
  2. Isolation Forest on multivariate dealer features

Usage:
    python scripts/ml/anomaly_detection.py
"""
import sqlite3
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "hawkins.db"
MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

CONTAMINATION = 0.02
Z_THRESHOLD = 3.0


# ---------- DATA LOADING ----------

def load_dealer_monthly(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("""
        SELECT
            fs.dealer_id,
            substr(fs.transaction_date, 1, 7) AS month,
            ROUND(SUM(fs.gross_amount), 2)     AS revenue,
            COUNT(*)                            AS txn_count,
            ROUND(AVG(fs.gross_amount), 2)     AS avg_basket
        FROM fact_sales fs
        GROUP BY fs.dealer_id, month
        ORDER BY fs.dealer_id, month
    """, conn)


def load_dealer_features(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("""
        SELECT
            vdp.dealer_id,
            vdp.total_revenue_inr           AS revenue,
            vdp.total_transactions          AS txn_count,
            vdp.avg_basket_inr              AS avg_basket,
            CAST(julianday('now') - julianday(vdp.last_txn_date) AS INTEGER)
                                            AS days_since_last_txn,
            dd.tier,
            dd.region
        FROM v_dealer_performance vdp
        JOIN dim_dealers dd ON vdp.dealer_id = dd.dealer_id
        WHERE dd.is_active = 1
    """, conn)


# ---------- Z-SCORE ANOMALIES ----------

def compute_zscore_anomalies(monthly: pd.DataFrame, threshold: float = Z_THRESHOLD) -> pd.DataFrame:
    stats = monthly.groupby("dealer_id")["revenue"].agg(["mean", "std"]).reset_index()
    stats.columns = ["dealer_id", "mean_rev", "std_rev"]
    stats["std_rev"] = stats["std_rev"].fillna(1).clip(lower=1)

    merged = monthly.merge(stats, on="dealer_id")
    merged["z_score"] = ((merged["revenue"] - merged["mean_rev"]) / merged["std_rev"]).round(3)
    anomalies = merged[merged["z_score"].abs() > threshold].copy()
    anomalies["anomaly_type"] = np.where(anomalies["z_score"] > 0, "Unusual Spike", "Unusual Drop")
    anomalies["severity"] = np.where(anomalies["z_score"].abs() > 5, "Critical", "Warning")
    anomalies["method"] = "Z-Score"
    return anomalies[["dealer_id", "month", "revenue", "mean_rev", "z_score", "anomaly_type", "severity", "method"]]


# ---------- ISOLATION FOREST ----------

FEATURE_COLS = ["revenue", "txn_count", "avg_basket", "days_since_last_txn"]


def train_isolation_forest(features: pd.DataFrame):
    X = features[FEATURE_COLS].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    iso = IsolationForest(
        n_estimators=200,
        contamination=CONTAMINATION,
        random_state=42,
        n_jobs=-1,
    )
    iso.fit(X_scaled)
    return iso, scaler


def detect_multivariate_anomalies(features: pd.DataFrame, iso, scaler) -> pd.DataFrame:
    X = features[FEATURE_COLS].fillna(0)
    X_scaled = scaler.transform(X)
    preds = iso.predict(X_scaled)          # -1 = anomaly, 1 = normal
    scores = iso.score_samples(X_scaled)   # lower = more anomalous

    result = features.copy()
    result["iso_prediction"] = preds
    result["anomaly_score"] = scores.round(4)
    result["is_anomaly"] = preds == -1
    result["severity"] = np.where(result["anomaly_score"] < result["anomaly_score"].quantile(0.01),
                                  "Critical", "Warning")
    result["method"] = "Isolation Forest"
    return result[result["is_anomaly"]]


def main():
    print("=== Anomaly Detection Training ===")
    conn = sqlite3.connect(DB_PATH)

    # Z-score on monthly series
    print("Computing Z-score anomalies on monthly dealer revenue…")
    monthly = load_dealer_monthly(conn)
    zscore_anomalies = compute_zscore_anomalies(monthly)
    print(f"  Found {len(zscore_anomalies)} monthly anomalies (|z| > {Z_THRESHOLD})")

    # Isolation Forest on per-dealer aggregate features
    print("Training Isolation Forest on dealer feature vectors…")
    features = load_dealer_features(conn)
    iso, scaler = train_isolation_forest(features)
    iso_anomalies = detect_multivariate_anomalies(features, iso, scaler)
    print(f"  Flagged {len(iso_anomalies)} dealers as anomalous (contamination={CONTAMINATION})")

    conn.close()

    # Save model
    payload = {"iso": iso, "scaler": scaler, "feature_cols": FEATURE_COLS}
    model_path = MODELS_DIR / "anomaly_dealer.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(payload, f)
    print(f"  Saved Isolation Forest → {model_path}")

    # Save pre-computed anomaly results for fast dashboard loading
    zscore_anomalies.to_parquet(MODELS_DIR / "zscore_anomalies.parquet", index=False)
    iso_anomalies.to_parquet(MODELS_DIR / "iso_anomalies.parquet", index=False)
    print("  Saved anomaly result caches → models/")
    print("Done.")


if __name__ == "__main__":
    main()

