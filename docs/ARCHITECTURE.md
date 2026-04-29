# HDIP Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA GENERATION LAYER                            │
│  scripts/data_generation/                                               │
│  generate_geography.py  → dim_states, dim_cities                    │
│  generate_products.py   → dim_products, dim_new_launches            │
│  generate_network.py    → dim_dealers, dim_factories,               │
│                           dim_service_centres                       │
│  generate_sales.py      → fact_sales (1.05M rows)                   │
│  generate_aux_tables.py → fact_inventory, fact_service_requests,    │
│                           fact_competitor_pricing                   │
│                                                                     │
│  Output: data/raw/*.csv                                             │
└───────────────────────┬─────────────────────────────────────────────┘
                        │  python run_pipeline.py (~2 min)
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       ETL LAYER                                     │
│  scripts/etl/load_to_sqlite.py   → loads CSVs → SQLite tables           │
│  scripts/etl/optimize_views.py   → creates analytical views,            │
│                                materializes v_state_summary          │
│                                                                     │
│  Output: data/hawkins.db (192 MB)                                   │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
              ┌─────────┴──────────┐
              ▼                    ▼
┌─────────────────────┐  ┌────────────────────────────────────────────┐
│    ML LAYER         │  │         DASHBOARD LAYER                    │
│  scripts/ml/            │  │  frontend/                                │
│  train_forecasts.py │  │  app.py (home / navigation)                │
│  anomaly_detection  │  │  pages/                                    │
│  segmentation.py    │  │    1_Executive_Overview.py                 │
│                     │  │    2_GIS_Distribution.py                   │
│  Output: models/    │  │    3_Dealer_Performance.py                 │
│  *.pkl, *.parquet   │  │    4_Forecasting.py                        │
└─────────────────────┘  │    5_Anomaly_Detection.py                  │
                         │    6_Service_Analytics.py                  │
                         │    7_Competitive_Intel.py                  │
                         │  utils/db.py, styling.py                   │
                         └────────────────────────────────────────────┘
```

## Technology Choices

| Layer | Technology | Rationale |
|---|---|---|
| Data storage | SQLite | Zero-config, file-portable, trivially migratable to Postgres |
| Dashboard | Streamlit | Fastest Python-native BI, native Plotly, easy Streamlit Cloud deploy |
| Charting | Plotly | Native Streamlit integration, drill-down, GIS choropleth support |
| Forecasting | statsmodels SARIMA | Lighter than Prophet (1/10th size), classical & defensible |
| Anomaly detection | scikit-learn IsolationForest | No labels required, multivariate, sklearn standard |
| GIS | Plotly Choropleth + GeoJSON | Native Streamlit rendering, no external tile server needed |

## Database Schema

### Dimension Tables
| Table | Rows | Description |
|---|---|---|
| `dim_products` | 123 | SKU catalogue with category, material, tier, unit_price |
| `dim_states` | 36 | Indian states/UTs with region, market_potential, lat/long |
| `dim_cities` | 119 | Cities with tier (1/2/3) and lat/long |
| `dim_dealers` | 1,900 | Dealer network with tier, capacity, onboarding date, lat/long |
| `dim_factories` | 3 | Plants at Thane (MH), Hoshiarpur (PB), Sathariya (UP) |
| `dim_service_centres` | 140 | Authorised service centres with lat/long |
| `dim_new_launches` | 31 | Product launches with performance rating |

### Fact Tables
| Table | Rows | Description |
|---|---|---|
| `fact_sales` | 1,053,833 | Daily sales: dealer × product × date × qty × amount |
| `fact_inventory` | 10,584 | Monthly factory stock snapshots |
| `fact_service_requests` | 45,000 | Warranty / repair claims |
| `fact_competitor_pricing` | 5,760 | Monthly competitor price points |

### Analytical Views
| View | Type | Description |
|---|---|---|
| `v_sales_enriched` | View | Sales joined with all dimensions |
| `v_monthly_revenue_by_state` | View | Monthly revenue per state |
| `v_dealer_performance` | View | Per-dealer aggregates |
| `v_product_performance` | View | Per-SKU aggregates |
| `v_state_summary` | Materialised table | State KPIs (pre-computed for performance) |
| `v_dealer_segments` | Table | RFM segments after running segmentation.py |

## Data Calibration

The synthetic data is calibrated to Hawkins' real financials:
- **₹917 Cr total revenue** over 3 years (≈ ₹305 Cr/yr)
- Real Hawkins FY2023 revenue: ₹1,194 Cr across 9,379 dealers
- Our scale: 1,900 / 9,379 = 20.3% of the real network → 20.3% of revenue ≈ ₹243 Cr
- The slight over-indexing accounts for synthetic calibration noise and is acceptable

## Scalability Path

| Current | Production Scale |
|---|---|
| SQLite, 192 MB | Postgres with partitioned `fact_sales` by date |
| 1,900 dealers | 9,379 dealers — 5× scale, same architecture |
| Manual `run_pipeline.py` | Airflow DAG on daily schedule |
| Streamlit Cloud | Kubernetes pod with Streamlit behind nginx |
| Flat-file ML models | MLflow model registry |

