# fintech-ai-segmentation
## Definitive Project Summary

---

## Problem Statement

SynaptiqPay is a Brazilian fintech with 8,000 digital wallet customers. Their commercial manager treats every customer identically — same offers, same communication, same retention strategy. This is inefficient because customers behave very differently from each other. Some are highly engaged and profitable. Others are dormant and about to leave.

Every Monday morning, the commercial manager spends 3+ hours manually analyzing spreadsheets to answer basic questions. This project replaces that workflow with an intelligent, automated dashboard — giving the manager a complete picture of the customer base in under 5 minutes, with AI-powered recommendations on what action to take for each customer.

---

## End User

**Primary:** Commercial manager / business manager at SynaptiqPay
**Interface:** Web dashboard — no code, no spreadsheets
**Core need:** Understand customers, identify risk, know what action to take

---

## The Real-World Analytical Path

The analysis follows a discovery-first narrative — each step builds on the previous one.

```
STEP 1: Who do we have?
        → EDA demographic (notebook 1)
        → Discovery-first: no segment labels used
        → Demographics, acquisition channels, CAC by channel
        → Product ownership as first behavioral signal

STEP 2: How do they behave over time?
        → Cohort + behavioral analysis (notebook 2)
        → Discovery-first: no segment labels used
        → Cohort retention (M3/M6), channel quality ranking
        → Behavioral heterogeneity, recency risk tiers,
          activation quality, product adoption curves,
          cohort revenue curves, churn proxies

STEP 3: What do we know about each customer?
        → RFM Scoring (Recency, Frequency, Monetary)
        → K-Means Clustering (k=3 operational segments)
        → Uploading clustering in a new customer_analysis mart table

STEP 4: What should we do about it?
        → LangGraph AI Agent
        → Receives segment, RFM profile, cohort health, product ownership
        → Generates personalized recommendation per customer

STEP V: Synthetic data validation (fake dataset only)
        → EDA_Validation_Fake_Dataset.ipynb
        → Primary ground-truth validation notebook
        → Confirms generator planted the right patterns
          before clustering is attempted
        → Note: Notebook 3 also loads true_segment for mart
          context but does not use it as a clustering input
```

---

## Notebook Files (Repository)

The [notebook roadmap](notebooks-roadmap.md) describes the full pipeline.

| File | Scope |
|---|---|
| `notebooks/0.Data_Generation.ipynb` | Raw tables only (`customers_raw`, `transactions_raw`, etc.) |
| `notebooks/1.EDA_demographic_analysis.ipynb` | STEP 1 — Demographics, acquisition, CAC, product ownership. No `true_segment`. |
| `notebooks/2.EDA_cohort_analysis.ipynb` | STEP 2 — Cohort retention, channel quality, 8 behavioral discovery analyses. No `true_segment`. |
| `notebooks/EDA_Validation_Fake_Dataset.ipynb` | STEP V — Ground-truth validation. Primary notebook for `true_segment` analysis. |
| `notebooks/3.EDA_RFM_Clustering.ipynb` | STEP 3 — RFM scoring, K-Means (k=3), cluster profiling, `customer_analysis` mart upload to Supabase |

---

## Business Questions To Answer

### Discovery (EDA + Cohort — no segment labels)
1. How is our customer base distributed by age, state, and acquisition channel?
2. Which acquisition channel brings customers with the broadest product portfolios?
3. Which acquisition month produces the most retained customers?
4. At what month do most customers disengage? (tenure retention curve)
5. Which acquisition channel brings the highest quality customers? (M6 retention + CAC payback)
6. Is the customer base behaviorally homogeneous or are there natural fault lines? (activity rate distribution, Pareto revenue)
7. Does early activation (M0 vs M1–M3 vs never) predict M6 retention?
8. What does the recency distribution look like — where are the natural churn risk breaks?
9. Does broader product ownership correlate with longer tenure?

### Synthetic Data Validation (EDA_Validation_Fake_Dataset.ipynb only)
10. Do segment counts match the planted 20/30/30/20 design?
11. Do age distributions by segment match generator parameters?
12. Does MAU by segment confirm expected lifecycle patterns (high_value stable, at_risk declining)?
13. Do M0–M6 retention curves separate cleanly by planted segment?
14. Does channel × segment composition explain the channel quality differences observed in STEP 2?

### Behavioral Intelligence (RFM + Clustering)
*(Notebook 3, Q6–Q10 in notebook flow)*
1. Who are our most valuable customers right now?
2. What behavioral patterns define each customer segment?
3. What is the RFM profile of each segment?
4. Do high-engagement customers own more products?
5. How does credit and investment utilization vary across segments?

