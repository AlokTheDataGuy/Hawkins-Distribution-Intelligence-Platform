# Interview Preparation — 30 Q&A

## Project / Business

**Q1. Why did you build this?**
The Hawkins JD explicitly calls for distribution analytics, dealer performance management, and data-driven decisions. Rather than describing generic BI experience, I built a live system calibrated to Hawkins' actual business — 1,900 dealers, ₹917 Cr revenue, India-wide geography — so every chart in the interview is directly relevant. It also demonstrates end-to-end capability: data engineering, SQL, ML, and dashboarding in one project.

**Q2. Walk me through the data flow.**
CSV generation (`scripts/data_generation/`) → ETL into SQLite (`scripts/etl/`) → analytical views created → ML models trained (`scripts/ml/`) → Streamlit dashboard serves everything (`frontend/`). The master entry point is `python run_pipeline.py` which rebuilds everything from scratch in ~2 minutes.

**Q3. Why synthetic data?**
Real Hawkins transaction data isn't publicly available. Synthetic data lets me demonstrate technical breadth without asking for confidential information. Critically, I calibrated it to verifiable public facts — Hawkins' ₹1,194 Cr FY2023 revenue, 9,379 dealer count, 32% pressure cooker market share — so the insights are directionally accurate, not made up.

**Q4. How accurate is the calibration?**
The 1,900 dealer network is 20.3% of Hawkins' real 9,379. Revenue is proportionally scaled: 20.3% × ₹1,194 Cr × 3 years ≈ ₹727 Cr theoretical max. Our ₹917 Cr slightly over-indexes because we model 3 full fiscal years with growth, which is acceptable. Seasonality (Diwali Oct–Nov, Akshaya Tritiya Apr–May) and regional product preferences (South India stainless-steel preference) are calibrated from public sources.

**Q5. Why SQLite, not Postgres?**
Zero-config — no server to spin up, no credentials to manage, the entire database is one portable file. It handles 1M+ rows perfectly at this scale. The architecture is trivially migratable: swap `sqlite3.connect()` for `psycopg2` in `db.py`, run the same ETL against Postgres, done. For a first-version analytics layer at Hawkins' in-house scale, SQLite is the pragmatic choice.

---

## Technical / SQL

**Q6. Show me a complex SQL you wrote.**
The `v_state_summary` materialised table:
```sql
INSERT OR REPLACE INTO v_state_summary
SELECT
    ds.state_code,
    ds.state_name,
    ds.region,
    ds.market_potential,
    COALESCE(sr.total_revenue_inr, 0) AS total_revenue_inr,
    COALESCE(sr.total_units, 0)        AS total_units,
    COALESCE(sr.transaction_count, 0)  AS transaction_count,
    COALESCE(da.active_dealers, 0)     AS active_dealers,
    COALESCE(sc.service_centres, 0)    AS service_centres
FROM dim_states ds
LEFT JOIN (
    SELECT d.state_name,
           SUM(fs.gross_amount) AS total_revenue_inr,
           SUM(fs.quantity)     AS total_units,
           COUNT(*)             AS transaction_count
    FROM fact_sales fs JOIN dim_dealers d ON fs.dealer_id = d.dealer_id
    GROUP BY d.state_name
) sr ON ds.state_name = sr.state_name
LEFT JOIN (...) da ON ...
LEFT JOIN (...) sc ON ...
```

**Q7. Why materialise the view?**
The naive correlated-subquery approach scanned 1M rows × 36 states = 36M comparisons on every dashboard load. Materialising to a table reduces that to a 36-row lookup. A `REFRESH` takes 200ms and runs once at ETL time.

**Q8. How would you scale to 9,379 dealers?**
Migrate to Postgres, partition `fact_sales` by `transaction_date` (monthly partitions), add a composite index on `(dealer_id, transaction_date)`. The analytical views remain identical — only the connection string changes. If real-time needed, add a Kafka consumer writing to the streaming table with a 15-minute micro-batch materialization.

