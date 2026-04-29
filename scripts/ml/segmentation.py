"""
Dealer RFM segmentation + K-Means clustering.
Creates v_dealer_segments view in the database.

Usage:
    python scripts/ml/segmentation.py
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "hawkins.db"

SEGMENT_LABELS = {
    0: "Champions",
    1: "At-Risk",
    2: "Potential Loyalists",
    3: "New / Low-Value",
}


def load_rfm(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("""
        SELECT
            fs.dealer_id,
            CAST(julianday('now') - julianday(MAX(fs.transaction_date)) AS INTEGER) AS recency_days,
            COUNT(*) AS frequency,
            ROUND(SUM(fs.gross_amount), 2) AS monetary
        FROM fact_sales fs
        GROUP BY fs.dealer_id
    """, conn)


def rfm_score(rfm: pd.DataFrame) -> pd.DataFrame:
    rfm = rfm.copy()
    # Use rank(method='first') on all three to guarantee unique bin edges
    rfm["R_score"] = pd.qcut(rfm["recency_days"].rank(method="first"), q=4, labels=[4, 3, 2, 1]).astype(int)
    rfm["F_score"] = pd.qcut(rfm["frequency"].rank(method="first"), q=4, labels=[1, 2, 3, 4]).astype(int)
    rfm["M_score"] = pd.qcut(rfm["monetary"].rank(method="first"), q=4, labels=[1, 2, 3, 4]).astype(int)
    rfm["rfm_total"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]
    return rfm


def elbow_inertias(X_scaled: np.ndarray, k_range=range(2, 9)):
    return [KMeans(n_clusters=k, random_state=42, n_init=10).fit(X_scaled).inertia_ for k in k_range]


def cluster(rfm: pd.DataFrame, k: int = 4) -> pd.DataFrame:
    features = rfm[["recency_days", "frequency", "monetary"]].copy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)

    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    rfm = rfm.copy()
    rfm["cluster"] = km.fit_predict(X_scaled)

    # Label clusters by mean monetary descending → Champions=highest value
    cluster_monetary = rfm.groupby("cluster")["monetary"].mean().sort_values(ascending=False)
    label_map = {old: new for new, old in enumerate(cluster_monetary.index)}
    rfm["cluster"] = rfm["cluster"].map(label_map)
    rfm["segment"] = rfm["cluster"].map(SEGMENT_LABELS)
    return rfm


def write_segment_view(conn: sqlite3.Connection, rfm: pd.DataFrame):
    rfm_cols = rfm[["dealer_id", "recency_days", "frequency", "monetary",
                     "R_score", "F_score", "M_score", "rfm_total", "cluster", "segment"]]
    rfm_cols.to_sql("v_dealer_segments", conn, if_exists="replace", index=False)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_seg_dealer ON v_dealer_segments(dealer_id)")
    conn.commit()
    print(f"  Wrote {len(rfm_cols)} rows to v_dealer_segments")


def main():
    print("=== Dealer RFM Segmentation ===")
    conn = sqlite3.connect(DB_PATH)

    rfm = load_rfm(conn)
    print(f"Loaded RFM for {len(rfm)} dealers")

    rfm = rfm_score(rfm)
    rfm = cluster(rfm, k=4)

    segment_summary = rfm.groupby("segment").agg(
        dealers=("dealer_id", "count"),
        avg_recency=("recency_days", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
    ).reset_index()
    print("\nSegment summary:")
    print(segment_summary.to_string(index=False))

    write_segment_view(conn, rfm)
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()