### AI Intelligence (LangGraph Agent)
12. Given this customer's full profile, what product should we offer?
13. What is the best retention strategy for this specific customer?
14. What message tone and approach fits this customer's segment?

---

## Customer Segments (Ground Truth — Planted In Dataset)

| Segment | Size | Profile |
|---|---|---|
| `high_value_active` | 1,600 (20%) | High transaction frequency (~40/month), high ticket (~R$220), 95% monthly activity rate |
| `mid_value_regular` | 2,400 (30%) | Moderate frequency (~18/month), moderate ticket (~R$160), 85% monthly activity rate |
| `low_value_dormant` | 2,400 (30%) | Low frequency (~4/month), low ticket (~R$100), 40% monthly activity rate |
| `at_risk_churner` | 1,600 (20%) | Very low frequency (~2/month), very low ticket (~R$45), 15% monthly activity rate |

---

## Current Raw CSV Row Counts

| File | Rows |
|---|---:|
| `customers_raw.csv` | 8,000 |
| `transactions_raw.csv` | ~2,180,000 |
| `products_raw.csv` | 5 |
| `customer_products_raw.csv` | ~19,900 |

---

## Dataset Schema

### Raw Tables (Generated by Faker)

**`customers_raw`** — registration-time attributes only
- `customer_id` (UUID), `name`, `email`, `age`, `state`, `registration_date`
- `acquisition_channel` — paid_ads, organic, referral, partnership
- `acquisition_cost` — R$ spent to acquire this customer (channel-specific distribution)
- `true_segment` — ground-truth label planted at generation time (for model validation only)

**`transactions_raw`** — one row per transaction
- `transaction_id`, `customer_id`, `transaction_datetime`, `amount`
- `transaction_type` — purchase, transfer, cash_withdrawal, fee, refund (product-specific distributions)
- `product_type` — wallet, credit_card, investment, insurance, loan
- `channel` — in_app, card_present, online, atm (product-specific distributions)
- `status` — completed (93%), pending, failed, reversed

**`products_raw`** — static product catalog (5 rows)
- `product_id`, `product_name`, `product_type`

**`customer_products_raw`** — bridge table: what products each customer owns
- `customer_id`, `product_id`, `start_date`, `is_active`

### Derived Features (Computed in Notebooks)

From Notebook 2 (Cohort Analysis):
- `tenure_months`, `cohort_month`, `cohort_retention_rate`

From Notebook 3 (RFM + Clustering → `customer_analysis` mart):
- `recency_days`, `frequency_total`, `monetary_total`, `avg_ticket`
- `recency_score`, `frequency_score`, `monetary_score`, `rfm_score` (1–5 scale)
- `active_months_ratio`, `activity_trend_ratio`, `tx_per_active_month`
- `has_wallet`, `has_credit_card`, `has_investment`, `has_insurance`, `has_loan`
- `lifecycle_stage` — active / new_no_tx / churned
- `cluster_km` (int, k=3), `cluster_name` — K-Means segment label

---

## Synthetic Data Design

### Observation Window
- Registration period: Jan 2022 – Feb 2026 (50 months)
- Gamma(2, 360) acquisition curve: peaks around Jan 2023 (hyper-growth), decays gracefully into 2026

### Behavioral Separation (What Makes Segments Separable)
The key to meaningful RFM/clustering is **realistic inactivity** — not noise:
- `p_active_per_month` controls whether a customer transacts at all in a given month (Bernoulli)
- `avg_tx_per_active_month` controls volume when active (Poisson)
- `at_risk_churner` additionally has exponential decay: `p(active)` shrinks month-over-month
- Permanent churn is drawn from a Geometric survival model per segment

| Segment | Monthly Activity Rate | 12-Month Churn Rate |
|---|---|---|
| `high_value_active` | 95% | ~11% |
| `mid_value_regular` | 85% | ~38% |
| `low_value_dormant` | 40% | ~62% |
| `at_risk_churner` | 15% (with decay) | ~90% |

### Product-Specific Transaction Amounts
Amounts are conditioned on both segment (avg ticket) and product type:
- **Wallet**: small, frequent (~30% of segment avg ticket, R$5 minimum)
- **Credit card**: baseline (100% of avg ticket)
- **Investment**: large deposits (6× avg ticket, R$100 minimum)
- **Insurance**: fixed premium-like (60% of avg ticket)
- **Loan**: large, periodic disbursements (8× avg ticket, R$200 minimum)

### Product Ownership Signals
Product ownership encodes behavioral signals by design:
- `high_value_active`: high investment (65%) and insurance (45%) ownership
- `at_risk_churner`: high loan rate (25%) and low investment rate (10%) — financial stress signal
- Cancellation rates escalate by segment (5% → 40%), reflecting lifecycle disengagement