---

## Machine Learning

**Q9. Why SARIMA over Prophet?**
Three reasons: (1) statsmodels ships in every Python data-science environment — Prophet requires compiling Stan, which often fails on constrained deployments. (2) For monthly data with 36 observations, SARIMA is sufficiently expressive. (3) Classical Box-Jenkins methodology is easier to justify in an interview — "we differenced to achieve stationarity, checked ACF/PACF, validated with MAPE on held-out data."

**Q10. How did you validate the forecast?**
Chronological train/test split: train on all months except the last 6, forecast the held-out 6 months, compute MAPE. This preserves temporal ordering — no look-ahead bias. Target MAPE < 15% for monthly SKU-level demand.

**Q11. Why Isolation Forest for anomalies?**
No labels needed (we don't have ground-truth "this was an anomaly" historical data). It handles mixed-scale features without distance metric issues. Linear time complexity — scales to 10K dealers with no issue. The contamination parameter maps directly to a business requirement: "flag the worst 2% for investigation."

**Q12. Why also use Z-score?**
Z-score on univariate monthly revenue is fully explainable to a regional manager: "Dealer X's April revenue was 4.2σ above their historical mean." Isolation Forest catches subtle multivariate patterns but scores are opaque. The two layers are complementary: Z-score for the obvious and explainable, Isolation Forest for the subtle.

---

## GIS / Visualization

**Q13. Why Plotly choropleth, not Folium?**
Plotly renders natively inside Streamlit as a single `st.plotly_chart()` call with no iframe. It supports interactive tooltips, zoom, and drill-down without a separate JS layer. Folium embeds an iframe which creates sizing and state-management issues in multi-page Streamlit apps.

**Q14. How did you handle India's state boundary file?**
Downloaded a public-domain GeoJSON (MIT licensed, based on Survey of India open data). The GeoJSON uses `ST_NM` as the state name property. I mapped our `dim_states.state_name` values to match, handling edge cases like "Andaman & Nicobar Islands" → "Andaman & Nicobar Island". The file is cached locally after first download so the app works offline.

---

## Architecture

**Q15. Where would automation hook in?**
`run_pipeline.py` is already designed as a single-command rebuild. Wrap it in an Airflow DAG with a daily trigger: `BashOperator(task_id='rebuild', bash_command='python run_pipeline.py')`. Add a downstream task to refresh ML models weekly. The dashboard queries live data — no cache invalidation needed.

**Q16. How do you handle data updates?**
Idempotent ETL: every run drops and rebuilds all tables from CSVs. At Hawkins' real scale, you'd switch to incremental loads (insert only new `transaction_date` partitions) and use `UPSERT` for dimension changes. The `v_state_summary` materialisation would become a nightly scheduled job.

**Q17. How would you secure this?**
The dashboard connects to SQLite in read-only mode (`file:hawkins.db?mode=ro`). ETL runs as a separate process with write access. For production: separate read and write database users, Streamlit behind SSO (SAML/OIDC), row-level security for regional manager views (each RSM sees only their region).

---

## Hawkins-specific

**Q18. What did you learn about Hawkins from this?**
Hawkins is fundamentally a distribution-led business — their moat is the dealer network, not just the product. 32% pressure cooker market share in a commoditising category is maintained through dealer loyalty programs and service quality. The UP + Maharashtra revenue concentration reflects both population scale and Thane plant logistics proximity. South India over-indexes on stainless steel due to idli/sambar cooking patterns.

**Q19. What would Hawkins use this in real life?**
Replace the monthly Excel-based regional review meeting. Regional Sales Managers currently spend 2–3 hours collating data before each meeting — this dashboard provides the same view in 30 seconds. The white-space analysis would directly inform the annual dealer recruitment targets by state. The anomaly alerts would replace the "someone noticed it looked wrong" approach to irregular transactions.

**Q20. What's the highest-value insight your dashboard surfaces?**
The white-space analysis: states with high `market_potential` but low `active_dealers` count. These are direct expansion targets where adding 10 new dealers would have the highest marginal revenue impact. The scatter plot makes this immediately visible — states in the upper-left quadrant (high potential, low dealers) are the prioritised expansion zones.

---

## Behavioral

**Q21. What was the hardest part?**
Calibrating realistic seasonality. Indian cookware demand has two distinct peaks — Diwali (Oct–Nov, gifting-driven) and Akshaya Tritiya (Apr–May, auspicious-occasion-driven) — plus regional variation. Getting the synthetic `fact_sales` generator to produce those patterns while maintaining the correct aggregate totals required several iterations of the `generate_sales.py` script.

**Q22. If you had more time?**
District-level GeoJSON drill-down (we currently do state-level only). Automated PDF report mailer — Python `reportlab` generating a 2-page executive summary emailed to RSMs every Monday morning. Natural-language query layer (Text-to-SQL using Claude) on top of `v_sales_enriched`.

**Q23. What would you do differently?**
Start with a smaller data scale (100 dealers, 3 months) and iterate up. I spent time debugging the large-scale generation before validating the dashboard was reading data correctly. "Small-first, scale-second" is better engineering practice for synthetic data projects.

**Q24. Tell me about a tradeoff.**
The 1,900 dealer scale vs. Hawkins' real 9,379. I chose the smaller scale so the database fits in a GitHub repo and Streamlit Cloud's memory limit. The production design is identical — only the CSV row counts change. I documented the migration path explicitly in ARCHITECTURE.md so the tradeoff is transparent.

---

## Domain depth

**Q25. What's the difference between Contura and Futura?**
Both are real Hawkins pressure cooker lines I modelled. Contura is the rounded-body, inner-lid aluminium line — Hawkins' mass-market premium product. Futura is the hard-anodised flagship — aluminium treated to be harder than stainless steel, better heat distribution, positioned at the top of the market. Their margin profiles and dealer stocking patterns differ significantly in the model.

**Q26. Why does South India over-index on stainless steel?**
Cultural cooking patterns — idli, sambar, rasam are cooked in large, shallow vessels that don't work well in aluminium cookers. Stainless steel is also perceived as more hygienic for wet rice dishes. In the `generate_sales.py` script I implemented a `REGION_PRODUCT_PREF` matrix that upweights stainless steel SKU sales for Southern dealers.

---

## Forward-looking

**Q27. How would you add real-time?**
Kafka stream from the dealer POS/ERP system → consumer writes to `fact_sales_streaming` table in Postgres → Streamlit uses `st.rerun()` with a 60-second interval or a WebSocket connection. The ML anomaly detection would shift from batch (nightly) to micro-batch (15-minute windows).

**Q28. AI/LLM integration?**
A natural-language query layer on top of `v_sales_enriched`. The user types "show me declining dealers in Maharashtra Q3" → Claude converts to SQL → result rendered as a chart. This is achievable with the Anthropic API's tool-use feature and a few dozen example (question, SQL) pairs for few-shot prompting.

**Q29. Mobile app?**
Streamlit's responsive layout handles mobile browsers reasonably well. For a dedicated app: export key KPIs to a Flutter wrapper using Streamlit's REST API, or build a separate FastAPI backend serving JSON to Flutter. The database layer wouldn't change.

**Q30. What ROI would Hawkins see?**
Quantifiable: faster RSM meeting prep (2–3 hours saved per RSM per month × 50 RSMs = 100–150 hours/month). Directional: white-space identification could drive 5–10 new dealers per quarter in under-served states → incremental ₹2–4 Cr annual revenue at average dealer throughput. Anomaly alerts catching one fraudulent dealer per quarter at ₹10–20L typical exposure = ₹40–80L annual risk reduction.

