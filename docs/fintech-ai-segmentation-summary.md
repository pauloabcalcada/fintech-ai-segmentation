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

The analysis follows a logical, sequential narrative — each step building on the previous one:

```
STEP 1: Who do we have?
        → EDA — demographics, acquisition channels, basic distributions

STEP 2: How did they arrive and when?
        → Cohort Analysis
        → Groups customers by registration month
        → Gives temporal context to all subsequent analysis

STEP 3: How do they behave?
        → RFM Scoring (Recency, Frequency, Monetary)
        → K-Means Clustering (4 behavioral segments)
        → Enriched by cohort context

STEP 4: How valuable are they?
        → LTV (Lifetime Value)
        → CAC (Customer Acquisition Cost)
        → Unit Economics (LTV/CAC ratio + payback period)

STEP 5: Who is at risk of leaving?
        → Churn Prediction Model (Logistic Regression)
        → Uses cohort + RFM + cluster + LTV as features
        → Produces churn_probability per customer (0-1)

STEP 6: What should we do about it?
        → LangGraph AI Agent
        → Receives ALL context from steps 1-5
        → Generates personalized, financially-grounded recommendation
```

---

## Notebook files (repository)

The [notebook roadmap](notebooks-roadmap.md) describes the full pipeline. **`notebooks/2.EDA_cohort_analysis.ipynb` is Notebook 2** and covers both **transaction EDA / monthly aggregates** and **cohort retention** (the roadmap used to describe those as two consecutive steps; they are one file with three parts).

| File | Scope |
|---|---|
| `notebooks/0.Data_Generation.ipynb` | Raw tables only (`customers_raw`, `transactions_raw`, etc.) |
| `notebooks/1.EDA_demographic_analysis.ipynb` | Base EDA — demographics, acquisition, quality checks |
| `notebooks/2.EDA_cohort_analysis.ipynb` | Notebook 2 — joins, calendar-time transaction EDA, cohort KPIs and roadmap questions Q2–Q5 |

Downstream steps (RFM, unit economics, churn) are planned as separate notebooks; the next roadmap step is Notebook 3 (RFM). See `docs/notebooks-roadmap.md`.

---

## Business Questions To Answer

### Foundation (EDA + Cohort)
1. How is our customer base distributed by age, state, and acquisition channel?
2. Which acquisition month produces the most retained customers?
3. At what month do most customers disengage?
4. Are recent cohorts healthier than older ones?
5. Which acquisition channel brings the highest quality customers?

### Behavioral Intelligence (RFM + Clustering)
6. Who are our most valuable customers right now?
7. What behavioral patterns define each customer segment?
8. What is the RFM profile of each segment?
9. Do high-engagement customers own more products?
10. How does credit utilization vary across segments?

### Business Intelligence (Unit Economics)
11. What is the predicted lifetime value per segment?
12. Which acquisition channel brings the highest LTV customers?
13. Which customer segments are unprofitable after CAC?
14. How long until each cohort pays back its acquisition cost?
15. Are high RFM score customers always the most profitable?
16. How do unit economics (LTV, CAC, LTV/CAC, payback) vary by product_type?

### Predictive Intelligence (Churn)
16. What percentage of our customer base is at churn risk?
17. Which variables correlate most strongly with churn?
18. Which features matter most for predicting churn?
19. Did K-Means successfully recover the segments we planted?

### AI Intelligence (LangGraph Agent)
20. Given this customer's full profile, what product should we offer?
21. What is the best retention strategy for this specific customer?
22. What message tone and approach fits this customer's segment?

---

## Customer Segments (Ground Truth — Planted In Dataset)

| Segment | Size | Profile |
|---|---|---|
| `high_value_active` | 1,600 (20%) | High balance, many transactions, very engaged |
| `mid_value_regular` | 2,400 (30%) | Medium balance, regular transactions, moderately engaged |
| `low_value_dormant` | 2,400 (30%) | Low balance, rare transactions, low engagement |
| `at_risk_churner` | 1,600 (20%) | Near-zero balance, almost inactive, high churn signal |

---

## Current Raw CSV Row Counts (2026-03-24)