### Demographic Correlations
Age is mildly correlated with segment to add realism:
- `high_value_active`: mean 38 — slightly older, more affluent
- `mid_value_regular`: mean 33 — young professional
- `low_value_dormant`: mean 42 — broader range
- `at_risk_churner`: mean 27 — youngest, less financially committed

### Seasonality
Brazilian calendar effects are modeled with segment-specific sensitivity:
- November (+20%) and December (+30%): 13th salary + Black Friday
- January (−20%) and February (−15%): post-holiday hangover + Carnival
- `high_value_active`: full seasonal response; `at_risk_churner`: minimal (20% sensitivity)

---

## Tech Stack (Phase 1 MVP)

| Layer | Technology | Purpose |
|---|---|---|
| Environment | Poetry | Dependency management |
| Data generation | Faker (pt_BR) | Realistic fake customer dataset with Brazilian locale |
| Data manipulation | Pandas | EDA, RFM scoring, cohort analysis |
| Machine learning | Scikit-learn | K-Means clustering (k=3 operational segments) |
| AI Agent | LangGraph + Pydantic | Personalized recommendations |
| LLM | OpenRouter (OpenAI-compatible client) | Routes to free/smart-auto models (gemini-flash, llama-70b, mistral-7b) |
| Backend | FastAPI | REST API connecting data to frontend |
| Frontend | React + Vite + Tailwind CSS + shadcn/ui + Recharts | Business dashboard |
| Database | Supabase (PostgreSQL) | Data persistence |
| ORM | SQLAlchemy | Database interaction |
| Containerization | Docker + Docker Compose | Local + VPS deployment |
| Frontend deployment | Vercel | Free, auto-deploy on GitHub push |
| Backend deployment | Render or Fly.io | Free tier VPS |
| Version control | Git + GitHub | Source control |

---

## Architecture Flow

```
Faker
  → generates 8,000 customers with 4 planted segments
        ↓
Pandas Pipeline
  → EDA → Cohort Analysis → RFM Scoring → K-Means Clustering
        ↓
Supabase (PostgreSQL)
  → persists all customers, scores, segments, cohort metrics
        ↓
FastAPI (deployed on Render/Fly.io)
  → serves data to frontend
  → triggers LangGraph AI agent
        ↓
LangGraph Agent
  → receives customer segment, RFM profile, cohort health, product ownership
  → generates personalized recommendation
        ↓
React + Vite Dashboard (deployed on Vercel)
  → business manager interacts via browser
        ↓
Docker Compose
  → orchestrates backend + ML pipeline locally and on VPS
```

---

## LangGraph Agent Flow

```
fetch_customer_profile
        ↓
analyze_segment + cohort_context
        ↓
assess_product_ownership + behavioral_profile
        ↓
generate_recommendation
        ↓
validate_output (Pydantic)
        ↓
return structured response
```

### Agent Input (per customer)
```json
{
  "segment": "at_risk_churner",
  "rfm_score": 1.4,
  "recency_days": 92,
  "frequency_score": 1,
  "monetary_score": 1,
  "cohort_health": "weak — 38% retention at month 6",
  "products_owned": ["wallet"],
  "acquisition_channel": "paid_ads",
  "acquisition_cost": 280.0,
  "tenure_months": 8
}
```

### Agent Output
```json
{
  "risk_level": "critical",
  "recommended_action": "immediate retention offer",
  "suggested_product": "cashback credit card",
  "message_tone": "urgent, empathetic",
  "reasoning": "Customer registered via paid_ads 8 months ago (R$280 acquisition cost) and is already showing strong disengagement — only a wallet, low RFM, and 92 days since last transaction. Their cohort retains at just 38% by month 6. A targeted, low-friction credit card offer could reactivate engagement before the relationship is lost."
}
```

---

## FastAPI Endpoints (Phase 1)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/dashboard/summary` | Aggregated KPI counts (total customers, segment breakdown, at-risk count) |
| GET | `/dashboard/aggregates` | Cohort retention heatmap data + segment distribution for charts |
| GET | `/customers` | Paginated, filterable customer list |
| GET | `/customers/{id}` | Individual customer profile + RFM scores + segment |
| POST | `/customers/{id}/analyze` | Trigger LangGraph AI agent → returns structured recommendation |

## FastAPI Endpoints (Phase 2 Addition)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/chat` | Receive natural language query → return SQL + result + chart config |

---

## Frontend Pages (Phase 1)

| Page | What The Business Manager Sees |
|---|---|
| `/dashboard` | KPI cards (total customers, at-risk count, avg RFM score, segment breakdown) + segment distribution chart + cohort retention heatmap |
| `/customers` | Filterable, sortable customer table with segment badge + RFM indicator |
| `/customers/:id` | Full customer profile + RFM scores + cohort context + product ownership + AI recommendation |

