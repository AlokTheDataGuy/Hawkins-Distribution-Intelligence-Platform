"""
ETL Pipeline: Loads all CSV dimensions and facts into a single SQLite database.

This database (data/hawkins.db) is the SINGLE SOURCE OF TRUTH for:
- The Streamlit dashboard
- The Power BI report
- All ML model training

Why SQLite for an "in-house" Hawkins-style system?
  - Zero-config (matches "in-house" ethos vs heavy ERP)
  - Power BI connects natively
  - Embeds with Streamlit Cloud deployment
  - Can be migrated to PostgreSQL/SQL Server later for production

The pipeline also creates SQL VIEWS for common analytical queries.
"""
import pandas as pd
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RAW  = ROOT / "data" / "raw"
DB   = ROOT / "data" / "hawkins.db"


# Table loading order matters for FKs (dimensions first, then facts)
TABLES = [
    # Dimensions
    ("dim_products",          "dim_products.csv"),
    ("dim_states",            "dim_states.csv"),
    ("dim_cities",            "dim_cities.csv"),
    ("dim_factories",         "dim_factories.csv"),
    ("dim_dealers",           "dim_dealers.csv"),
    ("dim_service_centres",   "dim_service_centres.csv"),
    ("dim_new_launches",      "dim_new_launches.csv"),
    # Facts
    ("fact_sales",            "fact_sales.csv"),
    ("fact_inventory",        "fact_inventory.csv"),
    ("fact_service_requests", "fact_service_requests.csv"),
    ("fact_competitor_pricing","fact_competitor_pricing.csv"),
]

# Tables too large to load into RAM at once on low-memory hosts (e.g. Render free 512MB)
CHUNKED_TABLES = {"fact_sales"}
CHUNK_SIZE = 50_000

# Indexes — critical for dashboard query performance
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_sales_date    ON fact_sales(transaction_date);",
    "CREATE INDEX IF NOT EXISTS idx_sales_dealer  ON fact_sales(dealer_id);",
    "CREATE INDEX IF NOT EXISTS idx_sales_product ON fact_sales(product_id);",
    "CREATE INDEX IF NOT EXISTS idx_sales_dealer_date ON fact_sales(dealer_id, transaction_date);",
    "CREATE INDEX IF NOT EXISTS idx_inv_date      ON fact_inventory(snapshot_date);",
    "CREATE INDEX IF NOT EXISTS idx_inv_factory   ON fact_inventory(factory_id);",
    "CREATE INDEX IF NOT EXISTS idx_svc_date      ON fact_service_requests(request_date);",
    "CREATE INDEX IF NOT EXISTS idx_svc_centre    ON fact_service_requests(centre_id);",
    "CREATE INDEX IF NOT EXISTS idx_dealers_state ON dim_dealers(state_code);",
    "CREATE INDEX IF NOT EXISTS idx_dealers_tier  ON dim_dealers(tier);",
]

