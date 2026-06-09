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
- `infra/deployment` — deployment manifests and scripts for Railway and related infra.

This structure keeps experimentation (`notebooks`) clearly separated from production code (`src`), and cleanly isolates infrastructure, tests, and data lifecycle.

---

## Reference Pattern: Production AI App Structure

The pattern below (from a reference production AI app) captures the layered folder conventions that this project follows and should extend toward as the AI agent and serving layers mature.

```
production-ai-app/
├── app/
│   ├── main.py                        # FastAPI entry, config, schemas, containerized
│   ├── config.py
│   ├── models.py
│   ├── Dockerfile
│   ├── components/
│   │   ├── hybrid_retriever.py        # Custom retrieval: hybrid search + reranking
│   │   └── reranker.py
│   ├── services/
│   │   ├── rag_pipeline.py            # Core business logic: pipeline, cache,
│   │   ├── semantic_cache.py          #   memory, rewriting, routing
│   │   ├── conversation.py
│   │   ├── query_rewriter.py
│   │   └── query_router.py
│   ├── prompts/
│   │   ├── templates.py               # Versioned, type-specific, hot-swappable
│   │   └── registry.py
│   ├── agents/
│   │   ├── document_grader.py         # Intelligence layer: self-correcting
│   │   ├── query_decomposer.py        #   retrieval, LLM-driven source selection
│   │   ├── adaptive_router.py
│   │   └── tools/
│   │       ├── vector_search.py       # Pluggable tool definitions
│   │       ├── web_search.py
│   │       └── code_search.py
│   └── security/
│       ├── input_guard.py             # Three guard layers: input, content, output
│       ├── content_filter.py
│       └── output_filter.py
├── evaluation/
│   ├── golden_dataset.json            # Golden test set, offline + online pipelines,
│   ├── offline_eval.py                #   tracked history
│   ├── online_monitor.py
│   └── eval_results/
├── observability/
│   ├── tracer.py                      # Per-stage tracing, feedback capture,
│   ├── feedback.py                    #   cost breakdown
│   └── cost_tracker.py
├── data/
│   ├── raw/                           # Raw → processed → index config
│   ├── processed/
│   └── index_config/
├── scripts/
│   ├── seed.py                        # Seed, migrate, healthcheck
│   ├── migrate.py
│   └── healthcheck.py
├── frontend/
│   ├── app.py                         # UI, containerized separately
│   ├── static/
│   ├── requirements.txt
│   └── Dockerfile
├── tests/
│   ├── test_retrieval.py              # Retrieval, cache, routing tests. CI-ready.
│   ├── test_cache.py
│   └── test_routing.py
├── docs/
│   ├── architecture.md                # Architecture, API ref, deployment guide
│   ├── api-reference.md
│   └── deployment.md
├── .claude/
│   └── rules/
│       ├── code-style.md              # AI coding agent context, rules, project memory
│       └── testing.md
├── CLAUDE.md
├── AGENTS.md
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

### Key conventions from this pattern

- **`app/services/`** — Core business logic lives here (pipelines, caches, routing). Keep it separate from entry points (`main.py`) and data models (`models.py`).
- **`app/agents/`** — Intelligence layer (LLM-driven nodes, graders, decomposers). Tools live under `agents/tools/` as pluggable definitions.
- **`app/prompts/`** — Prompt templates are versioned and registered centrally, not scattered across nodes.
- **`app/security/`** — Guard layers (input → content → output) are explicit modules, not inline conditionals.
- **`evaluation/`** — Golden datasets and offline/online eval pipelines are first-class citizens, not afterthoughts.
- **`observability/`** — Tracing, feedback capture, and cost tracking are isolated from business logic.
- **`scripts/`** — Operational scripts (seed, migrate, healthcheck) live outside `src/` and `app/`.
- **`.claude/rules/`** — Agent coding context and project-specific rules live here for AI-assisted development.