---

## Phased Roadmap

### Phase 1 — MVP ✅ Complete
```
✅ Faker dataset generation (4 planted segments)
✅ EDA demographic (notebook 1) — discovery-first, no segment labels
✅ EDA cohort + behavioral discovery (notebook 2) — 8 discovery analyses
✅ Synthetic data validation (EDA_Validation_Fake_Dataset.ipynb)
✅ RFM Scoring + K-Means Clustering (k=3 operational segments)
✅ LangGraph AI Agent (4-route conditional graph, OpenRouter LLM, LangSmith tracing)
✅ FastAPI — all endpoints including dashboard/summary + dashboard/aggregates
✅ Rate limiting + recommendation log store (RateLimiter, RecommendationLogStore)
✅ React + Vite dashboard — /dashboard, /customers list, /customers/:id + AI recommendation panel
✅ Supabase write-back of derived features (customer_analysis mart)
✅ Docker + Docker Compose
✅ Deployed on Vercel (frontend) + Fly.io (backend)
```

### Phase 2 — Intelligence Layer
```
⬜ Text-to-SQL chatbot — ask any question in plain Portuguese or English
⬜ Auto-generated charts — agent decides chart type based on query result
⬜ Read-only SQL guardrails — no INSERT, UPDATE, DELETE, DROP ever executes
⬜ Clarification loop — agent asks for clarification on ambiguous questions
⬜ /chat frontend page — conversation history + suggested questions
```

### Text-to-SQL Agent Flow (Phase 2)
```
User types natural language question
        ↓
Agent receives schema context (tables, columns, relationships)
        ↓
Agent checks if question is ambiguous → asks for clarification if needed
        ↓
Agent generates read-only SQL query
        ↓
Safety layer validates query (blocks any non-SELECT statement)
        ↓
Executes against Supabase
        ↓
Agent decides best chart type for result:
  → single number     = KPI card
  → categories        = bar chart
  → time series       = line chart
  → distribution      = histogram
  → two metrics       = scatter plot
        ↓
Returns table + auto-generated Recharts visualization
```

### Example Text-to-SQL Interactions (Phase 2)
```
User: "Show me at-risk customers from São Paulo with RFM below 2"
SQL:  SELECT * FROM customers
      WHERE state = 'SP'
      AND cluster_name = 'at_risk_churner'
      AND rfm_score < 2
Chart: Sortable table + bar chart of RFM score distribution

User: "Which acquisition channel brings the most high-value customers?"
SQL:  SELECT acquisition_channel, COUNT(*) as count
      FROM customers
      WHERE cluster_name = 'high_value_active'
      GROUP BY acquisition_channel ORDER BY count DESC
Chart: Horizontal bar chart ranked by count

User: "How did customer registrations evolve month by month?"
SQL:  SELECT cohort_month, COUNT(*) as new_customers
      FROM customers GROUP BY cohort_month ORDER BY cohort_month
Chart: Line chart showing acquisition trend over time
```

### Phase 3 — Business Intelligence Expansion
```
⬜ Unit economics deep-dive (LTV, CAC, payback period by segment and channel)
⬜ Churn prediction model (Logistic Regression or Random Forest)
⬜ Feature importance dashboard
⬜ LTV/CAC heatmap (segment × channel)
```

### Phase 4 — Documentation + Polish
```
⬜ MkDocs + mkdocstrings documentation site
⬜ GitHub Pages deployment
⬜ readme-ai generated README
⬜ EDA notebook exported as HTML
⬜ Architecture diagrams
```

---

## Deployment Strategy

| Service | Platform | Cost |
|---|---|---|
| Frontend (React + Vite) | Vercel | Free |
| Backend (FastAPI + LangGraph) | Render or Fly.io | Free tier |
| Database | Supabase | Free tier |
| Documentation (Phase 4) | GitHub Pages | Free |

---

## Project Narrative (For README + Interviews)

> SynaptiqPay's commercial manager was spending 3+ hours every Monday morning analyzing spreadsheets to understand their 8,000 customers. This project replaces that workflow entirely. Through cohort analysis, we understood when and how customers arrive and at what point they disengage. Through RFM scoring and K-Means clustering, we identified 3 operational behavioral segments from the transacting population — profiling their value, activity patterns, and product utilization. Through an AI agent powered by LangGraph and Claude, we deliver a personalized, behaviorally-grounded recommendation for every single customer — automatically, in seconds. And through a Text-to-SQL chatbot, the manager can ask any question about the customer base in plain language and get an instant answer with an automatically generated chart — no analyst, no SQL, no waiting.

