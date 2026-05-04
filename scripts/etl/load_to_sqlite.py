"""
ETL Pipeline: Loads all CSV dimensions and facts into a DuckDB database.

DuckDB's read_csv_auto streams directly from disk — no pandas DataFrame
in the middle — so even 1M-row fact tables stay within Render's 512MB limit.
"""
import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RAW  = ROOT / "data" / "raw"
DB   = ROOT / "data" / "hawkins.db"

TABLES = [
    # Dimensions
    ("dim_products",           "dim_products.csv"),
    ("dim_states",             "dim_states.csv"),
    ("dim_cities",             "dim_cities.csv"),
    ("dim_factories",          "dim_factories.csv"),
    ("dim_dealers",            "dim_dealers.csv"),
    ("dim_service_centres",    "dim_service_centres.csv"),
    ("dim_new_launches",       "dim_new_launches.csv"),
    # Facts
    ("fact_sales",             "fact_sales.csv"),
    ("fact_inventory",         "fact_inventory.csv"),
    ("fact_service_requests",  "fact_service_requests.csv"),
    ("fact_competitor_pricing","fact_competitor_pricing.csv"),
]

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_sales_date        ON fact_sales(transaction_date);",
    "CREATE INDEX IF NOT EXISTS idx_sales_dealer      ON fact_sales(dealer_id);",
    "CREATE INDEX IF NOT EXISTS idx_sales_product     ON fact_sales(product_id);",
    "CREATE INDEX IF NOT EXISTS idx_sales_dealer_date ON fact_sales(dealer_id, transaction_date);",
    "CREATE INDEX IF NOT EXISTS idx_inv_date          ON fact_inventory(snapshot_date);",
    "CREATE INDEX IF NOT EXISTS idx_inv_factory       ON fact_inventory(factory_id);",
    "CREATE INDEX IF NOT EXISTS idx_svc_date          ON fact_service_requests(request_date);",
    "CREATE INDEX IF NOT EXISTS idx_svc_centre        ON fact_service_requests(centre_id);",
    "CREATE INDEX IF NOT EXISTS idx_dealers_state     ON dim_dealers(state_code);",
    "CREATE INDEX IF NOT EXISTS idx_dealers_tier      ON dim_dealers(tier);",
]

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
            strftime(transaction_date, '%Y-%m') AS year_month,
            state_code,
            state_name,
            region,
            COUNT(*)                     AS transactions,
            SUM(quantity)                AS units_sold,
            ROUND(SUM(gross_amount), 2)  AS revenue_inr
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
            COUNT(s.transaction_id)                          AS total_transactions,
            COALESCE(SUM(s.quantity), 0)                     AS total_units,
            ROUND(COALESCE(SUM(s.gross_amount), 0), 2)       AS total_revenue_inr,
            ROUND(COALESCE(AVG(s.gross_amount), 0), 2)       AS avg_basket_inr,
            MIN(s.transaction_date)                          AS first_txn_date,
            MAX(s.transaction_date)                          AS last_txn_date
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
            COUNT(s.transaction_id)                    AS transactions,
            COALESCE(SUM(s.quantity), 0)               AS units_sold,
            ROUND(COALESCE(SUM(s.gross_amount), 0), 2) AS revenue_inr
        FROM dim_products p
        LEFT JOIN fact_sales s ON p.product_id = s.product_id
        GROUP BY p.product_id;
    """,
}


def load():
    if DB.exists():
        DB.unlink()
        print(f"  Removed existing {DB.name}")

    conn = duckdb.connect(str(DB))

    for tbl, fname in TABLES:
        csv_path = str(RAW / fname)
        conn.execute(f"""
            CREATE OR REPLACE TABLE {tbl} AS
            SELECT * FROM read_csv_auto('{csv_path}', header=true)
        """)
        count = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"  ✓ Loaded {tbl}: {count:,} rows")

    for idx_sql in INDEXES:
        conn.execute(idx_sql)
    print(f"  ✓ Created {len(INDEXES)} indexes")

    for name, sql in VIEWS.items():
        conn.execute(f"DROP VIEW IF EXISTS {name};")
        conn.execute(sql)
    print(f"  ✓ Created {len(VIEWS)} analytical views")

    tables = [r[0] for r in conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main' AND table_type='BASE TABLE' ORDER BY table_name").fetchall()]
    views  = [r[0] for r in conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main' AND table_type='VIEW' ORDER BY table_name").fetchall()]

    print("\n📊 DATABASE READY")
    print(f"   Path: {DB}")
    print(f"   Size: {DB.stat().st_size / (1024*1024):.1f} MB")
    print(f"   Tables ({len(tables)}): {', '.join(tables)}")
    print(f"   Views  ({len(views)}): {', '.join(views)}")

    conn.close()


if __name__ == "__main__":
    load()
