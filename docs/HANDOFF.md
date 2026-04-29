# Handoff to Claude Code

> **Read this document first before doing anything else.**

You are picking up the Hawkins Distribution Intelligence Platform (HDIP) at the end of **Phase 4: Foundation Complete**. The data layer, ETL, database, and dashboard skeleton are built and verified working. Your job is to complete the remaining work.

---

## ✅ What's Already Built (Don't Rebuild)

1. **All synthetic data** — 11 tables, 1.05M sales transactions, calibrated to real Hawkins financials
2. **SQLite database** at `data/hawkins.db` (192 MB) with indexes and 5 analytical views
3. **Master pipeline** — `python run_pipeline.py` rebuilds everything from scratch in ~2 min
4. **Dashboard skeleton** — `start.bat` works
5. **One fully-built reference page** — `frontend/pages/1_📊_Executive_Overview.py`
6. **Six stub pages** with detailed TODO comments at the top of each file

**Verify it works first:**
```bash
cd hdip/
pip install -r requirements.txt
python run_pipeline.py        # ~2 min
start.bat
```

If the home page shows ₹917 Cr revenue and 1,900 active dealers, you're good to go.

---

## 🎯 Your Build Order (Do These in Sequence)

### Priority 1: Complete the GIS Page (HIGHEST IMPACT)
**File:** `frontend/pages/2_🗺️_GIS_Distribution.py`

This is the centerpiece visual the JD explicitly calls for. Build:
1. India choropleth (states colored by revenue) using Plotly + India GeoJSON
   - GeoJSON URL: `https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/india_states.geojson`
   - Match `state_name` from `v_state_summary` to GeoJSON `ST_NM` property
2. Bubble overlay of dealers (lat/long in `dim_dealers`) sized by capacity, colored by tier
3. Three factory markers with distinct icon (Thane, Hoshiarpur, Sathariya)
4. Sidebar filters: region, product category, time period
5. **White-space analysis section** below the map: states ranked by `(market_potential / active_dealers)` ratio — high ratio = under-served = expansion opportunity

**Why this matters:** This is your strongest interview demo moment.

### Priority 2: Complete the Dealer Performance Page
**File:** `frontend/pages/3_🏪_Dealer_Performance.py`

The TODO comment at the top of the file has the full spec. Key deliverables:
- Performance scoring (revenue percentile within tier)
- Decliner detection (last 90d revenue / prior 90d revenue < 0.7)
- Individual dealer drill-down via selectbox
- Cohort analysis by onboarding year

### Priority 3: Build the ML Layer
Create new file: `scripts/ml/train_forecasts.py`
- Use SARIMA from `statsmodels.tsa.statespace.sarimax`
- Train on monthly aggregates per top-15 SKU
- Save each model to `models/forecast_{product_id}.pkl`
- Then update `frontend/pages/4_📈_Forecasting.py` to load and serve forecasts

Create `scripts/ml/anomaly_detection.py`:
- Z-score function for univariate (per-dealer monthly revenue)
- Isolation Forest from `sklearn.ensemble` for multivariate
- Feature set: revenue, txn_count, avg_basket, days_since_last_txn
- Save trained Isolation Forest to `models/anomaly_dealer.pkl`
- Update `frontend/pages/5_🚨_Anomaly_Detection.py`

Create `scripts/ml/segmentation.py`:
- RFM scoring (Recency, Frequency, Monetary) per dealer
- K-Means with k=4 (justified via elbow method)
- Add segment labels to a new view `v_dealer_segments`

### Priority 4: Complete Service Analytics & Competitive Intel
**Files:** `frontend/pages/6_🔧_Service_Analytics.py` and `7_⚔️_Competitive_Intel.py`

TODOs are documented at the top of each file. These are mostly Plotly charts on already-built tables — should be fast.

### Priority 5: Documentation
Write these files in `docs/`:
- `DATA_DICTIONARY.md` — every table and column documented (use the schema below)
- `ARCHITECTURE.md` — system diagram, tech choices
- `ML_METHODOLOGY.md` — why SARIMA, why Isolation Forest, evaluation metrics
- `INTERVIEW_PREP.md` — 30+ Q&A from the cheatsheet section below
- `DEMO_SCRIPT.md` — 5-minute live demo walkthrough