| File | Rows |
|---|---:|
| `customers_raw.csv` | 8,000 |
| `transactions_raw.csv` | 1,485,670 |
| `products_raw.csv` | 5 |
| `customer_products_raw.csv` | 19,659 |

`transactions_raw.csv` is also split for easier Supabase import:

| File | Rows |
|---|---:|
| `transactions_raw_part1.csv` | 495,224 |
| `transactions_raw_part2.csv` | 495,223 |
| `transactions_raw_part3.csv` | 495,223 |

---

## Dataset Schema (~32 columns)

### Identity & Metadata
- `customer_id` (UUID), `name`, `email`, `age`, `state`, `registration_date`
- `acquisition_channel` — paid_ads, organic, referral, partnership
- `acquisition_cost` — R$ spent to acquire this customer

### Financial Behavior
- `avg_monthly_balance`, `avg_transaction_ticket`, `monthly_transactions_count`
- `total_spent_12m`, `total_deposits_12m`, `credit_limit`, `credit_utilization_pct`
- `avg_monthly_revenue` — revenue SynaptiqPay generates from this customer

### Transaction-Level Data
- `transaction_datetime`, `amount`, `transaction_type`, `product_type`, `channel`, `status`

### Recency & Engagement
- `days_since_last_transaction`, `days_since_last_login`
- `monthly_app_logins`, `support_tickets_6m`

### Product Ownership
- `products_owned`, `has_credit_card`, `has_investments`, `has_insurance`, `has_loans`

### Derived Scores (calculated, not generated)
- `tenure_months` — derived from registration_date
- `recency_score`, `frequency_score`, `monetary_score`, `rfm_score` — 1-5 scale
- `cohort_month` — registration month label (e.g. "2023-01")
- `cohort_retention_rate` — retention rate of this customer's cohort at their tenure month
- `predicted_segment` — K-Means output
- `true_segment` — ground truth label for model validation
- `ltv` — avg_monthly_revenue × (1 / churn_probability) × gross_margin
- `ltv_cac_ratio` — ltv / acquisition_cost
- `payback_period_months` — acquisition_cost / avg_monthly_revenue
- `churn_probability` — Logistic Regression output (0-1)

---

## Tech Stack (Phase 1 MVP)

| Layer | Technology | Purpose |
|---|---|---|
| Environment | Poetry | Dependency management |
| Data generation | Faker | Realistic fake customer dataset |
| Data manipulation | Pandas | EDA, RFM, cohort, unit economics |
| Machine learning | Scikit-learn | K-Means clustering + Logistic Regression |
| AI Agent | LangGraph + Pydantic | Personalized recommendations |
| LLM | Anthropic Claude API (claude-sonnet-4-20250514) | Language model |
| Backend | FastAPI | REST API connecting data to frontend |
| Frontend | Next.js + Tailwind CSS + shadcn/ui + Recharts | Business dashboard |
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
  → EDA → Cohort Analysis → RFM Scoring → K-Means → Unit Economics → Churn Model
        ↓
Supabase (PostgreSQL)
  → persists all customers, scores, segments, cohort metrics
        ↓
FastAPI (deployed on Render/Fly.io)
  → serves data to frontend
  → triggers LangGraph AI agent
        ↓
LangGraph Agent
  → receives full customer context
  → generates personalized recommendation
        ↓
Next.js Dashboard (deployed on Vercel)
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
calculate_ltv_and_unit_economics
        ↓
assess_churn_risk
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
  "cohort_health": "weak — 38% retention at month 6",
  "ltv": "R$320",
  "cac": "R$280",
  "ltv_cac_ratio": "1.1x",
  "payback_period": "14 months",
  "churn_probability": 0.87
}
```

### Agent Output
```json
{
  "risk_level": "critical",
  "recommended_action": "immediate retention offer",
  "suggested_product": "cashback credit card",
  "message_tone": "urgent, empathetic",
  "reasoning": "Customer is barely profitable (LTV/CAC 1.1x) and highly likely to churn. A low-cost retention offer is justified — losing this customer at this stage means negative ROI on acquisition spend."
}
```

---

## FastAPI Endpoints (Phase 1)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/dashboard` | Aggregated KPI metrics for homepage |
| GET | `/customers` | Paginated, filterable customer list |
| GET | `/customers/{id}` | Individual customer profile + all scores |
| POST | `/customers/{id}/analyze` | Trigger LangGraph AI agent |

