# syntax=docker/dockerfile:1

# ── Stage 1: install dependencies ──────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml poetry.lock ./
COPY src/ ./src/

# pip reads pyproject.toml and installs only runtime deps (not dev group)
RUN pip install --no-cache-dir .

# ── Stage 2: runtime image ──────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY src/ ./src/
COPY pyproject.toml ./

ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "fintech_ai_segmentation.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
