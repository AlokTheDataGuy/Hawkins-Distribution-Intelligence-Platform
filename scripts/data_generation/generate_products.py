"""
Generate dim_products: Real Hawkins SKU catalog.

Based on actual Hawkins brand lines verified from hawkinscookers.com and ICRA report:
- 16+ pressure cooker brand lines
- Multiple cookware categories
- Electricals (Futura Smart Kettle launched FY24-25)
- 350+ total products in real catalog; we generate ~120 representative SKUs

Author: Alok Deep | HDIP Project
"""
import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)
OUT = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)


# Real Hawkins pressure cooker brand lines with their characteristics
# Pricing in INR — calibrated from actual buyhawkins.in market prices
COOKER_LINES = {
    "Classic":              {"material": "Aluminium",          "tier": "Standard", "base": 1450, "factor": 1.00, "induction": False, "popularity": 1.00},
    "Classic Wide":         {"material": "Aluminium",          "tier": "Standard", "base": 1850, "factor": 1.10, "induction": False, "popularity": 0.55},
    "Contura":              {"material": "Aluminium",          "tier": "Premium",  "base": 1850, "factor": 1.20, "induction": False, "popularity": 0.85},
    "Contura Black":        {"material": "Hard Anodised",      "tier": "Premium",  "base": 2400, "factor": 1.35, "induction": False, "popularity": 0.70},
    "Contura Black XT":     {"material": "Hard Anodised",      "tier": "Premium",  "base": 2900, "factor": 1.45, "induction": True,  "popularity": 0.55},
    "Stainless Steel Contura": {"material": "Stainless Steel", "tier": "Premium",  "base": 3400, "factor": 1.55, "induction": True,  "popularity": 0.45},
    "Hevibase":             {"material": "Aluminium",          "tier": "Standard", "base": 1750, "factor": 1.10, "induction": False, "popularity": 0.50},
    "Stainless Steel":      {"material": "Stainless Steel",    "tier": "Premium",  "base": 3200, "factor": 1.55, "induction": True,  "popularity": 0.65},
    "Tri-Ply Stainless Steel": {"material": "Stainless Steel", "tier": "Luxury",   "base": 4800, "factor": 1.80, "induction": True,  "popularity": 0.30},
    "Bigboy":               {"material": "Aluminium",          "tier": "Commercial","base": 4200, "factor": 1.40, "induction": False, "popularity": 0.20},
    "Instaa":               {"material": "Aluminium",          "tier": "Standard", "base": 1650, "factor": 1.05, "induction": False, "popularity": 0.40},
    "Ventura":              {"material": "Hard Anodised",      "tier": "Premium",  "base": 2200, "factor": 1.25, "induction": False, "popularity": 0.35},
    "Futura":               {"material": "Hard Anodised",      "tier": "Premium",  "base": 2700, "factor": 1.30, "induction": False, "popularity": 0.75},
    "Futura Stainless Steel": {"material": "Stainless Steel", "tier": "Premium",   "base": 3800, "factor": 1.60, "induction": True,  "popularity": 0.50},
    "Miss Mary":            {"material": "Aluminium",          "tier": "Economy",  "base": 1250, "factor": 0.90, "induction": False, "popularity": 0.65},
    "Miniature Classic":    {"material": "Aluminium",          "tier": "Economy",  "base": 950,  "factor": 0.80, "induction": False, "popularity": 0.25},
}

# Available sizes per brand line (matches real Hawkins catalog)
LINE_SIZES = {
    "Classic":              [1.5, 2, 3, 3.5, 4, 5, 6.5, 8, 10, 12],
    "Classic Wide":         [5, 6.5, 8, 10],
    "Contura":              [1.5, 2, 3, 3.5, 4, 5, 6.5],
    "Contura Black":        [3, 3.5, 4, 5, 6.5],
    "Contura Black XT":     [3, 4, 5, 6.5],
    "Stainless Steel Contura": [3, 4, 5, 6.5],
    "Hevibase":             [3, 4, 5, 6.5, 8],
    "Stainless Steel":      [2, 3, 4, 5, 6, 8, 10],
    "Tri-Ply Stainless Steel": [3, 5],
    "Bigboy":               [14, 18, 22],
    "Instaa":               [1.5, 2, 3],
    "Ventura":              [3, 5],
    "Futura":               [2, 3, 4, 5, 6, 7, 9],
    "Futura Stainless Steel": [3, 4, 5.5, 7],
    "Miss Mary":            [1.5, 2, 3, 3.5, 5],
    "Miniature Classic":    [1.5, 2],
}


