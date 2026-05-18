# Deployment Guide — Fly.io + Vercel

SynaptiqPay backend runs on **Fly.io** (GRU — São Paulo), frontend auto-deploys to **Vercel**.  
The first deployment is manual (from your machine). All subsequent deployments are triggered automatically by pushes to `main`.

---

## Architecture

```
GitHub (main branch)
  ├── push → .github/workflows/fly-deploy.yml → Fly.io (backend, gru region)
  └── push → Vercel GitHub integration           → Vercel CDN  (frontend)
```

| Service | Platform | Region | Trigger |
|---------|----------|--------|---------|
| FastAPI backend | Fly.io | GRU (São Paulo) | GitHub Actions on push to `main` |
| React + Vite frontend | Vercel | Global CDN | Vercel GitHub integration on push to `main` |

---

## Cost

Fly.io has no free tier. This configuration targets **~$2/month**:

| Resource | Config | Cost |
|----------|--------|------|
| Machine | 1× shared-1x CPU, 256 MB RAM | ~$1.94/month |
| IP | IPv6 only (no static IPv4) | $0 |
| Bandwidth | First 100 GB/month free | $0 |
| **Total** | | **~$1.94/month** |

FastAPI + SQLAlchemy + LangGraph idles well under 150 MB — the agent calls OpenRouter over HTTP and never loads a model into memory, so 256 MB is sufficient.

---

## What Is Already Done in the Repo

No action needed on these — they are committed and ready:

| Item | Detail |
|------|--------|
| `fly.toml` | App config: GRU region, 256 MB shared VM, `/health` check, no cold starts |
| `.github/workflows/fly-deploy.yml` | Auto-deploys backend on push to `main` |
| Multi-stage `Dockerfile` | Clean runtime image, no build tools, no `--reload` |
| `VITE_API_BASE_URL` in `frontend/src/lib/api.ts` | Reads Fly URL in production, falls back to `localhost:8000` locally |
| FastAPI docs disabled in production | `/docs` and `/redoc` return 404 when `ENVIRONMENT=production` |
| No SQL injection risk | All queries use SQLAlchemy bound parameters |

---

## Step-by-Step Deployment

### Step 1 — Create external accounts