### Priority 6: Power BI Companion
Create `powerbi/HDIP_Hawkins.pbix`:
1. Open Power BI Desktop
2. Get Data → ODBC → connect to `data/hawkins.db` (use SQLite ODBC driver)
3. Import these tables: `v_state_summary`, `v_dealer_performance`, `v_product_performance`, `fact_sales` (sample 100K rows for performance)
4. Build 4 pages: Executive Overview, GIS Map, Dealer Scorecard, Service Analytics
5. Save as `.pbix` to the `powerbi/` directory

### Priority 7: Deploy to Streamlit Cloud
1. Push to GitHub: `git init && git add . && git commit -m "Initial HDIP" && git push`
2. Connect repo to https://streamlit.io/cloud
3. App entry: `frontend/app.py`
4. Note: `data/hawkins.db` is 192 MB. If this exceeds GitHub's 100MB-per-file limit, use Git LFS OR commit only the CSVs and have Streamlit run `python run_pipeline.py` on first boot.

---

## 📋 Database Schema Reference

### Dimensions
| Table | Rows | Key Columns |
|---|---|---|
| `dim_products` | 123 | `product_id`, `category` (Pressure Cooker / Cookware / Electricals / Accessory), `sub_category`, `material`, `tier`, `unit_price`, `popularity_index` |
| `dim_states` | 36 | `state_code`, `state_name`, `region`, `market_potential`, `latitude`, `longitude` |
| `dim_cities` | 119 | `city_id`, `city_name`, `state_code`, `tier` (1/2/3), lat/long |
| `dim_factories` | 3 | `factory_id`, `factory_name`, `state_code`, `monthly_capacity_units` |
| `dim_dealers` | 1,900 | `dealer_id`, `tier` (A/B/C), `region`, `state_name`, `city_name`, `is_urban`, `monthly_capacity_units`, `years_active`, lat/long |
| `dim_service_centres` | 140 | `centre_id`, `state_code`, lat/long, `monthly_capacity_requests` |
| `dim_new_launches` | 31 | `launch_id`, `product_id`, `launch_date`, `performance` (Hit/Average/Underperformer) |

### Facts
| Table | Rows | Description |
|---|---|---|
| `fact_sales` | 1,053,833 | Daily transactions: dealer × product × date with quantity, unit_price, gross_amount |
| `fact_inventory` | 10,584 | Monthly stock snapshots: factory × product with opening, production, dispatch, closing |
| `fact_service_requests` | 45,000 | Warranty claims: centre, product, issue_type, severity, status, resolution_days, cost |
| `fact_competitor_pricing` | 5,760 | Monthly competitor prices: TTK Prestige, Butterfly, Pigeon, Stove Kraft × top SKUs |

### Pre-built Analytical Views
- `v_sales_enriched` — Sales joined with all dimension attributes (use this 80% of the time)
- `v_monthly_revenue_by_state` — Pre-aggregated monthly revenue per state
- `v_dealer_performance` — Per-dealer aggregates: total revenue, avg basket, first/last txn
- `v_product_performance` — Per-SKU aggregates: units sold, revenue
- `v_state_summary` — **Materialized table** (not view): state KPIs incl. dealer/centre counts

---

## 🎤 Interview Cheat-Sheet (30 Likely Questions)

Use these to populate `docs/INTERVIEW_PREP.md`. Each Q has the strongest answer angle.

**Project / Business**
1. *Why did you build this?* → Direct relevance to Hawkins' business + JD requirements
2. *Walk me through the data flow.* → CSV generation → ETL → SQLite → frontend/ML/PowerBI
3. *Why synthetic data?* → Real Hawkins data isn't public; calibrated to verifiable facts
4. *How accurate is the calibration?* → ₹917 Cr / 3yr ≈ ₹305 Cr/yr scaled from real ₹1,194 Cr (proportional to 1,900/9,379 dealer ratio)
5. *Why SQLite, not Postgres?* → Zero-config matches in-house ethos; trivially migratable

