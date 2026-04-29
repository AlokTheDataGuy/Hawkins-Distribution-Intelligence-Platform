# Hawkins Distribution Intelligence Platform

> A production-style internal analytics platform giving Hawkins management a single pane of glass over dealer performance, regional demand, inventory health, service quality, and competitive positioning — replacing scattered Excel reports with an automated, ML-augmented system.

Built by **Alok Deep** · Portfolio project for the Hawkins Cookers T/Systems role.

---

## Screenshots

### Home
![Home](frontend/public/screenshots/home.png)

### Executive Overview
![Executive Overview](frontend/public/screenshots/executive.png)

### GIS Distribution Map
![GIS Distribution](frontend/public/screenshots/gis_distribution.png)

### Dealer Performance
![Dealer Performance](frontend/public/screenshots/dealers_performance.png)

### Demand Forecasting
![Forecasting](frontend/public/screenshots/forecasting.png)

### Anomaly Detection
![Anomaly Detection](frontend/public/screenshots/anomaly_detection.png)

### Service Analytics
![Service Analytics](frontend/public/screenshots/service_analytics.png)

### Competitive Intelligence
![Competitive Intel](frontend/public/screenshots/competitive_intel.png)

---

## What This Project Demonstrates

| JD Requirement | How HDIP Addresses It |
|---|---|
| SQL, Python | Core data layer + ETL pipeline (1.05M transactions in SQLite) |
| Designing reports | 7 dashboard pages with drill-down filters and ML-augmented insights |
| Implementing automation | One-command pipeline, scheduled-style ETL, auto-trained ML models |
| ML / AI | SARIMA demand forecasting · Isolation Forest anomaly detection · RFM segmentation |
| Consumer / customer analytics | Dealer scoring, dormancy alerts, cohort analysis |
| GIS mapping | Pan-India choropleth with state drill-down and white-space opportunity scoring |
| In-house system development | Modular, fully documented, production-style codebase |
| Modern BI stack | React + TypeScript + Tailwind · FastAPI · Recharts · react-leaflet |

---

## The Data

All data is **synthetic but calibrated to publicly verified Hawkins facts**:

| Anchor | Real Hawkins Fact | This Project |
|---|---|---|
| Revenue | ₹1,030 Cr (FY24), ₹1,194 Cr (FY25) | ₹917 Cr over 3 years simulated |
| Dealers | 9,379 authorised dealers (ICRA 2024) | 1,900 (5× sampled for performance) |
| Service centres | ~700 across India / Nepal / Bhutan | 140 |
| Plants | Thane (MH), Hoshiarpur (PB), Sathariya (UP) | All 3 modelled with capacities |
| Brand lines | Classic, Contura, Futura, Stainless, Hevibase, Bigboy, Miss Mary, etc. | All 16+ lines with realistic SKU mix |
| Market share | ~32% Indian pressure cooker segment | Reflected in distribution patterns |
| Growth | FY23: +5%, FY24: +2%, FY25: recovery | Encoded in 3-year YoY trend |
| Seasonality | Diwali, Akshaya Tritiya, wedding season peaks | Coded into transaction date weights |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      DATA GENERATION LAYER                        │
│  scripts/data_generation/  →  data/raw/*.csv                      │
│  Products · Geography · Dealer network · Sales · Aux tables       │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                       ETL / DATABASE LAYER                        │
│  scripts/etl/load_to_sqlite.py  →  data/hawkins.db (SQLite)      │
│  10 indexes · 5 analytical views · 1 materialized summary        │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
          ┌─────────────────┴──────────────────┐
          ▼                                     ▼
┌──────────────────┐                 ┌─────────────────────────────┐
│    ML LAYER      │                 │       API LAYER              │
│                  │                 │  backend/  (FastAPI)         │
│  SARIMA forecasts│                 │  7 routers · 30+ endpoints   │
│  Isolation Forest│                 │  SQLite read-only · CORS     │
│  RFM + K-Means   │                 └──────────────┬──────────────┘
│  → models/*.pkl  │                                ▼
└──────────────────┘                 ┌─────────────────────────────┐
                                     │       UI LAYER               │
                                     │  frontend/  (React + Vite)   │
                                     │  TypeScript · Tailwind CSS   │
                                     │  Recharts · react-leaflet    │
                                     │  TanStack Query              │
                                     └─────────────────────────────┘
```

---

## Quick Start

**Prerequisites:** Python 3.10+ · Node.js 18+

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 2. Install Python dependencies
pip install -r backend/requirements.txt
pip install -r scripts/requirements.txt

# 3. Generate data, build database, and train ML models (~4 min)
python run_pipeline.py

# Skip ML training for a faster rebuild (~2 min):
python run_pipeline.py --skip-ml

# 4. Install frontend dependencies (first time only)
cd frontend && npm install && cd ..

# 5. Launch both servers
start.bat
```

| Service | URL |
|---|---|
| Frontend (React) | http://localhost:5173 |
| Backend (FastAPI) | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |

---

## Project Structure

```
hawkins-distribution-intelligence-platform/
├── backend/                        # FastAPI REST API
│   ├── routers/
│   │   ├── anomalies.py            # Z-score + Isolation Forest endpoints
│   │   ├── competitive.py          # Pricing gap vs competitors
│   │   ├── dealers.py              # Scoring, movers, cohorts
│   │   ├── executive.py            # KPIs, revenue trends
│   │   ├── forecasting.py          # SARIMA forecast endpoints
│   │   ├── gis.py                  # Map data, whitespace analysis
│   │   └── service.py              # Warranty claims, quality risk
│   ├── db.py                       # SQLite read-only connection helper
│   ├── main.py                     # FastAPI app + CORS
│   └── requirements.txt
│
├── frontend/                       # React + TypeScript (Vite)
│   ├── public/
│   │   ├── logo.png
│   │   └── screenshots/            # Dashboard screenshots for README
│   └── src/
│       ├── api/client.ts           # Axios base client
│       ├── components/             # Layout, Sidebar, ChartCard, KPICard, etc.
│       ├── context/FiltersContext.tsx  # Shared filter state across pages
│       └── pages/                  # One file per dashboard module
│           ├── Home.tsx
│           ├── Executive.tsx
│           ├── GISDistribution.tsx
│           ├── DealerPerformance.tsx
│           ├── Forecasting.tsx
│           ├── AnomalyDetection.tsx
│           ├── ServiceAnalytics.tsx
│           └── CompetitiveIntel.tsx
│
├── scripts/                        # Data pipeline + ML training
│   ├── data_generation/            # Synthetic data generators (5 scripts)
│   ├── etl/                        # CSV → SQLite + view optimisation
│   ├── ml/                         # SARIMA · Isolation Forest · RFM K-Means
│   └── requirements.txt            # Pipeline-only Python deps
│
├── data/
│   ├── raw/                        # Generated CSVs (11 files, 1.05M+ rows)
│   ├── processed/                  # ETL output staging
│   ├── hawkins.db                  # SQLite database (gitignored — run pipeline)
│   └── india_states.geojson        # State boundary polygons for choropleth
│
├── models/                         # Trained ML artifacts (gitignored)
│   ├── forecast_*.pkl              # Per-SKU SARIMA models
│   ├── forecast_index.json
│   ├── iso_anomalies.parquet       # Isolation Forest results
│   └── zscore_anomalies.parquet
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATA_DICTIONARY.md
│   ├── ML_METHODOLOGY.md
│   ├── DEMO_SCRIPT.md
│   ├── HANDOFF.md
│   └── INTERVIEW_PREP.md
│
├── .gitignore
├── run_pipeline.py                 # One-command: generate → ETL → ML training
└── start.bat                       # Launch backend + frontend together
```

---

## Interview Talking Points

**Opening (60 seconds):**
> *"I researched Hawkins' actual business model — 9,379 dealers across three plants in Thane, Hoshiarpur, and Sathariya, 32% market share in pressure cookers, 16+ brand lines from Classic to Futura. I built an internal-style analytics platform that addresses the specific operational questions your IT team would face: dealer performance, regional demand forecasting, inventory health, warranty patterns, and competitive pricing. The synthetic data is calibrated to your published financials — ₹1,030 Cr FY24, ₹1,194 Cr FY25, with the 2% growth slowdown that ICRA flagged."*

**Why this stands out:**
- Built specifically around Hawkins' real business — not generic dashboards
- Full-stack: FastAPI backend · React + TypeScript frontend · SQLite data layer
- ML depth: SARIMA time-series · Isolation Forest · RFM segmentation
- Matches Hawkins IT culture: modular, documented, in-house system design

---

## License

Educational / portfolio project. Not affiliated with Hawkins Cookers Ltd.
All facts about Hawkins are drawn from publicly available sources (annual reports, ICRA ratings, company website).