**Fly.io** (required — has a cost)
1. Sign up at [fly.io](https://fly.io)
2. Add a credit card — required even for the ~$2/month tier
3. You will not be charged until a machine is running

**Vercel** (free)
1. Sign up at [vercel.com](https://vercel.com) with your GitHub account
2. No credit card needed for the free hobby plan

---

### Step 2 — Install the Fly CLI and authenticate

```bash
brew install flyctl
fly auth login   # opens browser to complete login
```

---

### Step 3 — Push current changes to GitHub

Vercel connects to GitHub and needs the latest code — including `fly.toml` and the GitHub Actions workflow — before you set anything up on either platform.

```bash
git add fly.toml .github/workflows/fly-deploy.yml .env.example \
        src/fintech_ai_segmentation/app/settings.py \
        src/fintech_ai_segmentation/app/middleware.py \
        src/fintech_ai_segmentation/app/routers/customers.py \
        src/fintech_ai_segmentation/app/main.py \
        frontend/src/lib/api.ts \
        frontend/src/components/AiRecommendationPanel.tsx \
        docs/deployment-guide.md
git commit -m "chore: deployment configuration and pre-deploy cleanup"
git push origin main
```

---

### Step 4 — Create a least-privilege Supabase database role

The current `SUPABASE_DATABASE_URL` uses the `postgres` superuser. Do this before deploying so you never expose superuser credentials to the live backend.

Open the **Supabase SQL editor** for your project and run:

```sql
CREATE ROLE synaptiqpay_api WITH LOGIN PASSWORD 'choose-a-strong-password';

GRANT SELECT ON
  customer_analysis,
  customers_raw,
  transactions_raw,
  products_raw,
  customer_products_raw
TO synaptiqpay_api;

GRANT SELECT, INSERT ON recommendation_log TO synaptiqpay_api;
```

Note down the connection string for this new role — you will use it in the next step instead of the superuser URL. The format is:

```
postgresql://synaptiqpay_api:<password>@aws-1-us-east-2.pooler.supabase.com:5432/postgres
```

> The host and port are the same as your current `SUPABASE_DATABASE_URL` — only the username and password change.

---

### Step 5 — Register the Fly app

Run from the **project root**. Say **no** to Postgres and Redis — the project uses Supabase.

```bash
fly launch \
  --name synaptiqpay-backend \
  --region gru \
  --no-deploy
```

`--no-deploy` registers the app name without building anything yet. If prompted to overwrite `fly.toml`, keep the existing one — it is already production-ready.

Then release the auto-allocated IPv4 (paid) and add a free IPv6:

```bash
fly ips list
fly ips release <ipv4-address>   # remove if one was allocated
fly ips allocate-v6
```

---

### Step 6 — Set Fly secrets

All secrets are encrypted and injected at runtime — never in the Docker image or `fly.toml`.

> **Note:** Skip `FRONTEND_ORIGIN` for now — you don't have the Vercel URL yet. You will add it in Step 10.

```bash
fly secrets set \
  SUPABASE_DATABASE_URL="postgresql://synaptiqpay_api:<password>@aws-1-us-east-2.pooler.supabase.com:5432/postgres" \
  OPENROUTER_API_KEY="sk-or-v1-your-key" \
  LANGCHAIN_API_KEY="your-langchain-key" \
  LANGCHAIN_PROJECT="synaptiqpay-recommendations" \
  MAX_PER_IP_DAILY="10" \
  ENVIRONMENT="production"
```

Verify (values are always redacted):

```bash
fly secrets list
```

---

### Step 7 — First deploy (from your machine)

```bash
fly deploy
```

Fly builds the Docker image remotely using `Dockerfile`, deploys to GRU, and runs the `/health` check before marking the machine live. Watch logs:

```bash
fly logs
```

---

### Step 8 — Verify the live backend

```bash
# Health check
curl https://synaptiqpay-backend.fly.dev/health
# → {"status": "ok"}

# Confirm /docs is disabled
curl -I https://synaptiqpay-backend.fly.dev/docs
# → 404

# Confirm data is reachable
curl "https://synaptiqpay-backend.fly.dev/customers?limit=1"
```

---

### Step 9 — Enable GitHub Actions auto-deploy

Generate a long-lived deploy token so GitHub can deploy on your behalf:

```bash
fly tokens create deploy -x 999999h
```

Copy the output and add it to GitHub:

> GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**  
> Name: `FLY_API_TOKEN` | Value: *(paste token)*

From this point on, every push to `main` that touches `src/`, `Dockerfile`, `pyproject.toml`, `poetry.lock`, or `fly.toml` triggers an automatic backend deploy.

---

### Step 10 — Connect repo to Vercel and deploy frontend

1. Go to [vercel.com/new](https://vercel.com/new)
2. **Import Git Repository** → `pauloabcalcada/fintech-ai-segmentation`
3. In **Configure Project**:
   - **Root Directory**: `frontend` ← click "Edit" to set this
   - **Framework Preset**: Vite (auto-detected)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Add environment variable:

| Name | Value | Environments |
|------|-------|--------------|
| `VITE_API_BASE_URL` | `https://synaptiqpay-backend.fly.dev` | Production, Preview, Development |

5. Click **Deploy**

Vercel will give you a live URL — typically `https://synaptiqpay-frontend.vercel.app` or a variant with a random suffix. Note it down.

---

### Step 11 — Set FRONTEND_ORIGIN on Fly

Now that you have the Vercel URL, update the CORS allowlist on the backend:

```bash
fly secrets set FRONTEND_ORIGIN="https://synaptiqpay-frontend.vercel.app"
```

This triggers an automatic rolling restart. CORS will now allow requests from the deployed frontend.

---

### Step 12 — Enable Supabase Row Level Security (RLS)

Enabling RLS adds a safety net for Phase 2, when the Supabase REST API may be used directly.

In the Supabase dashboard:  
**Table Editor** → select each table → **RLS** → **Enable Row Level Security**

The backend connects via direct Postgres (bypasses RLS), so this does not affect current functionality.

---

### Step 13 — End-to-end verification

```bash
# Backend health
curl https://synaptiqpay-backend.fly.dev/health
# → {"status": "ok"}

# /docs disabled
curl -I https://synaptiqpay-backend.fly.dev/docs
# → 404

# Full round-trip: AI analysis (replace <uuid> with a real customer_id from your DB)
curl -X POST https://synaptiqpay-backend.fly.dev/customers/<uuid>/analyze \
  -H "Content-Type: application/json" \
  -d '{"model": "gemini-flash-free"}'
# → {"cached": false, "recommendation": {...}}

# No secrets in the repo
git grep -r "sk-or-v1\|postgresql://postgres\." -- ':!.env.example' ':!docs/'
# → must return nothing
```

Open the Vercel URL in the browser, open DevTools → Network tab, and confirm all API calls go to `fly.dev`, not `localhost`.

Push a whitespace commit to `main` and confirm:
- GitHub → **Actions** tab shows the `fly-deploy` job running
- Vercel Dashboard shows a new deployment triggered

---

## Re-deploying

| What changed | Action needed |
|---|---|
| Backend code (`src/`, `Dockerfile`, etc.) | Push to `main` → GitHub Action deploys automatically |
| Frontend code (`frontend/src/`, etc.) | Push to `main` → Vercel deploys automatically |
| Fly secrets | `fly secrets set KEY="value"` — triggers automatic restart |
| Vercel env vars | Vercel Dashboard → Settings → Environment Variables → redeploy |

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| `fly deploy` fails at build | `fly logs` — usually a missing dependency in `pyproject.toml` |
| `/health` returns 503 | `fly status` → `fly machine start` if stopped |
| Frontend shows CORS error | `FRONTEND_ORIGIN` on Fly does not match the Vercel URL exactly (no trailing slash) |
| GitHub Action fails with auth error | `FLY_API_TOKEN` not set or expired — run `fly tokens create deploy` and update the secret |
| Vercel build fails | Check build logs — most likely wrong Root Directory (must be `frontend`) |
| `/docs` still visible in production | `ENVIRONMENT` secret not set to `production` on Fly |
| AI analysis returns 429 | Rate limit hit — wait until tomorrow or increase `MAX_PER_IP_DAILY` via `fly secrets set` |