def generate():
    rows = []
    sku = 10000
    
    # ---------- Pressure Cookers (core business) ----------
    for line, specs in COOKER_LINES.items():
        for size in LINE_SIZES[line]:
            sku += 1
            # Price scales with size, capped sensibly
            price = round(specs["base"] * (0.55 + 0.10 * size) * specs["factor"], -1)
            rows.append({
                "product_id":    f"HW-PC-{sku}",
                "product_name":  f"Hawkins {line} {size}L",
                "category":      "Pressure Cooker",
                "sub_category":  line,
                "material":      specs["material"],
                "tier":          specs["tier"],
                "size_litres":   size,
                "is_induction":  specs["induction"],
                "unit_price":    price,
                "popularity_index": specs["popularity"],
                "warranty_years": 5,
                "launch_year":   np.random.choice([2015, 2018, 2020, 2022, 2023, 2024], p=[0.15,0.20,0.25,0.20,0.10,0.10]),
            })
    
    # ---------- Cookware (Futura + Hawkins brands) ----------
    cookware_catalog = [
        # (sub_category, material, name_template, sizes, base_price)
        ("Tava",        "Non-Stick",        "Futura Non-Stick Tava {size}cm",       [22, 25, 28, 30], 550),
        ("Tava",        "Hard Anodised",    "Futura Hard Anodised Tava {size}cm",   [22, 25, 28],     750),
        ("Dosa Tava",   "Non-Stick",        "Futura Non-Stick Dosa Tava {size}cm",  [28, 30, 33],     900),
        ("Frying Pan",  "Non-Stick",        "Futura Non-Stick Frying Pan {size}cm", [22, 24, 26],     950),
        ("Frying Pan",  "Hard Anodised",    "Futura Hard Anodised Frying Pan {size}cm", [22, 24, 26], 1250),
        ("Kadhai",      "Non-Stick",        "Futura Non-Stick Kadhai {size}cm",     [24, 26, 28],     1300),
        ("Kadhai",      "Hard Anodised",    "Futura Hard Anodised Kadhai {size}cm", [24, 26, 28],     1650),
        ("Saucepan",    "Non-Stick",        "Futura Non-Stick Saucepan {size}cm",   [16, 18, 20],     750),
        ("Saucepan",    "Stainless Steel",  "Hawkins Tri-Ply Saucepan {size}cm",    [16, 18, 20],     1500),
        ("Handi",       "Non-Stick",        "Futura Non-Stick Handi {size}cm",      [22, 24],         1450),
        ("Deep Fry Pan","Hard Anodised",    "Futura Hard Anodised Deep Fry Pan {size}cm", [24, 26],   1800),
        ("Casserole",   "Hard Anodised",    "Futura Hard Anodised Casserole {size}cm", [22, 24, 26],  2100),
    ]
    for sub_cat, mat, name_tmpl, sizes, base in cookware_catalog:
        for size in sizes:
            sku += 1
            price = round(base + (size - sizes[0]) * 80, -1)
            rows.append({
                "product_id":    f"HW-CW-{sku}",
                "product_name":  name_tmpl.format(size=size),
                "category":      "Cookware",
                "sub_category":  sub_cat,
                "material":      mat,
                "tier":          "Premium" if mat in ["Hard Anodised", "Stainless Steel"] else "Standard",
                "size_litres":   None,
                "is_induction":  mat in ["Hard Anodised", "Stainless Steel"],
                "unit_price":    price,
                "popularity_index": np.random.uniform(0.25, 0.65),
                "warranty_years": 2,
                "launch_year":   np.random.choice([2018, 2020, 2022, 2023, 2024]),
            })
    
    # ---------- Electricals (newer category) ----------
    electricals = [
        ("Futura Smart Electronic Kettle 1.5L", "Electricals", "Smart Kettle", "Stainless Steel", 2890, 2024),
        ("Futura Electronic Kettle 1.7L",       "Electricals", "Kettle",       "Stainless Steel", 2190, 2023),
        ("Hawkins Induction Cooktop 2000W",     "Electricals", "Induction",    "Glass-top",       3490, 2022),
    ]
    for name, cat, sub, mat, price, yr in electricals:
        sku += 1
        rows.append({
            "product_id":    f"HW-EL-{sku}",
            "product_name":  name,
            "category":      cat,
            "sub_category":  sub,
            "material":      mat,
            "tier":          "Premium",
            "size_litres":   None,
            "is_induction":  False,
            "unit_price":    price,
            "popularity_index": 0.15,  # New, low popularity
            "warranty_years": 2,
            "launch_year":   yr,
        })
    
    # ---------- Accessories (high volume, low margin) ----------
    accessories = [
        ("Hawkins Gasket Standard",      "Accessory", "Gasket",        140),
        ("Hawkins Gasket Mini",          "Accessory", "Gasket",        110),
        ("Hawkins Gasket Bigboy",        "Accessory", "Gasket",        220),
        ("Hawkins Safety Valve",         "Accessory", "Safety Valve",  90),
        ("Hawkins Vent Weight",          "Accessory", "Vent Weight",   80),
        ("Hawkins Lid Handle",           "Accessory", "Handle",        180),
        ("Hawkins Body Handle Set",      "Accessory", "Handle",        260),
        ("Hawkins Repair Kit",           "Accessory", "Repair Kit",    450),
        ("Hawkins Idli Stand 4-Plate",   "Accessory", "Stand",         340),
        ("Hawkins Dish Set Separator",   "Accessory", "Separator",     280),
        ("Pressure Cooker Grid",         "Accessory", "Grid",          150),
    ]
    for name, cat, sub, price in accessories:
        sku += 1
        rows.append({
            "product_id":    f"HW-AC-{sku}",
            "product_name":  name,
            "category":      cat,
            "sub_category":  sub,
            "material":      "Mixed",
            "tier":          "Standard",
            "size_litres":   None,
            "is_induction":  False,
            "unit_price":    price,
            "popularity_index": 0.85,  # Replacement parts → constant demand
            "warranty_years": 0,
            "launch_year":   2015,
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "dim_products.csv", index=False)
    print(f"✓ dim_products: {len(df)} SKUs across {df['category'].nunique()} categories")
    print(f"  Categories: {df['category'].value_counts().to_dict()}")
    return df


if __name__ == "__main__":
    generate()
