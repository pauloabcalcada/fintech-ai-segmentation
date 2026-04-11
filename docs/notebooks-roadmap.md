## Notebook Pipeline Roadmap

This roadmap follows the chronological analytical path described in `docs/fintech-ai-segmentation-summary.md`.  
Faker generates only **raw tables**; all analytical features are created step by step.

---

### Notebook 0 — Data Generation (raw tables only)

- **Goal**: Use `fintech_ai_segmentation.faker_base_generation` to generate:
  - `customers_raw`
  - `transactions_raw`
  - `products_raw`
  - `customer_products_raw`
- **Outputs**:
  - In-memory pandas DataFrames for quick inspection.
  - CSV exports to `data/raw/` for loading into Supabase.
- **Important constraint**: No RFM, cohort metrics, or cluster labels are computed here.
- **Generator highlights**:
  - 8,000 customers across 4 planted segments; registration dates follow a Gamma(2, 360) acquisition curve (Jan 2022 – Feb 2026).
  - Per-customer monthly activity drawn from Bernoulli (`p_active_per_month`) + Poisson (`avg_tx`), not uniform scattering — this is what creates realistic inactivity gaps.
  - Permanent churn drawn from a Geometric survival model per segment (hazards: 1% → 4% → 8% → 18%/month).
  - Transaction amounts conditioned on both segment (avg ticket) and product type (wallet = small, investment = large deposits, loan = large disbursements).
  - Product ownership encodes behavioral signals: `at_risk_churner` has higher loan probability and lower investment probability.
  - `validate_base_tables_consistency()` runs automatically after generation to ensure every transaction references a valid, active product for that customer.

---

### Notebook 1 — Base EDA (who do we have?)

- **Inputs**:
  - `customers_raw`
- **Focus**:
  - Distributions by age, state, acquisition channel, registration date.
  - Acquisition channel quality — which channels skew toward which segments.
  - Basic quality checks (duplicates, missing values, outliers).
- **Outputs**:
  - Business narratives: who the customers are and how they were acquired.
  - Channel economics: acquisition cost (CAC) by channel and segment mix.

---

### Notebook 2 — Cohort Analysis (transactions + cohorts)

Both **transaction behavior** and **cohort retention** are implemented in this single notebook (three parts: data loading & joins → monthly aggregates & calendar-time EDA → cohort analysis).

#### Part 1 — Transactions EDA & monthly aggregates

- **Inputs**:
  - `transactions_raw` joined with `customers_raw`.
- **Focus**:
  - Transaction volume and value over time (per month, per segment, per channel).
  - Per-customer, per-month aggregates: `monthly_transactions_count`, `monthly_spent`, recency indicators.
  - Seasonality patterns in TPV (Nov/Dec peaks, Jan/Feb lulls).
- **Outputs**:
  - Per-customer monthly aggregate table, reused by Notebook 3.

#### Part 2 — Cohort Analysis

- **Inputs**:
  - Registration dates from `customers_raw`.
  - Activity indicators from the monthly aggregates above.
- **Focus**:
  - Define cohorts by `cohort_month` (registration month).
  - Compute M0, M1, M3, M6 retention curves (strict-streak and ever-active KPIs).
  - Channel quality ranking by M6 first-month-active rate.
- **Outputs**:
  - Cohort metrics table: `cohort_month`, `tenure_month`, `retention_rate`.
  - `cohort_retention_rate` feature joinable back to individual customers.

---

### Notebook 3 — RFM Scoring & Clustering (behavioral segments)

- **Inputs**:
  - Per-customer aggregates from Notebook 2.
  - `customers_raw` for demographic enrichment.
- **Focus**:
  - Compute RFM metrics:
    - `recency_days` — days since last transaction (observation window: Apr 2024 – Feb 2026)
    - `frequency_transactions` — total transactions in the window
    - `monetary_value` — total spend in the window
  - Map to discrete scores (1–5): `recency_score`, `frequency_score`, `monetary_score`, `rfm_score`.
  - Run K-Means (k=4) to produce `predicted_segment`.
  - **Cluster validation**: compare `predicted_segment` to `true_segment` — did the model recover the planted segments?
  - Behavioral cross-slices: product composition, monetary type shares, and cohort health by cluster.
- **Outputs**:
  - Per-customer RFM table with `predicted_segment` ready for the AI agent.
  - Validation report: confusion matrix and ARI score vs. ground truth.

---

### What Comes Next (Phase 1 Completion)

After Notebook 3, the analytical pipeline is complete. The next deliverables are:

1. **LangGraph AI Agent** — receives per-customer RFM profile, segment, cohort health, and product ownership; outputs a personalized recommendation.
2. **FastAPI backend** — serves customer data and triggers the agent.
3. **Next.js dashboard** — the commercial manager's interface (3 pages: `/dashboard`, `/customers`, `/customers/[id]`).
4. **Supabase write-back** — derived features (RFM scores, `predicted_segment`) persisted alongside raw tables.

See `docs/fintech-ai-segmentation-summary.md` for the full roadmap including Phase 2 (Text-to-SQL) and Phase 3 (unit economics, churn modeling).
