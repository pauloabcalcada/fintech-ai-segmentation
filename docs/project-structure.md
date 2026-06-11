## Project Folder Structure

This project follows a standard analytics + ML + app architecture as described in `fintech-ai-segmentation-summary.md`.

```
Fintech_AI_Segmentation/
├── src/
│   └── fintech_ai_segmentation/
│       ├── __init__.py
│       ├── base_tables.py              # Pydantic schemas for raw table contracts
│       ├── faker_base_generation.py    # Synthetic data generation (Faker pt_BR)
│       ├── rfm_features.py             # RFM feature engineering pipeline
│       ├── cohort_aggregates.py        # Cohort-level aggregation logic
│       ├── agent/
│       │   ├── llm_client.py           # OpenRouter LLM client (OpenAI-compatible)
│       │   ├── prompts.py              # Prompt templates
│       │   ├── recommendation_agent.py # LangGraph agent (4-node conditional graph)
│       │   └── schemas.py              # Pydantic output schemas
│       └── app/
│           ├── main.py                 # FastAPI entry point + CORS + rate limiter
│           ├── settings.py             # Pydantic settings (env vars)
│           ├── database.py             # SQLAlchemy engine + session factory
│           ├── middleware.py           # Security middleware (DEMO_PASSWORD auth)
│           ├── client_ip.py            # Client IP extraction utility
│           ├── repositories/
│           │   ├── customer.py         # Customer queries (list, detail, mart)
│           │   ├── dashboard.py        # Aggregated KPI queries
│           │   └── recommendation.py   # Recommendation log store
│           ├── routers/
│           │   ├── customers.py        # GET /customers, GET /customers/:id, POST /customers/:id/analyze
│           │   ├── dashboard.py        # GET /dashboard/summary, GET /dashboard/aggregates
│           │   └── health.py           # GET /health
│           └── schemas/
│               ├── customer.py         # Customer request/response models
│               └── dashboard.py        # Dashboard response models
├── frontend/                           # React + Vite + Tailwind + shadcn/ui + Recharts
│   ├── src/
│   │   ├── pages/                      # Dashboard, Customers list, Customer detail
│   │   ├── components/                 # Shared UI components
│   │   ├── context/                    # React context (theme, auth)
│   │   ├── i18n/                       # Translations
│   │   └── lib/                        # API client, utilities
│   ├── public/
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   ├── nginx.conf
│   ├── vite.config.ts
│   └── package.json
├── notebooks/
│   ├── 0.Data_Generation.ipynb         # Orchestrates data gen + validation
│   ├── 1.EDA_demographic_analysis.ipynb
│   ├── 2.EDA_cohort_analysis.ipynb
│   ├── 3.EDA_RFM_Clustering.ipynb
│   ├── EDA_Validation_Fake_Dataset.ipynb
│   └── snapshots/                      # Static HTML exports of key notebook states
├── data/
│   └── raw/                            # Synthetic CSVs (customers, transactions, products, customer_products)
├── tests/
│   └── unit/                           # Unit tests (pytest)
├── supabase/
│   ├── base_schema.sql                 # Raw table DDL
│   ├── customers_analytics_view.sql    # customer_analysis mart view
│   └── phase1_app_layer.sql            # App-layer tables (recommendation_log, rate_limit)
├── scripts/
│   └── load_raw_tables.sh              # Bulk-loads raw CSVs into Supabase via psql COPY
├── docs/
│   ├── fintech-ai-segmentation-summary.md
│   ├── project-structure.md            # This file
│   ├── deployment-guide.md
│   ├── data-generation-summary.md
│   ├── kpi-dashboard-ranking.md
│   ├── project-journey.md
│   ├── security/
│   │   └── pentest-2026-06-09.md
│   └── images/
├── infra/
│   └── (future: deployment manifests, Railway config)
├── Dockerfile                          # Backend Dockerfile
├── docker-compose.yml
├── docker-compose.override.yml
├── pyproject.toml                      # Poetry config + dev dependencies
├── poetry.lock
├── CLAUDE.md
└── .env.example
```

### Layer responsibilities

- **`src/fintech_ai_segmentation/`** — All Python source: data generation, feature engineering, FastAPI app, LangGraph agent. Single package under a `src/` layout.
- **`frontend/`** — React SPA. Communicates only with the FastAPI backend; never holds DB credentials.
- **`notebooks/`** — Exploratory and analytical work. Self-contained per notebook; outputs are CSV aggregates or mart writes.
- **`supabase/`** — SQL schema and migrations. The `customer_analysis` mart is the single source of truth for the agent and dashboard.
- **`scripts/`** — Operational scripts outside `src/` (bulk load, healthcheck).
- **`tests/unit/`** — Fast, isolated pytest tests covering API endpoints, agent logic, and feature engineering.
- **`docs/`** — Project documentation and architecture references.
