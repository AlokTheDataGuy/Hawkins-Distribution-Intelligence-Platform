"""
Generate auxiliary fact tables:
  - fact_inventory: monthly stock snapshots by factory & SKU
  - fact_service_requests: warranty claims, repairs (links to service centres)
  - fact_competitor_pricing: TTK Prestige, Butterfly, Pigeon prices vs Hawkins
  - dim_new_launches: 58 new product launches over 3 years (per Hawkins FY25 report)
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date, timedelta

np.random.seed(42)
RAW = Path(__file__).resolve().parent.parent.parent / "data" / "raw"

START = date(2023, 4, 1)
END   = date(2026, 3, 31)


# ============================================================
# fact_inventory — Monthly stock snapshots per factory × SKU
# ============================================================
def generate_inventory():
    products  = pd.read_csv(RAW / "dim_products.csv")
    factories = pd.read_csv(RAW / "dim_factories.csv")
    
    rows = []
    snap_id = 600000
    
    # Each factory specializes
    factory_focus = {
        "FAC-001": {"Aluminium": 1.5, "Hard Anodised": 0.7, "Stainless Steel": 0.5},  # Thane: alu focus
        "FAC-002": {"Aluminium": 0.8, "Hard Anodised": 1.6, "Stainless Steel": 0.6},  # Hoshiarpur: HA focus
        "FAC-003": {"Aluminium": 0.6, "Hard Anodised": 0.7, "Stainless Steel": 1.6},  # Sathariya: SS + cookware
    }
    
    months = pd.date_range(START, END, freq="MS")
    
    for fac in factories.itertuples(index=False):
        focus = factory_focus.get(fac.factory_id, {})
        
        for prod in products.itertuples(index=False):
            # Skip if material isn't this factory's specialty (probabilistically)
            mat_factor = focus.get(prod.material, 1.0)
            if np.random.random() > min(mat_factor, 1.0):
                continue
            
            # Base monthly production for this SKU at this factory
            base = int(fac.monthly_capacity_units * prod.popularity_index * mat_factor / 1000)
            base = max(base, 50)
            
            for month in months:
                snap_id += 1
                # Production (with seasonality - higher pre-Diwali)
                seasonal_mult = 1.4 if month.month in [9, 10] else (0.85 if month.month in [7, 8] else 1.0)
                production = int(base * seasonal_mult * np.random.uniform(0.85, 1.15))
                
                # Opening, dispatch, closing
                opening = int(production * np.random.uniform(0.20, 0.45))
                dispatch = int((production + opening) * np.random.uniform(0.75, 0.95))
                closing = opening + production - dispatch
                
                rows.append({
                    "snapshot_id":     f"INV-{snap_id}",
                    "snapshot_date":   month.date().isoformat(),
                    "factory_id":      fac.factory_id,
                    "product_id":      prod.product_id,
                    "opening_stock":   opening,
                    "production_units": production,
                    "dispatch_units":  dispatch,
                    "closing_stock":   max(closing, 0),
                })
    
    df = pd.DataFrame(rows)
    df.to_csv(RAW / "fact_inventory.csv", index=False)
    print(f"✓ fact_inventory: {len(df):,} snapshots ({df['factory_id'].nunique()} factories × {df['product_id'].nunique()} SKUs × {len(months)} months)")
    return df


# ============================================================
# fact_service_requests — Warranty claims & repairs
# ============================================================
def generate_service_requests(n_requests=45000):
    products = pd.read_csv(RAW / "dim_products.csv")
    centres  = pd.read_csv(RAW / "dim_service_centres.csv")
    
    # Service requests skew toward older units & certain SKU lines
    # Pressure cookers under warranty (5 years) generate the most claims
    cookers = products[products["category"] == "Pressure Cooker"].copy()
    cookers["service_weight"] = cookers["popularity_index"] * np.where(
        cookers["material"] == "Aluminium", 1.2,  # Aluminium gaskets wear faster
        np.where(cookers["material"] == "Hard Anodised", 0.9, 0.7)
    )
    cookers["service_weight"] /= cookers["service_weight"].sum()
    
    issue_types = [
        ("Gasket Replacement",    0.35, "Routine"),
        ("Safety Valve Issue",    0.18, "Critical"),
        ("Handle Damage",         0.15, "Routine"),
        ("Vent Weight Lost",      0.12, "Routine"),
        ("Lid Stuck",             0.08, "Critical"),
        ("Pressure Loss",         0.06, "Critical"),
        ("Body Dent",             0.04, "Cosmetic"),
        ("Manufacturing Defect",  0.02, "Critical"),
    ]
    issue_names = [x[0] for x in issue_types]
    issue_probs = np.array([x[1] for x in issue_types])
    issue_severity_map = {x[0]: x[2] for x in issue_types}
    
    statuses = [("Resolved", 0.85), ("Pending", 0.10), ("Escalated", 0.05)]
    status_names = [x[0] for x in statuses]
    status_probs = [x[1] for x in statuses]
    
    rows = []
    
    # Date weights — more requests in summer (high cooking) and post-Diwali (returns/issues)
    date_range = pd.date_range(START, END - timedelta(days=1), freq="D")
    date_weights = np.array([
        1.3 if d.month in [5, 6, 11, 12] else (0.85 if d.month in [1, 2] else 1.0)
        for d in date_range
    ])
    date_weights /= date_weights.sum()
    
    chosen_dates = np.random.choice(date_range, size=n_requests, p=date_weights)
    chosen_centres = np.random.choice(centres["centre_id"].values, size=n_requests)
    chosen_products = np.random.choice(cookers["product_id"].values, size=n_requests, p=cookers["service_weight"].values)
    chosen_issues = np.random.choice(issue_names, size=n_requests, p=issue_probs)
    chosen_statuses = np.random.choice(status_names, size=n_requests, p=status_probs)
    
    # Resolution time depends on severity
    severity_arr = np.array([issue_severity_map[i] for i in chosen_issues])
    base_resolution = np.where(severity_arr == "Critical", 5, np.where(severity_arr == "Routine", 2, 3))
    resolution_days = base_resolution + np.random.poisson(2, size=n_requests)
    resolution_days = np.where(chosen_statuses == "Pending", -1, resolution_days)  # -1 = not resolved
    
    # Cost - replacement parts under warranty are free; out-of-warranty is paid
    is_under_warranty = np.random.random(n_requests) < 0.78  # 78% under 5-year warranty
    cost = np.where(is_under_warranty, 0,
                    np.random.choice([150, 250, 450, 800, 1500], size=n_requests, p=[0.4,0.3,0.15,0.10,0.05]))
    
    for i in range(n_requests):
        rows.append({
            "request_id":         f"SVC-REQ-{700000+i}",
            "request_date":       pd.Timestamp(chosen_dates[i]).date().isoformat(),
            "centre_id":          chosen_centres[i],
            "product_id":         chosen_products[i],
            "issue_type":         chosen_issues[i],
            "severity":           severity_arr[i],
            "status":             chosen_statuses[i],
            "resolution_days":    int(resolution_days[i]) if resolution_days[i] >= 0 else None,
            "is_under_warranty":  bool(is_under_warranty[i]),
            "cost_inr":           int(cost[i]),
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(RAW / "fact_service_requests.csv", index=False)
    print(f"✓ fact_service_requests: {len(df):,} requests")
    print(f"  Top issues: {df['issue_type'].value_counts().head(3).to_dict()}")
    return df


# ============================================================
# fact_competitor_pricing — TTK Prestige, Butterfly, Pigeon
# ============================================================
def generate_competitor_pricing():
    products = pd.read_csv(RAW / "dim_products.csv")
    
    # Competitors and their pricing posture relative to Hawkins
    competitors = {
        "TTK Prestige":       {"factor": 1.05, "volatility": 0.04},  # Premium positioning, +5%
        "Butterfly":          {"factor": 0.88, "volatility": 0.06},  # Value, -12%
        "Pigeon":             {"factor": 0.78, "volatility": 0.05},  # Budget, -22%
        "Stove Kraft":        {"factor": 0.92, "volatility": 0.07},  # Mid-market
    }
    
    # Sample monthly prices for top SKUs only (otherwise table explodes)
    top_skus = products.nlargest(40, "popularity_index")
    months = pd.date_range(START, END, freq="MS")
    
    rows = []
    pid = 800000
    
    for prod in top_skus.itertuples(index=False):
        for month in months:
            for comp_name, specs in competitors.items():
                pid += 1
                # Add monthly drift
                mom = (month.year - 2023) * 12 + month.month - 4
                drift = 1 + (mom * 0.003)  # gentle inflation
                base_factor = specs["factor"] * drift
                noise = np.random.normal(1.0, specs["volatility"])
                comp_price = round(prod.unit_price * base_factor * noise, -1)
                
                rows.append({
                    "pricing_id":       f"CP-{pid}",
                    "snapshot_date":    month.date().isoformat(),
                    "product_id":       prod.product_id,
                    "competitor":       comp_name,
                    "hawkins_price":    prod.unit_price,
                    "competitor_price": comp_price,
                    "price_gap_pct":    round((comp_price - prod.unit_price) / prod.unit_price * 100, 2),
                })
    
    df = pd.DataFrame(rows)
    df.to_csv(RAW / "fact_competitor_pricing.csv", index=False)
    print(f"✓ fact_competitor_pricing: {len(df):,} rows ({df['competitor'].nunique()} competitors × {df['product_id'].nunique()} SKUs × {len(months)} months)")
    return df


# ============================================================
# dim_new_launches — Track product launches (58/year per Hawkins FY25)
# ============================================================
def generate_launches():
    products = pd.read_csv(RAW / "dim_products.csv")
    
    # Use products with launch_year >= 2023 plus extrapolate
    launches = []
    
    # FY24-25 launches from real product list
    recent = products[products["launch_year"] >= 2023].copy()
    
    for prod in recent.itertuples(index=False):
        # Random launch month within the launch year
        launch_month = np.random.randint(1, 13)
        launch_day = np.random.randint(1, 28)
        launch_date = date(int(prod.launch_year), launch_month, launch_day)
        
        # Performance buckets
        perf_roll = np.random.random()
        if perf_roll < 0.20:
            perf, units_sold_y1 = "Hit", np.random.randint(15000, 50000)
        elif perf_roll < 0.55:
            perf, units_sold_y1 = "Average", np.random.randint(3000, 15000)
        else:
            perf, units_sold_y1 = "Underperformer", np.random.randint(200, 3000)
        
        launches.append({
            "launch_id":         f"LCH-{900000 + len(launches)}",
            "product_id":        prod.product_id,
            "product_name":      prod.product_name,
            "category":          prod.category,
            "launch_date":       launch_date.isoformat(),
            "launch_year":       int(prod.launch_year),
            "performance":       perf,
            "units_sold_year1":  int(units_sold_y1),
            "marketing_spend_inr": int(np.random.uniform(50000, 800000)),
        })
    
    df = pd.DataFrame(launches)
    df.to_csv(RAW / "dim_new_launches.csv", index=False)
    print(f"✓ dim_new_launches: {len(df)} launches")
    print(f"  Performance distribution: {df['performance'].value_counts().to_dict()}")
    return df


if __name__ == "__main__":
    generate_inventory()
    generate_service_requests()
    generate_competitor_pricing()
    generate_launches()
