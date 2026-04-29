"""
Generate geography dimensions:
- dim_states: 36 Indian states/UTs with population, market potential, lat/long
- dim_cities: ~250 key cities (used as dealer hubs and consumption centres)
- dim_factories: 3 real Hawkins plants (Thane, Hoshiarpur, Sathariya)

Population & GDP weights drive realistic dealer distribution and sales volumes.
Source: Census 2011 + Niti Aayog estimates (publicly available data).
"""
import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)
OUT = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)


# ============================================================
# STATES — 28 states + 8 UTs with realistic market weights
# ============================================================
# Format: (state, code, region, population_cr, gdp_per_capita_inr_lakh, lat, lng, urbanisation_pct)
STATES = [
    # ---- North ----
    ("Delhi",              "DL", "North",   2.0,  4.50,  28.61, 77.21, 97.5),
    ("Punjab",             "PB", "North",   3.0,  1.95,  31.15, 75.34, 37.5),
    ("Haryana",            "HR", "North",   2.9,  3.10,  29.06, 76.09, 35.0),
    ("Himachal Pradesh",   "HP", "North",   0.7,  2.40,  31.10, 77.17, 10.0),
    ("Uttarakhand",        "UK", "North",   1.1,  2.30,  30.07, 79.02, 30.5),
    ("Jammu & Kashmir",    "JK", "North",   1.4,  1.30,  33.78, 76.57, 27.5),
    ("Ladakh",             "LA", "North",   0.03, 1.30,  34.15, 77.58, 23.0),
    ("Chandigarh",         "CH", "North",   0.12, 3.40,  30.73, 76.78, 97.0),
    
    # ---- West ----
    ("Maharashtra",        "MH", "West",   12.5,  2.50,  19.75, 75.71, 45.0),
    ("Gujarat",            "GJ", "West",    7.0,  2.85,  22.26, 71.19, 43.0),
    ("Rajasthan",          "RJ", "West",    8.1,  1.50,  27.02, 74.21, 25.0),
    ("Goa",                "GA", "West",    0.16, 4.70,  15.30, 74.12, 62.5),
    ("Dadra Nagar Haveli", "DD", "West",    0.06, 2.20,  20.39, 72.83, 47.0),
    
    # ---- South ----
    ("Tamil Nadu",         "TN", "South",   8.0,  2.65,  11.13, 78.66, 48.5),
    ("Karnataka",          "KA", "South",   6.7,  2.85,  15.32, 75.71, 38.7),
    ("Andhra Pradesh",     "AP", "South",   5.3,  2.10,  15.91, 79.74, 29.5),
    ("Telangana",          "TS", "South",   3.9,  2.65,  17.12, 79.20, 39.0),
    ("Kerala",             "KL", "South",   3.5,  2.80,  10.85, 76.27, 47.5),
    ("Puducherry",         "PY", "South",   0.13, 2.40,  11.94, 79.83, 68.0),
    ("Lakshadweep",        "LD", "South",   0.007,1.80,  10.57, 72.64, 78.0),
    ("Andaman Nicobar",    "AN", "South",   0.04, 2.20,  11.74, 92.66, 37.7),
    
    # ---- East ----
    ("West Bengal",        "WB", "East",    9.5,  1.45,  22.99, 87.86, 32.0),
    ("Odisha",             "OD", "East",    4.4,  1.50,  20.95, 85.10, 17.0),
    ("Jharkhand",          "JH", "East",    3.4,  1.10,  23.61, 85.28, 24.0),
    ("Bihar",              "BR", "East",   11.5,  0.55,  25.10, 85.31, 11.5),
    
    # ---- Central ----
    ("Uttar Pradesh",      "UP", "Central",20.0,  0.85,  26.85, 80.95, 22.0),
    ("Madhya Pradesh",     "MP", "Central", 8.0,  1.30,  22.97, 78.66, 28.0),
    ("Chhattisgarh",       "CG", "Central", 2.9,  1.30,  21.28, 81.87, 23.0),
    
    # ---- Northeast ----
    ("Assam",              "AS", "Northeast", 3.4,  1.10,  26.20, 92.94, 14.5),
    ("Tripura",            "TR", "Northeast", 0.4,  1.55,  23.94, 91.99, 26.0),
    ("Meghalaya",          "ML", "Northeast", 0.3,  0.90,  25.47, 91.37, 20.0),
    ("Manipur",            "MN", "Northeast", 0.3,  0.85,  24.66, 93.91, 30.0),
    ("Nagaland",           "NL", "Northeast", 0.2,  1.30,  26.16, 94.56, 28.0),
    ("Mizoram",            "MZ", "Northeast", 0.12, 1.55,  23.16, 92.94, 51.5),
    ("Arunachal Pradesh",  "AR", "Northeast", 0.15, 1.40,  28.22, 94.73, 22.5),
    ("Sikkim",             "SK", "Northeast", 0.07, 3.70,  27.53, 88.51, 25.0),
]