# Analytical views — expose common joins as if they were tables
VIEWS = {
    "v_sales_enriched": """
        CREATE VIEW v_sales_enriched AS
        SELECT
            s.transaction_id,
            s.transaction_date,
            s.dealer_id,
            d.dealer_name,
            d.tier            AS dealer_tier,
            d.region,
            d.state_name,
            d.state_code,
            d.city_name,
            d.is_urban,
            d.latitude        AS dealer_lat,
            d.longitude       AS dealer_lng,
            s.product_id,
            p.product_name,
            p.category,
            p.sub_category,
            p.material,
            p.tier            AS product_tier,
            p.is_induction,
            s.quantity,
            s.unit_price,
            s.gross_amount,
            s.discount_pct,
            s.channel
        FROM fact_sales s
        JOIN dim_dealers  d ON s.dealer_id  = d.dealer_id
        JOIN dim_products p ON s.product_id = p.product_id;
    """,
    "v_monthly_revenue_by_state": """
        CREATE VIEW v_monthly_revenue_by_state AS
        SELECT
            substr(transaction_date, 1, 7) AS year_month,
            state_code,
            state_name,
            region,
            COUNT(*)             AS transactions,
            SUM(quantity)        AS units_sold,
            ROUND(SUM(gross_amount), 2) AS revenue_inr
        FROM v_sales_enriched
        GROUP BY year_month, state_code, state_name, region;
    """,
    "v_dealer_performance": """
        CREATE VIEW v_dealer_performance AS
        SELECT
            d.dealer_id,
            d.dealer_name,
            d.tier,
            d.region,
            d.state_name,
            d.city_name,
            d.is_urban,
            d.latitude,
            d.longitude,
            COUNT(s.transaction_id)              AS total_transactions,
            COALESCE(SUM(s.quantity), 0)         AS total_units,
            ROUND(COALESCE(SUM(s.gross_amount),0), 2) AS total_revenue_inr,
            ROUND(COALESCE(AVG(s.gross_amount),0), 2) AS avg_basket_inr,
            MIN(s.transaction_date)              AS first_txn_date,
            MAX(s.transaction_date)              AS last_txn_date
        FROM dim_dealers d
        LEFT JOIN fact_sales s ON d.dealer_id = s.dealer_id
        GROUP BY d.dealer_id;
    """,
    "v_product_performance": """
        CREATE VIEW v_product_performance AS
        SELECT
            p.product_id,
            p.product_name,
            p.category,
            p.sub_category,
            p.material,
            p.tier,
            p.unit_price,
            COUNT(s.transaction_id)              AS transactions,
            COALESCE(SUM(s.quantity), 0)         AS units_sold,
            ROUND(COALESCE(SUM(s.gross_amount),0), 2) AS revenue_inr
        FROM dim_products p
        LEFT JOIN fact_sales s ON p.product_id = s.product_id
        GROUP BY p.product_id;
    """,
    "v_state_summary": """
        CREATE VIEW v_state_summary AS
        SELECT
            st.state_code,
            st.state_name,
            st.region,
            st.population_cr,
            st.urban_pct,
            st.market_potential,
            st.latitude,
            st.longitude,
            (SELECT COUNT(*) FROM dim_dealers d WHERE d.state_code = st.state_code AND d.is_active = 1) AS active_dealers,
            (SELECT COUNT(*) FROM dim_service_centres c WHERE c.state_code = st.state_code) AS service_centres,
            (SELECT ROUND(COALESCE(SUM(s.gross_amount),0),2)
             FROM fact_sales s JOIN dim_dealers d ON s.dealer_id=d.dealer_id
             WHERE d.state_code = st.state_code) AS total_revenue_inr,
            (SELECT COALESCE(SUM(s.quantity),0)
             FROM fact_sales s JOIN dim_dealers d ON s.dealer_id=d.dealer_id
             WHERE d.state_code = st.state_code) AS total_units
        FROM dim_states st;
    """,
}


def load():
    if DB.exists():
        DB.unlink()
        print(f"  Removed existing {DB.name}")
    
    conn = sqlite3.connect(DB)
    
    # Load tables
    for tbl, fname in TABLES:
        csv_path = RAW / fname
        if tbl in CHUNKED_TABLES:
            total = 0
            first = True
            for chunk in pd.read_csv(csv_path, chunksize=CHUNK_SIZE):
                chunk.to_sql(tbl, conn, index=False, if_exists="replace" if first else "append")
                first = False
                total += len(chunk)
            print(f"  ✓ Loaded {tbl}: {total:,} rows")
        else:
            df = pd.read_csv(csv_path)
            df.to_sql(tbl, conn, index=False, if_exists="replace")
            print(f"  ✓ Loaded {tbl}: {len(df):,} rows")
    
    # Indexes
    cur = conn.cursor()
    for idx_sql in INDEXES:
        cur.execute(idx_sql)
    print(f"  ✓ Created {len(INDEXES)} indexes")
    
    # Views
    for name, sql in VIEWS.items():
        cur.execute(f"DROP VIEW IF EXISTS {name};")
        cur.execute(sql)
    print(f"  ✓ Created {len(VIEWS)} analytical views")
    
    conn.commit()
    
    # Summary
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name;")
    views = [r[0] for r in cur.fetchall()]
    
    print("\n📊 DATABASE READY")
    print(f"   Path: {DB}")
    print(f"   Size: {DB.stat().st_size / (1024*1024):.1f} MB")
    print(f"   Tables ({len(tables)}): {', '.join(tables)}")
    print(f"   Views  ({len(views)}): {', '.join(views)}")
    
    conn.close()


if __name__ == "__main__":
    load()
