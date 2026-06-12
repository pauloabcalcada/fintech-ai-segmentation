# Local Setup

This guide takes you from a fresh fork to a fully running local instance. The only tool you need on your machine is Docker Desktop. No Python, Node, Poetry, or `psql` installation required.

---

## 1. Prerequisites

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and make sure it is running before you continue.

---

## 2. Create accounts

You need three free accounts. Create each one before filling in the environment file.

### Supabase (database)

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard) and create a free account.
2. Create a new project. Choose a region close to you (US East works well).
3. Once the project is ready, open **Project Settings → Database → Connection string**.
4. Select **Session mode** and **port 5432**. Copy the connection string — it looks like:
   ```
   postgresql://postgres.[project-ref]:[password]@aws-1-us-east-2.pooler.supabase.com:5432/postgres
   ```
5. Replace `[YOUR-PASSWORD]` with your project password before pasting it into `.env`.

### OpenRouter (LLM routing)

1. Go to [openrouter.ai](https://openrouter.ai) and create a free account.
2. Navigate to **API Keys** and generate a new key.
3. Copy the key — it starts with `sk-or-v1-`.

### LangSmith (tracing)

1. Go to [smith.langchain.com](https://smith.langchain.com) and create a free account.
2. Create a new project (any name — e.g. `synaptiqpay`).
3. Navigate to **Settings → API Keys** and copy your API key.
4. Note the project name you chose.

---

## 3. Environment setup

Copy the example file and fill in the four required values:

```bash
cp .env.example .env
```

Open `.env` and set these four variables:

| Variable | Where to find it | What breaks if left blank |
|---|---|---|
| `SUPABASE_DATABASE_URL` | Supabase → Project Settings → Database → Session mode, port 5432 | All stages fail immediately |
| `OPENROUTER_API_KEY` | OpenRouter → API Keys | AI recommendations return an error |
| `LANGCHAIN_API_KEY` | LangSmith → Settings → API Keys | Tracing is disabled; the app still works |
| `LANGCHAIN_PROJECT` | The project name you created in LangSmith | Traces go to the default project |

Leave all other variables at their default values for local development.

---

## 4. Database and data setup

Run the data loader. This is a one-shot command that sets up everything:

```bash
docker compose run --rm data-loader
```

What it does, in order:

- **Stage 1 (schema)** — Creates all Supabase tables from the SQL files in `supabase/`. Safe to re-run.
- **Stage 2 (generation)** — Generates 8,000 synthetic customers and approximately 2.2 million transactions using Faker. Writes CSVs to `data/raw/`.
- **Stage 3 (load)** — Bulk-loads all four raw tables into Supabase using the PostgreSQL COPY protocol.
- **Stage 4 (mart)** — Computes RFM scores, fits K-Means (k=3), and writes the `customer_analysis` mart. The dashboard and AI agent read from this table.

Expected progress output:

```
==> [Stage 1/4] Schema setup
    Dropping raw tables (reverse FK order)...
    Executing base_schema.sql...
    Executing phase1_app_layer.sql...
    Executing customer_analysis_schema.sql...
    Schema ready.

==> [Stage 2/4] Generating synthetic data (Faker)
    customers_raw: 8,000 rows → customers_raw.csv
    transactions_raw: ~2,200,000 rows → transactions_raw.csv
    ...

==> [Stage 3/4] Loading raw tables via COPY protocol (FK order)
    Loading products_raw from products_raw.csv...
    products_raw: 5 rows loaded
    ...
    transactions_raw: ~2,200,000 rows loaded
    Raw tables loaded.

==> [Stage 4/4] Computing RFM scores, K-Means clustering, writing mart
    ...
    Done. 8,000 rows written.

Data loader complete. Run `docker compose up` to start the app.
```

Estimated runtime: 2 to 4 minutes for data generation, 1 to 2 minutes for the COPY load, 2 to 4 minutes for RFM and clustering. Total is roughly 5 to 10 minutes depending on your machine and Supabase region.

---

## 5. Start the app

```bash
docker compose up
```

Once both containers are running:

| URL | What you get |
|---|---|
| `http://localhost` | React dashboard (customer list, segments, AI recommendations) |
| `http://localhost:8000/docs` | FastAPI interactive docs |

---

## 6. Troubleshooting

**`SUPABASE_DATABASE_URL` missing or wrong**

The loader exits immediately with:
```
ERROR: SUPABASE_DATABASE_URL is not set.
```
Check that the value in `.env` is not wrapped in extra quotes and that you copied the Session mode connection string (port 5432), not the Transaction pooler (port 6543).

**Wrong Supabase connection string mode**

If you copied the Transaction pooler URL (port 6543), you will see a connection error during Stage 1. Go back to Project Settings → Database, select Session mode, and copy that URL instead.

**Port 80 or 8000 already in use**

Docker will fail to bind the port. Stop whatever is using it (`lsof -i :80` or `lsof -i :8000`) or change the port mapping in `docker-compose.yml`.

**Docker is not running**

You will see `Cannot connect to the Docker daemon`. Open Docker Desktop and wait for it to finish starting before running any `docker compose` commands.

---

## Deploying to production

This guide covers local setup only. For step-by-step instructions on deploying to Railway (the platform this project runs on), see [docs/deployment-guide.md](docs/deployment-guide.md).