def generate_states():
    df = pd.DataFrame(STATES, columns=[
        "state_name","state_code","region","population_cr",
        "gdp_per_capita_lakh","latitude","longitude","urban_pct"
    ])
    
    # Market potential = population × disposable income proxy
    # Hawkins is mid-premium; weights toward higher-income, more urban states
    df["market_potential"] = (
        df["population_cr"] * 0.6 +
        df["gdp_per_capita_lakh"] * 0.3 +
        df["urban_pct"] / 100 * 0.1
    ).round(2)
    
    # Normalized share for use in sales generation
    df["market_share_pct"] = (df["market_potential"] / df["market_potential"].sum() * 100).round(2)
    
    df.to_csv(OUT / "dim_states.csv", index=False)
    print(f"✓ dim_states: {len(df)} states/UTs across {df['region'].nunique()} regions")
    print(f"  Top 5 by market potential: {df.nlargest(5, 'market_potential')['state_name'].tolist()}")
    return df


# ============================================================
# CITIES — Major cities used as dealer hubs (~120 cities)
# ============================================================
# Format: (city, state_code, lat, lng, tier)
# Tier 1: Mumbai, Delhi, Bangalore, etc.
# Tier 2: state capitals + major cities
# Tier 3: smaller district HQs

CITIES = [
    # Maharashtra
    ("Mumbai", "MH", 19.07, 72.88, 1), ("Pune", "MH", 18.52, 73.86, 1),
    ("Nagpur", "MH", 21.15, 79.09, 2), ("Nashik", "MH", 20.00, 73.79, 2),
    ("Thane", "MH", 19.22, 72.98, 1), ("Aurangabad", "MH", 19.88, 75.34, 2),
    ("Solapur", "MH", 17.66, 75.91, 3), ("Kolhapur", "MH", 16.71, 74.24, 3),
    ("Amravati", "MH", 20.93, 77.76, 3), ("Nanded", "MH", 19.16, 77.30, 3),
    
    # Delhi
    ("New Delhi", "DL", 28.61, 77.21, 1), ("Dwarka", "DL", 28.59, 77.05, 2),
    ("Rohini", "DL", 28.74, 77.07, 2),
    
    # Karnataka
    ("Bangalore", "KA", 12.97, 77.59, 1), ("Mysore", "KA", 12.30, 76.65, 2),
    ("Mangalore", "KA", 12.91, 74.86, 2), ("Hubli", "KA", 15.36, 75.12, 2),
    ("Belgaum", "KA", 15.85, 74.50, 3), ("Gulbarga", "KA", 17.33, 76.83, 3),
    
    # Tamil Nadu
    ("Chennai", "TN", 13.08, 80.27, 1), ("Coimbatore", "TN", 11.02, 76.96, 2),
    ("Madurai", "TN", 9.93, 78.12, 2), ("Trichy", "TN", 10.79, 78.70, 2),
    ("Salem", "TN", 11.66, 78.15, 3), ("Tirunelveli", "TN", 8.71, 77.76, 3),
    ("Vellore", "TN", 12.92, 79.13, 3), ("Erode", "TN", 11.34, 77.72, 3),
    
    # Telangana / AP
    ("Hyderabad", "TS", 17.39, 78.49, 1), ("Warangal", "TS", 17.97, 79.59, 3),
    ("Visakhapatnam", "AP", 17.69, 83.22, 2), ("Vijayawada", "AP", 16.51, 80.65, 2),
    ("Tirupati", "AP", 13.63, 79.42, 3), ("Guntur", "AP", 16.31, 80.43, 3),
    
    # West Bengal
    ("Kolkata", "WB", 22.57, 88.36, 1), ("Howrah", "WB", 22.59, 88.26, 2),
    ("Durgapur", "WB", 23.52, 87.31, 3), ("Siliguri", "WB", 26.71, 88.43, 3),
    ("Asansol", "WB", 23.68, 86.97, 3),
    
    # Gujarat
    ("Ahmedabad", "GJ", 23.02, 72.57, 1), ("Surat", "GJ", 21.17, 72.83, 2),
    ("Vadodara", "GJ", 22.31, 73.18, 2), ("Rajkot", "GJ", 22.30, 70.80, 2),
    ("Bhavnagar", "GJ", 21.76, 72.15, 3), ("Jamnagar", "GJ", 22.47, 70.06, 3),
    ("Gandhinagar", "GJ", 23.22, 72.65, 3),
    
    # Rajasthan
    ("Jaipur", "RJ", 26.91, 75.79, 1), ("Jodhpur", "RJ", 26.24, 73.02, 2),
    ("Udaipur", "RJ", 24.59, 73.71, 2), ("Kota", "RJ", 25.21, 75.86, 3),
    ("Ajmer", "RJ", 26.45, 74.64, 3), ("Bikaner", "RJ", 28.02, 73.31, 3),
    
    # Kerala
    ("Kochi", "KL", 9.93, 76.27, 2), ("Thiruvananthapuram", "KL", 8.52, 76.94, 1),
    ("Kozhikode", "KL", 11.25, 75.78, 2), ("Thrissur", "KL", 10.52, 76.21, 3),
    ("Kannur", "KL", 11.87, 75.37, 3), ("Kollam", "KL", 8.89, 76.61, 3),
    
    # UP — including Sathariya/Jaunpur (real Hawkins plant)
    ("Lucknow", "UP", 26.85, 80.95, 1), ("Kanpur", "UP", 26.45, 80.33, 2),
    ("Agra", "UP", 27.18, 78.01, 2), ("Varanasi", "UP", 25.32, 82.97, 2),
    ("Allahabad", "UP", 25.44, 81.85, 2), ("Sathariya", "UP", 25.65, 82.55, 3),
    ("Jaunpur", "UP", 25.75, 82.68, 3), ("Meerut", "UP", 28.98, 77.71, 2),
    ("Ghaziabad", "UP", 28.67, 77.45, 1), ("Noida", "UP", 28.54, 77.39, 1),
    ("Bareilly", "UP", 28.37, 79.43, 3), ("Aligarh", "UP", 27.88, 78.08, 3),
    ("Gorakhpur", "UP", 26.76, 83.37, 3),
    
    # Punjab — including Hoshiarpur (real Hawkins plant)
    ("Ludhiana", "PB", 30.90, 75.86, 1), ("Amritsar", "PB", 31.63, 74.87, 2),
    ("Jalandhar", "PB", 31.33, 75.58, 2), ("Hoshiarpur", "PB", 31.53, 75.91, 2),
    ("Patiala", "PB", 30.34, 76.39, 3), ("Bathinda", "PB", 30.21, 74.95, 3),
    
    # Haryana
    ("Gurugram", "HR", 28.46, 77.03, 1), ("Faridabad", "HR", 28.41, 77.32, 1),
    ("Panipat", "HR", 29.39, 76.96, 3), ("Karnal", "HR", 29.69, 76.99, 3),
    ("Hisar", "HR", 29.15, 75.72, 3), ("Ambala", "HR", 30.37, 76.78, 3),
    
    # MP
    ("Bhopal", "MP", 23.26, 77.41, 1), ("Indore", "MP", 22.72, 75.86, 1),
    ("Gwalior", "MP", 26.22, 78.18, 2), ("Jabalpur", "MP", 23.18, 79.99, 2),
    ("Ujjain", "MP", 23.18, 75.78, 3),
    
    # Bihar
    ("Patna", "BR", 25.59, 85.14, 1), ("Gaya", "BR", 24.79, 85.00, 3),
    ("Muzaffarpur", "BR", 26.12, 85.36, 3), ("Bhagalpur", "BR", 25.24, 86.97, 3),
    
    # Odisha
    ("Bhubaneswar", "OD", 20.30, 85.82, 2), ("Cuttack", "OD", 20.46, 85.88, 3),
    ("Rourkela", "OD", 22.26, 84.85, 3),
    
    # Jharkhand
    ("Ranchi", "JH", 23.34, 85.31, 2), ("Jamshedpur", "JH", 22.80, 86.20, 2),
    ("Dhanbad", "JH", 23.80, 86.43, 3),
    
    # Chhattisgarh
    ("Raipur", "CG", 21.25, 81.63, 2), ("Bhilai", "CG", 21.20, 81.43, 3),
    
    # Assam + NE
    ("Guwahati", "AS", 26.14, 91.74, 2), ("Silchar", "AS", 24.83, 92.78, 3),
    ("Dibrugarh", "AS", 27.47, 94.91, 3),
    ("Agartala", "TR", 23.83, 91.28, 3), ("Imphal", "MN", 24.81, 93.94, 3),
    ("Shillong", "ML", 25.58, 91.89, 3), ("Aizawl", "MZ", 23.73, 92.72, 3),
    ("Kohima", "NL", 25.67, 94.11, 3), ("Itanagar", "AR", 27.10, 93.62, 3),
    ("Gangtok", "SK", 27.33, 88.61, 3),
    
    # HP / Uttarakhand / J&K
    ("Shimla", "HP", 31.10, 77.17, 3), ("Dharamshala", "HP", 32.22, 76.32, 3),
    ("Dehradun", "UK", 30.32, 78.03, 2), ("Haridwar", "UK", 29.95, 78.16, 3),
    ("Srinagar", "JK", 34.08, 74.80, 2), ("Jammu", "JK", 32.73, 74.86, 2),
    
    # Goa / Pondy
    ("Panaji", "GA", 15.50, 73.83, 2), ("Margao", "GA", 15.27, 73.96, 3),
    ("Pondicherry", "PY", 11.94, 79.83, 3),
    ("Chandigarh City", "CH", 30.73, 76.78, 1),
]


