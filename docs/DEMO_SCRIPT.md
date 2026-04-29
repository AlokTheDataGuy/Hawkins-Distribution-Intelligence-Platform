# 5-Minute Live Demo Script

**Audience:** Hiring manager or panel at Hawkins  
**Setting:** Screen share of the running Streamlit dashboard  
**Goal:** Show the full stack in 5 minutes, leaving time for questions

---

## Minute 0–1: Opening Hook

> "I want to show you a tool I built specifically for Hawkins — it connects to a synthetic but calibrated dataset of 1,900 dealers, 1 million transactions, and 3 years of sales history, all benchmarked against Hawkins' public financials."

**Open the Home page / Executive Overview.**

- Point to the ₹917 Cr revenue, 1,900 active dealers, 123 SKUs
- "These numbers are proportionally scaled from Hawkins' real figures — about 20% of your actual network."
- Hover over the monthly revenue chart: "You can see the Diwali spike in October–November and the Akshaya Tritiya lift in April–May — I calibrated both based on Hawkins' seasonal patterns."

---

## Minute 1–2: The GIS Map (Strongest Visual)

> "The question every National Sales Manager asks every Monday: where are we strong, and where are we losing ground?"

**Navigate to the GIS Distribution page.**

- The choropleth lights up — darker red = higher revenue states
- "UP and Maharashtra dominate — UP for population scale, Maharashtra because our Thane plant gives us logistics advantage within 200 km."
- Toggle on Dealers layer: bubbles appear
- "Each bubble is a dealer — size is their capacity, colour is tier. Green = Tier A, the top performers."
- Star markers: "Three factories — Thane, Hoshiarpur, Sathariya."

**Scroll to White-Space Analysis.**

- "This is the insight that changes a board presentation. The scatter plots market potential on the Y axis versus active dealers on the X axis. States in the upper-left are under-served — high potential, few dealers."
- Point to the table: "These are your expansion targets ranked by opportunity score. This is what I'd put on slide 3 of the annual strategy deck."

---

## Minute 2–3: Dealer Performance

> "Once we know where to expand, we need to know who's performing inside the existing network."

**Navigate to Dealer Performance → Decliners & Risers tab.**

- "Any dealer whose last 90 days is less than 70% of the prior 90 days is flagged as a Decliner — these need a call from the regional manager this week."
- "Risers — up more than 40% — these need extra inventory allocation before they run out and miss sales."

**Switch to Individual Drill-down.**

- Pick a top dealer: "This is their monthly revenue trend, their top SKUs, and how they compare to their tier peers on the box plot. This is the view the RSM opens before a dealer visit."

---

## Minute 3–4: ML Capabilities

> "Beyond reporting, the platform has predictive and detection capabilities."

**Navigate to Demand Forecasting.**

- Select a top SKU (e.g., a Pressure Cooker)
- "SARIMA model trained on 36 months of data. The dashed line is the 6-month forecast with confidence bands. MAPE on held-out data is around 10–12%."
- Drag the what-if slider: "If we run a 20% promotional campaign, the model projects this revenue lift. That's a planning input."

**Navigate to Anomaly Detection.**

- Show the inbox: "Critical alerts at the top — dealers with no transactions in 60+ days, price entry errors, statistical outliers."
- "We layer two detection methods: Z-score for explainable univariate spikes, Isolation Forest for subtle multivariate patterns. The rule-based dormancy alerts are what a regional manager would act on first."

---

## Minute 4–5: Closing with Competitive Intel

**Navigate to Competitive Intelligence.**

- Show the price gap trend: "Prestige is tracking about 5% above us, Butterfly 12% below. That means we're the value-leader vs Prestige but positioned above the low-end players."
- Show the heatmap: "You can see exactly which SKUs are under price pressure from which competitor."
- "This replaces the quarterly market research report. A pricing manager could open this on Monday morning and respond to a competitor move by Tuesday."

**Close:**

> "The entire stack — data generation, ETL, database, ML models, and this dashboard — runs from a single command. The database is SQLite for portability, trivially migratable to Postgres for production. Happy to walk through any layer in depth."

---

## Backup Talking Points (if questions arise)

- **"How long did this take?"** — About a week end-to-end: 2 days data engineering, 1 day SQL/views, 1 day ML, 2 days dashboard, 1 day docs.
- **"Is the data real?"** — Synthetic but calibrated. The aggregate financials match Hawkins' published numbers; the individual transactions are generated with realistic distributions.
- **"Could this run at Hawkins?"** — Yes. Connect to your actual ERP/SAP extract instead of the CSVs. The ETL and dashboard layers don't care where the CSVs come from.
- **"What would you add next?"** — District-level drill-down on the GIS map, automated Monday morning PDF reports to RSMs, and a natural-language query interface on top of the sales view.
