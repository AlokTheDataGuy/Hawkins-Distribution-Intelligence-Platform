# Data Dictionary

Single source of truth for every table and column in HDIP.

## Dimension Tables

### `dim_products` (123 rows)
| Column | Type | Description |
|---|---|---|
| product_id | TEXT (PK) | Synthetic ID e.g. `HW-PC-10001` (PC=Pressure Cooker, CW=Cookware, EL=Electricals, AC=Accessory) |
| product_name | TEXT | Real Hawkins SKU name e.g. "Hawkins Classic 5L" |
| category | TEXT | Pressure Cooker / Cookware / Electricals / Accessory |
| sub_category | TEXT | Brand line: Classic, Contura, Futura, Stainless, etc. |
| material | TEXT | Aluminium / Hard Anodised / Stainless Steel / Non-Stick / Mixed / Glass-top |
| tier | TEXT | Economy / Standard / Premium / Luxury / Commercial |
| size_litres | REAL | Capacity for cookers; null for cookware/accessories |
| is_induction | BOOLEAN | True if induction-compatible |
| unit_price | REAL | List price in INR |
| popularity_index | REAL | 0-1 base demand multiplier (drives sales generation) |
| warranty_years | INT | 5 for cookers, 2 for cookware, 0 for accessories |
| launch_year | INT | When introduced to market |

### `dim_states` (36 rows)
| Column | Type | Description |
|---|---|---|
| state_name | TEXT | Full state/UT name |
| state_code | TEXT (PK) | 2-letter code e.g. MH, TN, KA |
| region | TEXT | North / South / East / West / Central / Northeast |
| population_cr | REAL | Population in crores (Census 2011 estimates) |
| gdp_per_capita_lakh | REAL | Approximate, in INR lakh |
| latitude / longitude | REAL | State centroid |
| urban_pct | REAL | Urbanisation % |
| market_potential | REAL | Composite: population × income × urbanisation |
| market_share_pct | REAL | This state's share of national potential |

### `dim_cities` (119 rows)
| Column | Description |
|---|---|
| city_id (PK), city_name, state_code | Standard |
| tier | 1 / 2 / 3 (drives dealer allocation) |
| latitude, longitude | City coordinates |

### `dim_factories` (3 rows)
The three real Hawkins plants: Thane (MH), Hoshiarpur (PB), Sathariya (UP).
| Column | Description |
|---|---|
| factory_id, factory_name, city_name, state_code | Standard |
| latitude, longitude | Plant location |
| established | Year founded |
| monthly_capacity_units | Production capacity |
| primary_product_line | Specialization |
| employees | Headcount |

### `dim_dealers` (1,900 rows)
| Column | Description |
|---|---|
| dealer_id (PK) | `DLR-XXXXXX` |
| dealer_name | Synthetic e.g. "Mumbai A201 Distributors" |
| city_id, city_name, state_code, state_name, region | Geo |
| tier | A (top 20%) / B (30%) / C (50%) — Pareto distribution |
| channel | Retail Store / Multi-Brand Outlet / Online Marketplace / Institutional/B2B |
| is_urban | Boolean — drives induction-cooker preference |
| monthly_capacity_units | Sales capacity (used for performance scoring) |
| years_active, onboarded_date | Tenure |
| latitude, longitude | Dealer location (jittered within city) |
| credit_limit_inr | Credit terms |
| is_active | 97% true; 3% dormant |

### `dim_service_centres` (140 rows)
| Column | Description |
|---|---|
| centre_id (PK), centre_name | Standard |
| city_id, city_name, state_code, state_name, region | Geo |
| latitude, longitude, monthly_capacity_requests | Operational |
| established_year, is_authorised | Status |

### `dim_new_launches` (31 rows)
Subset of `dim_products` with extra launch metadata.
| Column | Description |
|---|---|
| launch_id (PK), product_id (FK), product_name, category | Standard |
| launch_date, launch_year | When launched |
| performance | Hit / Average / Underperformer |
| units_sold_year1 | First-year sales |
| marketing_spend_inr | Launch marketing budget |

---

## Fact Tables

### `fact_sales` (1,053,833 rows)
The core transactional table. One row per dealer purchase.
| Column | Description |
|---|---|
| transaction_id (PK) | `TXN-XXXXXXX` |
| transaction_date | ISO date string |
| dealer_id (FK), product_id (FK) | Standard |
| quantity | Units in transaction (mostly 1-5; tier-A bulk orders 20-100) |
| unit_price | Realized price (list ± dealer margin) |
| gross_amount | quantity × unit_price |
| discount_pct | 0-8% |
| channel | Echoes dealer's channel for fact-table self-sufficiency |

### `fact_inventory` (10,584 rows)
Monthly stock snapshots.
| Column | Description |
|---|---|
| snapshot_id (PK), snapshot_date (1st of each month) | Standard |
| factory_id (FK), product_id (FK) | Standard |
| opening_stock, production_units, dispatch_units, closing_stock | Inventory flow |

### `fact_service_requests` (45,000 rows)
Warranty claims & repairs.
| Column | Description |
|---|---|
| request_id (PK), request_date, centre_id (FK), product_id (FK) | Standard |
| issue_type | Gasket Replacement / Safety Valve Issue / Handle Damage / Vent Weight Lost / Lid Stuck / Pressure Loss / Body Dent / Manufacturing Defect |
| severity | Critical / Routine / Cosmetic |
| status | Resolved (85%) / Pending (10%) / Escalated (5%) |
| resolution_days | NULL if not resolved yet |
| is_under_warranty | 78% true |
| cost_inr | 0 if under warranty |

### `fact_competitor_pricing` (5,760 rows)
Monthly price snapshots for top 40 SKUs vs 4 competitors.
| Column | Description |
|---|---|
| pricing_id (PK), snapshot_date, product_id (FK) | Standard |
| competitor | TTK Prestige / Butterfly / Pigeon / Stove Kraft |
| hawkins_price, competitor_price | Side-by-side |
| price_gap_pct | (competitor - hawkins) / hawkins × 100 |

---

## Analytical Views

| View | Purpose |
|---|---|
| `v_sales_enriched` | Sales joined with dealer + product attributes — use for 80% of analysis |
| `v_monthly_revenue_by_state` | Pre-aggregated monthly revenue per state |
| `v_dealer_performance` | Per-dealer total revenue, avg basket, transaction count |
| `v_product_performance` | Per-SKU units sold and revenue |
| `v_state_summary` | **Materialized table** — state KPIs incl. dealer/centre counts |
| `v_dealer_segments` | **Table** (created by `scripts/ml/segmentation.py`) — RFM scores + K-Means segment per dealer: `recency_days`, `frequency`, `monetary`, `R_score`, `F_score`, `M_score`, `rfm_total`, `cluster`, `segment` (Champions / Potential Loyalists / At-Risk / New–Low-Value) |

---

## Realism Rules Encoded in the Data

1. **Pareto on dealers:** Top 20% (Tier A) generate ~60% of revenue
2. **Seasonality:** Diwali +60%, Akshaya Tritiya +30%, wedding season +20%, monsoon -15%
3. **Regional preferences:** South over-indexes stainless steel; North over-indexes hard anodised
4. **Urban / rural split:** Urban dealers favor induction-compatible
5. **Growth trend:** FY24 +5%, FY25 +8% YoY (matches published Hawkins financials)
6. **Inactive dealers:** 3% have no transactions in last 6 months (planted dormancy signal)
7. **Service patterns:** Aluminium gaskets fail more often than stainless steel
8. **Competitor positioning:** Prestige +5%, Butterfly -12%, Pigeon -22% vs Hawkins