**Technical / SQL**
6. *Show me a complex SQL you wrote.* → The materialized `v_state_summary` with multi-LEFT-JOIN aggregation
7. *Why materialize the view?* → Correlated subqueries scanned 1M rows × 36 states = slow
8. *How would you scale to 9,379 dealers?* → Migrate to Postgres, partition fact_sales by date

**Machine Learning**
9. *Why SARIMA over Prophet?* → Lighter dependency (statsmodels is 1/10th size of fbprophet), works well for monthly data, more defensible
10. *How did you validate the forecast?* → MAPE on last 6 months held-out
11. *Why Isolation Forest for anomalies?* → Multivariate, no labels needed, scikit-learn standard
12. *Why also use Z-score?* → Univariate, fully explainable. Layered approach: ZScore for the obvious, IF for the subtle.

**GIS / Visualization**
13. *Why Plotly choropleth, not Folium?* → Native Streamlit integration, better drill-down
14. *How did you handle India's state boundary file?* → Public domain GeoJSON, joined on state_name

**Architecture**
15. *Where would automation hook in?* → run_pipeline.py wrapped in cron / Airflow DAG
16. *How do you handle data updates?* → Idempotent ETL: drop & rebuild from CSVs (small enough to do daily)
17. *How would you secure this?* → SQLite read-only mode in dashboard, separate write user for ETL

**Hawkins-specific**
18. *What did you learn about Hawkins from this?* → Distribution-led business, 32% pressure cooker market share, dealer concentration risk
19. *What would Hawkins use this for in real life?* → Replace the monthly Excel-based regional review meetings
20. *What's the highest-value insight your dashboard surfaces?* → White-space states (high market_potential, low active_dealers) — direct expansion targets

**Behavioral**
21. *What was the hardest part?* → Realistic seasonality calibration (had to research Diwali/Akshaya Tritiya effects)
22. *If you had more time?* → Real GeoJSON district drill-down, automated PDF report mailer
23. *What would you do differently?* → Start with smaller data scale, iterate up
24. *Tell me about a tradeoff.* → 5x downsample for Streamlit Cloud — production design at full 9,379 scale

**Domain depth**
25. *What's the difference between Contura and Futura?* → Contura is rounded-body inner-lid aluminium (mass-market premium), Futura is hard-anodised flagship line — both real Hawkins lines I modeled
26. *Why does South India over-index on stainless steel?* → Cultural preference, idli/sambar cooking patterns, modeled via REGION_PRODUCT_PREF matrix

**Forward-looking**
27. *How would you add real-time?* → Kafka stream into a streaming table; Streamlit auto-refresh
28. *AI/LLM integration?* → A natural-language query layer (Text-to-SQL) on top of v_sales_enriched
29. *Mobile app?* → Streamlit's mobile responsiveness handles it; could also export to a Flutter wrapper
30. *What ROI would Hawkins see?* → Faster decisions (Excel → 30-sec dashboard), white-space identification, anomaly catch rate

---

## 🚨 Known Issues / Gotchas

1. **Database file is 192 MB.** GitHub free tier limits files to 100 MB. Use Git LFS, or commit only CSVs and have the deploy environment run `run_pipeline.py`.

2. **Streamlit caching warnings** in the test scripts are normal (caches need the runtime to actually run).

3. **Page filenames have emoji** — this works in Streamlit but be careful when copying paths in shell commands; quote them.

4. **Some dealers have zero transactions** — these are the 3% inactive ones, deliberately. Filter `is_active = 1` or use `LEFT JOIN`.

5. **Date format is ISO string** in `fact_sales.transaction_date`. For SARIMA, parse with `pd.to_datetime`.

---

## 🎯 Definition of "Done"

The project is interview-ready when:
- [ ] All 7 dashboard pages render without errors
- [ ] GIS choropleth shows India with revenue colored
- [ ] At least one ML model is trained and serves a forecast
- [ ] Power BI .pbix file exists and connects to the database
- [ ] All docs in `docs/` are filled in
- [ ] Project deployed to Streamlit Cloud with a public URL
- [ ] README has a live demo link in the header

Good luck. The foundation is solid — go build something interview-winning.

— Foundation built by previous Claude · April 2026