def generate_cities():
    df = pd.DataFrame(CITIES, columns=["city_name","state_code","latitude","longitude","tier"])
    df["city_id"] = ["CITY-" + str(1000 + i) for i in range(len(df))]
    df = df[["city_id","city_name","state_code","tier","latitude","longitude"]]
    df.to_csv(OUT / "dim_cities.csv", index=False)
    print(f"✓ dim_cities: {len(df)} cities (Tier1: {(df['tier']==1).sum()}, Tier2: {(df['tier']==2).sum()}, Tier3: {(df['tier']==3).sum()})")
    return df


# ============================================================
# FACTORIES — 3 real Hawkins plants
# ============================================================
def generate_factories():
    factories = [
        {
            "factory_id":   "FAC-001",
            "factory_name": "Thane Plant",
            "city_name":    "Thane",
            "state_code":   "MH",
            "latitude":     19.22,
            "longitude":    72.98,
            "established":  1960,
            "monthly_capacity_units": 220000,
            "primary_product_line":   "Pressure Cooker - Aluminium",
            "employees":    280,
        },
        {
            "factory_id":   "FAC-002",
            "factory_name": "Hoshiarpur Plant",
            "city_name":    "Hoshiarpur",
            "state_code":   "PB",
            "latitude":     31.53,
            "longitude":    75.91,
            "established":  1985,
            "monthly_capacity_units": 165000,
            "primary_product_line":   "Pressure Cooker - Hard Anodised",
            "employees":    195,
        },
        {
            "factory_id":   "FAC-003",
            "factory_name": "Sathariya Plant (Jaunpur)",
            "city_name":    "Sathariya",
            "state_code":   "UP",
            "latitude":     25.65,
            "longitude":    82.55,
            "established":  2010,
            "monthly_capacity_units": 140000,
            "primary_product_line":   "Pressure Cooker - Stainless Steel + Cookware",
            "employees":    175,
        },
    ]
    df = pd.DataFrame(factories)
    df.to_csv(OUT / "dim_factories.csv", index=False)
    print(f"✓ dim_factories: {len(df)} plants — total monthly capacity {df['monthly_capacity_units'].sum():,} units")
    return df


if __name__ == "__main__":
    generate_states()
    generate_cities()
    generate_factories()
