## Project Folder Structure

This project follows a standard analytics + ML + app architecture aligned with the `fintech-ai-segmentation-summary.md` design.

- `data/raw` — original synthetic data exported from Faker and any external sources.
- `data/processed` — cleaned, feature-engineered datasets ready for modeling and dashboard consumption.
- `notebooks` — Jupyter notebooks for EDA, cohort analysis, RFM, clustering, unit economics, and churn modeling.
- `src/backend` — FastAPI backend application (API endpoints, business logic, services).
- `src/frontend` — Next.js dashboard code (pages, components, charts).
- `src/agent` — LangGraph agent, Pydantic schemas, and LLM orchestration logic.
- `src/ml` — reusable ML pipeline code (feature engineering, training, evaluation, model artifacts).
- `src/api` — shared request/response models and client abstractions between services.
- `src/db` — database models and migrations (SQLAlchemy, Supabase/PostgreSQL integration).
- `src/config` — configuration, settings, and environment management.
- `tests/unit` — fast unit tests for isolated pieces of logic.
- `tests/integration` — end-to-end and API tests that span multiple layers.
- `docs` — documentation (this file plus additional guides like setup, architecture, and usage).
- `infra/docker` — Dockerfiles and local container orchestration.
- `infra/deployment` — deployment manifests and scripts for Render/Fly.io/Vercel and related infra.

This structure keeps experimentation (`notebooks`) clearly separated from production code (`src`), and cleanly isolates infrastructure, tests, and data lifecycle.
