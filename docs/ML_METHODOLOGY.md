# ML Methodology

## 1. Demand Forecasting — SARIMA

### Why SARIMA?

| Criterion | SARIMA | Prophet |
|---|---|---|
| Dependency size | ~5 MB (statsmodels) | ~500 MB (fbprophet + stan) |
| Monthly data performance | Excellent | Good |
| Interpretability | ACF/PACF, classical stats | Black-box trend + Fourier |
| Interview defensibility | "Peer-reviewed, Box-Jenkins" | "Facebook's library" |
| Streamlit Cloud fit | ✅ | Often memory-limits |

**SARIMA(1,1,1)(1,1,1,12)** is the starting parameterisation:
- `(p=1, d=1, q=1)` — one AR lag, first-order differencing, one MA term
- `(P=1, D=1, Q=1, m=12)` — seasonal AR, seasonal differencing, seasonal MA at 12-month period

### Training Protocol
1. Aggregate `fact_sales` to monthly revenue per SKU
2. Top-15 SKUs by total revenue selected for modelling
3. Hold out last 6 months as test set
4. Fit SARIMA on training split → compute MAPE on held-out months
5. Refit on full series for production forecasting
6. Save fitted result + forecast + confidence intervals to `models/forecast_{product_id}.pkl`

### Evaluation Metric
**MAPE (Mean Absolute Percentage Error)** on the held-out 6-month window:

```
MAPE = mean(|actual - forecast| / actual) × 100
```

Target: MAPE < 15% for monthly SKU-level forecasting is considered good.
Typical range for FMCG demand: 10–25% depending on SKU volatility.

### Seasonality
Indian cookware demand shows strong seasonality driven by:
- **Diwali (Oct–Nov):** gifting surge, +30–60% above trendline
- **Akshaya Tritiya (Apr–May):** auspicious purchase occasion, +20–40%
- **Summer (Apr–Jun):** travel cooking, rural harvest income → baseline lift

These are captured automatically by the seasonal component `(P,D,Q,12)`.

---

## 2. Anomaly Detection — Layered Approach

### Layer 1: Z-Score (Univariate)

**What it detects:** Per-dealer monthly revenue that falls outside ±3σ of that dealer's own history.

**Formula:**
```
z = (revenue_month - mean_revenue) / std_revenue
Flag if |z| > 3.0
```

**Why it's included:** Fully explainable. "Dealer X's April revenue was 4.2 standard deviations above their historical mean" is something a regional manager can immediately understand and act on.

**Severity:**  |z| > 5 → Critical, else Warning

### Layer 2: Isolation Forest (Multivariate)

**What it detects:** Dealers whose *combination* of features is unusual — even if no single metric is extreme.

**Features used:**
- `revenue` — 3-year total sales
- `txn_count` — transaction frequency
- `avg_basket` — average order size
- `days_since_last_txn` — recency

**Algorithm:** Isolation Forest partitions the feature space by randomly selecting a feature and a split value. Anomalous points require fewer splits to isolate → lower anomaly score.

**Parameters:**
- `n_estimators=200` — ensemble of 200 trees
- `contamination=0.02` — flag top 2% as anomalies
- `random_state=42` — reproducibility

**Why Isolation Forest over LOF/DBSCAN:**
- No distance metric required (handles mixed scales well)
- Scales linearly with dataset size
- sklearn standard with no extra dependencies
- Contamination parameter maps directly to business requirement ("flag the worst 2%")

### Layer 3: Rule-based (Domain)

Rules that statistics alone can't catch:
- **Dormancy:** Tier-A/B dealer with no transactions in >30 days
- **Price entry errors:** Unit price >20% above/below catalogue
- **Inventory spike:** Factory stock >2× rolling 3-month average

---

## 3. Dealer Segmentation — RFM + K-Means

### RFM Scoring

Each dealer is scored on three dimensions:

| Dimension | Definition | Scoring |
|---|---|---|
| **Recency (R)** | Days since last transaction | Lower = better (score 1–4, 4=most recent) |
| **Frequency (F)** | Total transaction count | Higher = better (score 1–4) |
| **Monetary (M)** | Total gross revenue | Higher = better (score 1–4) |

Scores are assigned by quartile (Q4 = best performance).

### K-Means Clustering (k=4)

**Elbow method** confirms k=4 as optimal: inertia drops sharply from k=1 to k=4, then flattens.

**Segment labels** (assigned by mean monetary value descending):

| Segment | Characteristics | Action |
|---|---|---|
| **Champions** | High R, F, M — recently active, frequent, high-value | Protect; early product access |
| **Potential Loyalists** | High F/M but recency slipping | Re-engagement campaign |
| **At-Risk** | Was high-value but recently dormant | Urgent outreach |
| **New / Low-Value** | Low across all three | Standard onboarding support |

**Preprocessing:** StandardScaler applied before K-Means (prevents monetary scale dominating distance).

**Random seed:** 42 for reproducibility. `n_init=10` to avoid local minima.

---

## Evaluation Summary

| Model | Metric | Target | Notes |
|---|---|---|---|
| SARIMA | MAPE (6m hold-out) | < 15% | Varies by SKU volatility |
| Isolation Forest | Precision@2% | Qualitative review | No ground-truth labels |
| K-Means | Silhouette score | > 0.3 | Checked via elbow + visual |
| Z-score | |z| threshold | 3.0 | Industry standard |
