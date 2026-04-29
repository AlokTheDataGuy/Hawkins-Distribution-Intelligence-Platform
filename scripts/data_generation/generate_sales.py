"""
Generate fact_sales: 3 years of dealer-level sales transactions.

REALISM RULES (these enable real interview answers):
1. SEASONALITY:
   - Diwali peak (Oct-Nov): +60% sales
   - Akshaya Tritiya (Apr-May): +30% (auspicious to buy new utensils)
   - Wedding season (Nov-Feb): +20%
   - Monsoon dip (Jul-Aug): -15%

2. REGIONAL PATTERNS:
   - South India: over-indexes on Stainless Steel + Idli Stands
   - North India: over-indexes on Hard Anodised + larger sizes
   - West: premium SKUs, Futura line strong
   - East: price-sensitive, Miss Mary + Classic strong
   - Central: balanced, growing market
   - Northeast: smaller volumes, induction-compatible preferred

3. GROWTH TREND:
   - FY22-23: post-COVID boom (+12% YoY)
   - FY23-24: slowdown (+5%)
   - FY24-25: recovery (+8%)
   These match published Hawkins financials (revenue ₹1,030 Cr → ₹1,194 Cr)

4. DEALER TIER EFFECTS:
   - Tier A: high frequency, large baskets
   - Tier B: moderate
   - Tier C: low frequency, small baskets

5. PRODUCT POPULARITY:
   - Drives base sales rate per SKU
   - Accessories sell very steadily (replacement parts)
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date, timedelta

np.random.seed(42)
RAW = Path(__file__).resolve().parent.parent.parent / "data" / "raw"

# 3-year window: 1 Apr 2023 → 31 Mar 2026
START = date(2023, 4, 1)
END   = date(2026, 3, 31)


def seasonality_multiplier(d: date) -> float:
    """Return seasonality multiplier for a given date."""
    m, dy = d.month, d.day
    mult = 1.0
    
    # Diwali (varies, but mid-Oct to mid-Nov)
    if (m == 10 and dy >= 15) or (m == 11 and dy <= 15):
        mult *= 1.60
    # Pre-Diwali ramp
    elif m == 10 and dy < 15:
        mult *= 1.25
    # Akshaya Tritiya & Vaisakhi (late April to mid May)
    elif (m == 4 and dy >= 20) or (m == 5 and dy <= 15):
        mult *= 1.30
    # Wedding season
    elif m in [11, 12, 1, 2] and not (m == 11 and dy <= 15):
        mult *= 1.20
    # Monsoon
    elif m in [7, 8]:
        mult *= 0.85
    # Post-financial-year clearance
    elif m == 3:
        mult *= 1.10
    
    # Weekly pattern: weekends slightly higher
    if d.weekday() >= 5:
        mult *= 1.15
    
    return mult


def yoy_growth_factor(d: date) -> float:
    """Apply YoY growth aligned to Hawkins published financials."""
    fy_year = d.year if d.month >= 4 else d.year - 1
    if fy_year == 2023:
        return 1.00       # FY24 base (Apr23-Mar24)
    elif fy_year == 2024:
        return 1.05       # FY25: +5%
    elif fy_year == 2025:
        return 1.13       # FY26: +8% on previous = ~1.13x base
    return 1.0


# Regional product preference matrix
# Higher value = more preferred in that region
REGION_PRODUCT_PREF = {
    "South":     {"Stainless Steel": 1.4, "Hard Anodised": 0.9, "Aluminium": 1.0, "Non-Stick": 1.2, "Mixed": 1.0, "Glass-top": 1.1},
    "North":     {"Stainless Steel": 0.9, "Hard Anodised": 1.4, "Aluminium": 1.1, "Non-Stick": 1.0, "Mixed": 1.0, "Glass-top": 1.0},
    "West":      {"Stainless Steel": 1.2, "Hard Anodised": 1.3, "Aluminium": 1.0, "Non-Stick": 1.1, "Mixed": 1.0, "Glass-top": 1.2},
    "East":      {"Stainless Steel": 0.8, "Hard Anodised": 0.9, "Aluminium": 1.3, "Non-Stick": 1.0, "Mixed": 1.0, "Glass-top": 0.8},
    "Central":   {"Stainless Steel": 0.9, "Hard Anodised": 1.0, "Aluminium": 1.2, "Non-Stick": 1.0, "Mixed": 1.0, "Glass-top": 0.9},
    "Northeast": {"Stainless Steel": 1.1, "Hard Anodised": 1.0, "Aluminium": 0.9, "Non-Stick": 1.1, "Mixed": 1.0, "Glass-top": 1.0},
}


def generate_sales():
    products = pd.read_csv(RAW / "dim_products.csv")
    dealers  = pd.read_csv(RAW / "dim_dealers.csv")
    
    print(f"  Generating sales for {len(dealers)} dealers × ~{(END-START).days} days...")
    
    # PRE-COMPUTE date weights ONCE for the full date range
    full_dates = pd.date_range(START, END - timedelta(days=1), freq="D")
    date_weights_full = np.array([
        seasonality_multiplier(d.date()) * yoy_growth_factor(d.date())
        for d in full_dates
    ])
    print(f"  Pre-computed weights for {len(full_dates)} days")
    
    # Dealer monthly transaction frequency by tier
    # Tuned to target ~1M total rows for deployment-friendly Streamlit Cloud performance
    tier_monthly_txn = {"A": 40, "B": 15, "C": 5}
    
    # Pre-compute product weights and attribute arrays
    products["_weight"] = products["popularity_index"]
    material_arr  = products["material"].values
    induction_arr = products["is_induction"].values
    tier_arr      = products["tier"].values
    prod_id_arr   = products["product_id"].values
    prod_price_arr = products["unit_price"].values
    prod_cat_arr  = products["category"].values
    base_weight   = products["_weight"].values
    
    # Cache region-prefs vectors
    region_pref_cache = {
        r: np.array([prefs.get(m, 1.0) for m in material_arr])
        for r, prefs in REGION_PRODUCT_PREF.items()
    }
    
    tier_c_boost = np.array([{"Economy": 1.4, "Standard": 1.2, "Premium": 0.7, "Luxury": 0.3, "Commercial": 0.5}.get(t, 1.0) for t in tier_arr])
    tier_a_boost = np.array([{"Economy": 0.7, "Standard": 1.0, "Premium": 1.3, "Luxury": 1.5, "Commercial": 1.2}.get(t, 1.0) for t in tier_arr])
    induction_urban_boost = np.where(induction_arr, 1.25, 0.95)
    
    chunks = []
    txn_counter = 1_000_000
    
    for d_idx, dealer in enumerate(dealers.itertuples(index=False)):
        if d_idx % 250 == 0:
            print(f"  ... processing dealer {d_idx}/{len(dealers)}")
        
        if not dealer.is_active:
            dealer_end = END - timedelta(days=int(np.random.randint(180, 365)))
        else:
            dealer_end = END
        
        dealer_start = max(START, date.fromisoformat(dealer.onboarded_date))
        if dealer_start >= dealer_end:
            continue
        
        n_days = (dealer_end - dealer_start).days
        base_monthly = tier_monthly_txn[dealer.tier] * np.random.uniform(0.80, 1.20)
        est_total = int(base_monthly * n_days / 30)
        if est_total < 1:
            continue
        
        start_offset = (dealer_start - START).days
        end_offset = (dealer_end - START).days
        weights = date_weights_full[start_offset:end_offset].copy()
        weights /= weights.sum()
        date_slice = full_dates[start_offset:end_offset]
        
        chosen_day_idx = np.random.choice(len(date_slice), size=est_total, p=weights)
        chosen_dates = date_slice[chosen_day_idx]
        
        # Build product weights vector for this dealer (vectorized)
        prod_weights = base_weight * region_pref_cache.get(dealer.region, np.ones(len(products)))
        if dealer.is_urban:
            prod_weights = prod_weights * induction_urban_boost
        if dealer.tier == "C":
            prod_weights = prod_weights * tier_c_boost
        elif dealer.tier == "A":
            prod_weights = prod_weights * tier_a_boost
        prod_weights = prod_weights / prod_weights.sum()
        
        chosen_prod_idx = np.random.choice(len(products), size=est_total, p=prod_weights)
        
        # Vectorized quantity
        cat_vec = prod_cat_arr[chosen_prod_idx]
        qty_default = np.random.choice([1,2,3,4,5], size=est_total, p=[0.55,0.22,0.12,0.07,0.04])
        qty_accessory = np.random.choice([1,2,3,5,10], size=est_total, p=[0.4,0.25,0.15,0.12,0.08])
        qty = np.where(cat_vec == "Accessory", qty_accessory, qty_default)
        
        if dealer.tier == "A":
            bulk_mask = np.random.random(est_total) < 0.05
            bulk_qty = np.random.randint(20, 100, size=est_total)
            qty = np.where(bulk_mask, bulk_qty, qty)
        
        margin_factor = np.random.uniform(0.92, 1.02, size=est_total)
        unit_price = np.round(prod_price_arr[chosen_prod_idx] * margin_factor, 2)
        gross_amount = np.round(qty * unit_price, 2)
        discount_pct = np.round(np.maximum(0, (1 - margin_factor) * 100), 2)
        
        txn_ids = np.arange(txn_counter + 1, txn_counter + 1 + est_total)
        txn_counter += est_total
        
        chunk = pd.DataFrame({
            "transaction_id":   ["TXN-" + str(t) for t in txn_ids],
            "transaction_date": pd.to_datetime(chosen_dates).date.astype(str),
            "dealer_id":        dealer.dealer_id,
            "product_id":       prod_id_arr[chosen_prod_idx],
            "quantity":         qty.astype(int),
            "unit_price":       unit_price,
            "gross_amount":     gross_amount,
            "discount_pct":     discount_pct,
            "channel":          dealer.channel,
        })
        chunks.append(chunk)
    
    print(f"  Concatenating {len(chunks)} dealer chunks...")
    df = pd.concat(chunks, ignore_index=True)
    print(f"  Total rows generated: {len(df):,}")
    
    # Sort by date for nice ordering
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df = df.sort_values("transaction_date").reset_index(drop=True)
    df["transaction_date"] = df["transaction_date"].dt.date.astype(str)
    
    df.to_csv(RAW / "fact_sales.csv", index=False)
    
    # Print summary stats for sanity
    print(f"✓ fact_sales: {len(df):,} transactions")
    print(f"  Date range: {df['transaction_date'].min()} → {df['transaction_date'].max()}")
    print(f"  Total gross: ₹{df['gross_amount'].sum()/1e7:.0f} Cr")
    print(f"  Unique dealers transacting: {df['dealer_id'].nunique()}")
    print(f"  Unique products sold: {df['product_id'].nunique()}")
    
    return df


if __name__ == "__main__":
    generate_sales()
