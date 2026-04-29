"""
Optimization step: Materialize the v_state_summary view as a real table.
The original view used correlated subqueries which were slow on large fact_sales.
Run AFTER load_to_sqlite.py.
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent.parent / "data" / "hawkins.db"


def materialize():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # Drop the slow view, replace with a materialized table
    cur.execute("DROP VIEW IF EXISTS v_state_summary;")
    
    cur.execute("""
        CREATE TABLE v_state_summary AS
        SELECT
            st.state_code,
            st.state_name,
            st.region,
            st.population_cr,
            st.urban_pct,
            st.market_potential,
            st.latitude,
            st.longitude,
            COALESCE(d.active_dealers, 0)    AS active_dealers,
            COALESCE(c.service_centres, 0)   AS service_centres,
            COALESCE(s.total_revenue_inr, 0) AS total_revenue_inr,
            COALESCE(s.total_units, 0)       AS total_units
        FROM dim_states st
        LEFT JOIN (
            SELECT state_code, COUNT(*) AS active_dealers
            FROM dim_dealers WHERE is_active = 1 GROUP BY state_code
        ) d ON st.state_code = d.state_code
        LEFT JOIN (
            SELECT state_code, COUNT(*) AS service_centres
            FROM dim_service_centres GROUP BY state_code
        ) c ON st.state_code = c.state_code
        LEFT JOIN (
            SELECT d.state_code,
                   ROUND(SUM(s.gross_amount), 2) AS total_revenue_inr,
                   SUM(s.quantity)              AS total_units
            FROM fact_sales s JOIN dim_dealers d ON s.dealer_id = d.dealer_id
            GROUP BY d.state_code
        ) s ON st.state_code = s.state_code;
    """)
    
    cur.execute("CREATE INDEX idx_state_summary_code ON v_state_summary(state_code);")
    
    # Run ANALYZE so query planner has stats
    cur.execute("ANALYZE;")
    
    conn.commit()
    rows = cur.execute("SELECT COUNT(*) FROM v_state_summary").fetchone()[0]
    sample = cur.execute("SELECT state_name, total_revenue_inr FROM v_state_summary ORDER BY total_revenue_inr DESC LIMIT 3").fetchall()
    conn.close()
    
    print(f"  ✓ Materialized v_state_summary: {rows} rows")
    print(f"  ✓ Top 3 by revenue: {sample}")


if __name__ == "__main__":
    materialize()
