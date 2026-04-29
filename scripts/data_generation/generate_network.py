"""
Generate dim_dealers and dim_service_centres.

Real Hawkins network (per ICRA 2024):
  - 9,379 authorized dealers
  - ~700 service centres across India, Nepal, Bhutan

Project scale (5x sampled): 1,900 dealers, 140 service centres
This sampling is documented as a deliberate engineering choice in the README.

Distribution logic:
  - Dealers allocated to cities weighted by state market potential & city tier
  - Tier A/B/C dealer classification (Pareto: 20% top → 60% revenue)
  - Service centres located in tier 1 & 2 cities only (urban concentration)
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date, timedelta

np.random.seed(42)
RAW = Path(__file__).resolve().parent.parent.parent / "data" / "raw"


def generate_dealers(n_dealers=1900):
    states = pd.read_csv(RAW / "dim_states.csv")
    cities = pd.read_csv(RAW / "dim_cities.csv")
    
    # Allocate dealer count per state proportional to market potential
    states["dealer_count"] = (states["market_potential"] / states["market_potential"].sum() * n_dealers).round().astype(int)
    # Adjust rounding to hit exact target
    diff = n_dealers - states["dealer_count"].sum()
    if diff != 0:
        idx = states["dealer_count"].idxmax()
        states.at[idx, "dealer_count"] += diff
    
    rows = []
    dealer_id = 100000
    
    # City tier weights — tier 1 cities get more dealers per capita
    tier_weight = {1: 5.0, 2: 2.5, 3: 1.0}
    
    for _, st in states.iterrows():
        st_cities = cities[cities["state_code"] == st["state_code"]].copy()
        if len(st_cities) == 0:
            # Fallback: use state centroid
            st_cities = pd.DataFrame([{
                "city_id": f"FALLBACK-{st['state_code']}",
                "city_name": st["state_name"],
                "state_code": st["state_code"],
                "tier": 3,
                "latitude": st["latitude"],
                "longitude": st["longitude"],
            }])
        st_cities["weight"] = st_cities["tier"].map(tier_weight)
        st_cities["weight"] /= st_cities["weight"].sum()
        
        n = int(st["dealer_count"])
        if n == 0:
            continue
        # Sample cities for each dealer, with replacement
        chosen_idx = np.random.choice(st_cities.index, size=n, p=st_cities["weight"], replace=True)
        
        for ci in chosen_idx:
            city = st_cities.loc[ci]
            dealer_id += 1
            
            # Dealer tier — Pareto: 20% A, 30% B, 50% C
            tier_roll = np.random.random()
            if tier_roll < 0.20:
                d_tier, capacity = "A", np.random.randint(1500, 4000)
            elif tier_roll < 0.50:
                d_tier, capacity = "B", np.random.randint(600, 1500)
            else:
                d_tier, capacity = "C", np.random.randint(150, 600)
            
            # Years active — older dealers tend to be tier A
            tier_year_bias = {"A": (8, 30), "B": (4, 18), "C": (1, 10)}
            yrs_active = np.random.randint(*tier_year_bias[d_tier])
            
            # Onboarded date
            onboard = date.today() - timedelta(days=int(yrs_active * 365 + np.random.randint(0, 365)))
            
            # Small jitter on lat/long to spread points within a city
            lat = city["latitude"] + np.random.uniform(-0.05, 0.05)
            lng = city["longitude"] + np.random.uniform(-0.05, 0.05)
            
            # Channel — most are physical retailers, a few are online/B2B
            channel_roll = np.random.random()
            if channel_roll < 0.78:
                channel = "Retail Store"
            elif channel_roll < 0.92:
                channel = "Multi-Brand Outlet"
            elif channel_roll < 0.97:
                channel = "Online Marketplace"
            else:
                channel = "Institutional/B2B"
            
            # Urban / rural flag based on city tier
            is_urban = city["tier"] in [1, 2]
            
            rows.append({
                "dealer_id":          f"DLR-{dealer_id}",
                "dealer_name":        f"{city['city_name']} {d_tier}{np.random.randint(100,999)} Distributors",
                "city_id":            city["city_id"],
                "city_name":          city["city_name"],
                "state_code":         st["state_code"],
                "state_name":         st["state_name"],
                "region":             st["region"],
                "tier":               d_tier,
                "channel":            channel,
                "is_urban":           is_urban,
                "monthly_capacity_units": capacity,
                "years_active":       yrs_active,
                "onboarded_date":     onboard.isoformat(),
                "latitude":           round(lat, 4),
                "longitude":          round(lng, 4),
                "credit_limit_inr":   int(capacity * np.random.uniform(800, 2000)),
                "is_active":          np.random.random() > 0.03,  # 3% inactive (closed/dormant)
            })
    
    df = pd.DataFrame(rows)
    df.to_csv(RAW / "dim_dealers.csv", index=False)
    print(f"✓ dim_dealers: {len(df)} dealers")
    print(f"  By tier: {df['tier'].value_counts().to_dict()}")
    print(f"  By region: {df['region'].value_counts().to_dict()}")
    print(f"  Active: {df['is_active'].sum()} ({df['is_active'].mean()*100:.1f}%)")
    return df


def generate_service_centres(n_centres=140):
    cities = pd.read_csv(RAW / "dim_cities.csv")
    states = pd.read_csv(RAW / "dim_states.csv")
    
    # Service centres only in tier 1 & 2 cities (urban network)
    eligible = cities[cities["tier"].isin([1, 2])].copy()
    eligible = eligible.merge(states[["state_code","state_name","region","market_potential"]], on="state_code")
    
    # Weight by city tier and state market potential
    eligible["weight"] = eligible.apply(
        lambda r: (3.0 if r["tier"] == 1 else 1.5) * (1 + r["market_potential"]/10), axis=1)
    eligible["weight"] /= eligible["weight"].sum()
    
    # Sample with replacement, then deduplicate-extend so each city can have multiple centres
    chosen = np.random.choice(eligible.index, size=n_centres, p=eligible["weight"], replace=True)
    
    rows = []
    centre_id = 50000
    for ci in chosen:
        city = eligible.loc[ci]
        centre_id += 1
        
        # Capacity: tier 1 cities have larger centres
        cap = np.random.randint(80, 250) if city["tier"] == 1 else np.random.randint(30, 100)
        
        rows.append({
            "centre_id":          f"SVC-{centre_id}",
            "centre_name":        f"Hawkins Service Centre - {city['city_name']} #{np.random.randint(1,9)}",
            "city_id":            city["city_id"],
            "city_name":          city["city_name"],
            "state_code":         city["state_code"],
            "state_name":         city["state_name"],
            "region":             city["region"],
            "latitude":           round(city["latitude"] + np.random.uniform(-0.03, 0.03), 4),
            "longitude":          round(city["longitude"] + np.random.uniform(-0.03, 0.03), 4),
            "monthly_capacity_requests": cap,
            "established_year":   np.random.randint(1985, 2024),
            "is_authorised":      True,
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(RAW / "dim_service_centres.csv", index=False)
    print(f"✓ dim_service_centres: {len(df)} centres in {df['city_name'].nunique()} cities, {df['state_code'].nunique()} states")
    return df


if __name__ == "__main__":
    generate_dealers()
    generate_service_centres()
