## Notebook Pipeline Roadmap

This roadmap follows the chronological analytical path described in `docs/fintech-ai-segmentation-summary.md`.  
Faker generates only **raw tables**; all analytical features are created step by step.

---

### Notebook 0 — Data generation (raw tables only)

- **Goal**: Use `fintech_ai_segmentation.faker_base_generation` to generate:
  - `customers_raw`
  - `transactions_raw`
  - `products_raw`
  - `customer_products_raw`
- **Outputs**:
  - In-memory pandas DataFrames for quick inspection.
  - CSV/Parquet exports for loading into Supabase.
- **Important constraint**: No RFM, LTV, churn, or cohort metrics are computed here.

---

### Notebook 1 — Base EDA (who do we have?)

- **Inputs**:
  - `customers_raw`
- **Focus**:
  - Distributions by age, state, acquisition channel, registration date.
  - Basic quality checks (duplicates, missing values, outliers).
- **Outputs**:
  - Cleaned view of `customers_raw` (e.g., standardized states/emails).
  - Business narratives: who the customers are and how they were acquired.

---

### Notebook 2 — Transactions EDA & monthly aggregates (how do they behave?)

- **Inputs**:
  - `transactions_raw` joined with `customers_raw`.
- **Focus**:
  - Transaction volume and value over time (per month, per segment, per channel).
  - Build per-customer, per-month aggregates:
    - `monthly_transactions_count`
    - `monthly_spent`
    - basic recency indicators.
- **Outputs**:
  - Intermediate aggregate tables to be reused by cohort, RFM, and unit economics notebooks.

---

### Notebook 3 — Cohort analysis (when did they arrive, how do cohorts retain?)

- **Inputs**:
  - Registration dates from `customers_raw`.
  - Activity indicators from transactions monthly aggregates.
- **Focus**:
  - Define cohorts by `cohort_month`.
  - Compute retention curves over tenure (e.g., active vs inactive by month).
- **Outputs**:
  - Cohort metrics table (e.g., `cohort_month`, `tenure_month`, `retention_rate`).
  - Features such as `cohort_retention_rate` that can later be joined back to customers.

---

### Notebook 4 — RFM scoring & clustering (behavioral segments)

- **Inputs**:
  - Per-customer aggregates from Notebook 2.
- **Focus**:
  - Compute RFM metrics:
    - `recency_days`, `frequency_transactions`, `monetary_value`.
  - Map them to discrete scores (1–5) to obtain `recency_score`, `frequency_score`, `monetary_score`, and `rfm_score`.
  - Run K-Means (or similar) to produce `predicted_segment`.
- **Outputs**:
  - Per-customer RFM table that can be joined back to `customers_raw`.

---

### Notebook 5 — Unit economics (LTV, CAC, payback)

- **Inputs**:
  - Acquisition data from `customers_raw`.
  - Revenue-related aggregates from transactions.
  - RFM / segments from Notebook 4.
- **Focus**:
  - Compute:
    - `avg_monthly_revenue`
    - `ltv`
    - `ltv_cac_ratio`
    - `payback_period_months`
- **Outputs**:
  - Per-customer unit-economics table, suitable for joining into a unified analytics view.

---

### Notebook 6 — Churn modeling (Logistic Regression)

- **Inputs**:
  - All previously engineered features (cohorts, RFM, unit economics, engagement).
- **Focus**:
  - Define a churn label from raw behavior (e.g., no transactions / logins for X months).
  - Train a Logistic Regression model to predict churn.
  - Generate `churn_probability` per customer.
- **Outputs**:
  - Final ML features and predictions that can be written back to Supabase and surfaced in the dashboard and AI agent.

