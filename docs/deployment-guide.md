# Deployment Guide — Railway

SynaptiqPay runs on **Railway** — one project, two services (backend + frontend), both auto-deploying on push to `main`.

---

## Architecture

```
GitHub (main branch)
  └── push → Railway GitHub webhook
        ├── backend service  → FastAPI/uvicorn container  (port 8000)
        └── frontend service → React/Vite/nginx container (port 80)
```

| Service | Platform | Trigger |
|---------|----------|---------|
| FastAPI backend | Railway | Push to `main` via GitHub webhook |
| React + Vite frontend | Railway | Push to `main` via GitHub webhook |

---

## Cost

Railway Hobby plan gives **$5/month** of free compute credit.

| Resource | Config | Cost |
|----------|--------|------|
| Backend | Shared CPU, 512 MB RAM | ~$2–3/month |
| Frontend | nginx container, minimal idle usage | ~$0.50/month |
| **Total** | | **~$3/month (within free credit)** |

---

## What Is Already Done in the Repo

| Item | Detail |
|------|--------|
| `Dockerfile` (root) | Backend: multi-stage Python image, uvicorn on port 8000 |
| `frontend/Dockerfile` | Frontend: Node 22 build → nginx:1.27-alpine on port 80, `ARG VITE_API_BASE_URL` for build-time injection |
| `frontend/nginx.conf` | SPA routing — all paths fall back to `index.html` |
| FastAPI docs disabled in production | `/docs` and `/redoc` return 404 when `ENVIRONMENT=production` |
| No SQL injection risk | All queries use SQLAlchemy bound parameters |

---

## Step-by-Step Deployment

### Step 1 — Create a Railway account

1. Go to [railway.app](https://railway.app) and sign up with your GitHub account
2. Authorize the Railway GitHub App when prompted — grant access to the `fintech-ai-segmentation` repo

---

### Step 2 — Create a new project

1. Click **New Project** → **Empty Project**
2. Name it `synaptiqpay`

---

### Step 3 — Deploy the backend service

1. On the project canvas, click **+ New Service → GitHub Repo**
2. Select `pauloabcalcada/fintech-ai-segmentation`
3. Leave **Root Directory** blank (repo root, where `Dockerfile` lives)
4. In the **Variables** tab, add:

| Variable | Value |
|---|---|
| `SUPABASE_DATABASE_URL` | Your Supabase connection string |
| `OPENROUTER_API_KEY` | Your OpenRouter key |
| `LANGCHAIN_API_KEY` | Your LangSmith key |
| `LANGCHAIN_PROJECT` | `synaptiqpay-recommendations` |
| `MAX_PER_IP_DAILY` | `10` |
| `FRONTEND_ORIGIN` | `placeholder` (update after Step 4) |
| `ENVIRONMENT` | `production` |

5. Click **Deploy** and wait for the build to complete (~3 minutes)
6. Click **Settings → Networking → Generate Domain**, set port `8000`
7. Verify: visit `https://<backend-url>/health` → `{"status": "ok", "version": "0.1.0"}`

> **Security note:** Variables are encrypted at rest in Railway's vault and injected at container startup — never stored in the Docker image or visible in build logs.

---

### Step 4 — Deploy the frontend service

1. On the project canvas, click **+ New Service → GitHub Repo**
2. Select the same `pauloabcalcada/fintech-ai-segmentation` repo
3. Set **Root Directory** to `frontend`
4. In the **Variables** tab, add:

| Variable | Value |
|---|---|
| `VITE_API_BASE_URL` | `https://<backend-url>` from Step 3 — must include `https://` |

> **Important:** `VITE_API_BASE_URL` is baked into the JS bundle at build time by Vite. It must be set before the first build runs. If you ever change the backend URL, update this variable and redeploy the frontend.

5. Click **Deploy** and wait for the build to complete (~2 minutes)
6. Click **Settings → Networking → Generate Domain**, set port `80`
7. Copy the frontend URL — you need it in Step 5

---

### Step 5 — Wire CORS

1. Go back to the **backend** service → **Variables**
2. Update `FRONTEND_ORIGIN` from `placeholder` to your frontend Railway URL:
   ```
   https://<frontend-url>
   ```
3. Save — Railway restarts the backend automatically (~60 seconds, no rebuild)

---

### Step 6 — End-to-end verification

Open the frontend URL in the browser:

- `/dashboard` — KPI cards and charts load from the database
- `/customers` — paginated customer table loads with segment badges
- `/customers/:id` → click **Analyze** — AI recommendation panel returns a result

Open DevTools → **Network** tab and confirm all API calls go to the Railway backend URL, not `localhost`.

Push a whitespace commit to `main` — both services should show a new deployment in the Railway **Deployments** tab within 30 seconds.

---

## Re-deploying

| What changed | Action needed |
|---|---|
| Backend code (`src/`, `Dockerfile`, etc.) | Push to `main` → Railway deploys automatically |
| Frontend code (`frontend/src/`, etc.) | Push to `main` → Railway deploys automatically |
| Backend env vars | Railway dashboard → Variables → save → auto-restart |
| `VITE_API_BASE_URL` (frontend) | Update in Railway → Variables → Redeploy frontend |

---

## Adding a Custom Domain

1. Go to the service → **Settings → Networking → Custom Domain**
2. Enter your domain (e.g. `api.synaptiqpay.com`)
3. Point your DNS CNAME to the Railway-provided target
4. Railway provisions TLS automatically
5. Update `VITE_API_BASE_URL` (backend) and `FRONTEND_ORIGIN` (backend) to use the new domains, then redeploy both services

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Frontend calls `localhost:8000` | `VITE_API_BASE_URL` was not set before the build — update the variable and **Redeploy** the frontend |
| Frontend shows CORS error | `FRONTEND_ORIGIN` on the backend does not match the frontend URL exactly (no trailing slash) |
| Backend health check fails | Check the **Deployments** build log — usually a missing env var or Poetry install failure |
| `/docs` visible in production | `ENVIRONMENT` not set to `production` on the backend service |
| AI analysis returns 429 | Rate limit hit — wait until tomorrow or increase `MAX_PER_IP_DAILY` in Railway Variables |