## FastAPI Endpoints (Phase 2 Addition)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/chat` | Receive natural language query → return SQL + result + chart config |

---

## Frontend Pages (Phase 1)

| Page | What The Business Manager Sees |
|---|---|
| `/dashboard` | KPI cards (total customers, at-risk count, avg LTV, avg churn probability) + segment distribution chart + cohort retention heatmap |
| `/customers` | Filterable, sortable customer table with segment badge + churn risk indicator |
| `/customers/[id]` | Full customer profile + RFM scores + unit economics + churn probability + AI recommendation |

---

## Phased Roadmap

### Phase 1 — MVP (Build First, Ship Fast)
```
✅ Faker dataset generation (4 planted segments)
✅ EDA
✅ Cohort Analysis
✅ RFM Scoring
✅ K-Means Clustering
✅ Unit Economics (LTV, CAC, LTV/CAC, payback period)
✅ Churn Prediction (Logistic Regression)
✅ LangGraph AI Agent
✅ FastAPI (4 endpoints)
✅ Next.js dashboard (3 pages)
✅ Supabase persistence
✅ Docker
✅ Deployed on Vercel + Render/Fly.io
```

### Phase 2 — Intelligence Layer
```
⬜ Text-to-SQL chatbot — ask any question in plain Portuguese or English
⬜ Auto-generated charts — agent decides chart type based on query result
⬜ Read-only SQL guardrails — no INSERT, UPDATE, DELETE, DROP ever executes
⬜ Clarification loop — agent asks for clarification on ambiguous questions
⬜ /chat frontend page — conversation history + suggested questions
⬜ Random Forest churn model (challenger to Logistic Regression)
⬜ Feature importance dashboard
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
User: "Show me at-risk customers from São Paulo with churn above 80%"
SQL:  SELECT * FROM customers
      WHERE state = 'SP'
      AND predicted_segment = 'at_risk_churner'
      AND churn_probability > 0.80
Chart: Sortable table + bar chart of churn probability distribution

User: "Which acquisition channel has the best LTV/CAC ratio?"
SQL:  SELECT acquisition_channel, AVG(ltv_cac_ratio) as avg_ratio
      FROM customers GROUP BY acquisition_channel ORDER BY avg_ratio DESC
Chart: Horizontal bar chart ranked by ratio

User: "How did customer registrations evolve month by month?"
SQL:  SELECT cohort_month, COUNT(*) as new_customers
      FROM customers GROUP BY cohort_month ORDER BY cohort_month
Chart: Line chart showing acquisition trend over time
```

### Phase 3 — Business Intelligence Expansion
```
⬜ Unit economics deep-dive page
⬜ Acquisition channel profitability analysis
⬜ Payback period by cohort visualization
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
| Frontend (Next.js) | Vercel | Free |
| Backend (FastAPI + LangGraph) | Render or Fly.io | Free tier |
| Database | Supabase | Free tier |
| Documentation (Phase 4) | GitHub Pages | Free |

---

## Project Narrative (For README + Interviews)

> SynaptiqPay's commercial manager was spending 3+ hours every Monday morning analyzing spreadsheets to understand their 8,000 customers. This project replaces that workflow entirely. Through cohort analysis, we understood when and how customers arrive. Through RFM scoring and K-Means clustering, we discovered 4 distinct behavioral segments. Through unit economics, we identified which segments are truly profitable after acquisition costs. Through churn prediction, we flagged the 20% of customers most likely to leave. Through an AI agent powered by LangGraph and Claude, we deliver a personalized, financially-grounded recommendation for every single customer — automatically, in seconds. And through a Text-to-SQL chatbot, the manager can ask any question about the customer base in plain language and get an instant answer with an automatically generated chart — no analyst, no SQL, no waiting.
