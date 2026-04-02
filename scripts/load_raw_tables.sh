#!/usr/bin/env bash
# Reload all SynaptiqPay raw tables into Supabase from local CSV files.
#
# Steps performed:
#   1. Drop tables if they exist  (reverse FK order)
#   2. Re-create tables from supabase/base_schema.sql (CREATE TABLE IF NOT EXISTS)
#   3. Load CSVs via COPY protocol (FK dependency order)
#
# Usage (from project root):
#   bash scripts/load_raw_tables.sh
#
# Prerequisites:
#   - psql installed  (brew install libpq && brew link --force libpq)
#   - .env file at project root containing SUPABASE_DATABASE_URL
#   - data/raw/*.csv files already generated (run notebook 0.Data_Generation.ipynb first)

set -euo pipefail

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RAW_DIR="$PROJECT_ROOT/data/raw"
SCHEMA_FILE="$PROJECT_ROOT/supabase/base_schema.sql"

# ── Load .env ─────────────────────────────────────────────────────────────────
ENV_FILE="$PROJECT_ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: .env not found at $ENV_FILE"
    exit 1
fi

# Export only KEY=VALUE lines (ignores comments and blank lines).
# NOTE: If the value in .env is wrapped in double quotes (e.g. KEY="value"),
# the grep+source approach may not strip them correctly and the check below
# will fail even though the variable looks set.
# In that case, export the variable manually before running this script:
#
#   export SUPABASE_DATABASE_URL="postgresql://..."
#   bash scripts/load_raw_tables.sh
#
set -a
# shellcheck disable=SC1090
source <(grep -E '^[A-Z_]+=.+' "$ENV_FILE")
set +a

if [ -z "${SUPABASE_DATABASE_URL:-}" ]; then
    echo "ERROR: SUPABASE_DATABASE_URL not set in .env"
    echo "Try: export SUPABASE_DATABASE_URL=\"<your-url>\" && bash scripts/load_raw_tables.sh"
    exit 1
fi

PGURL="$SUPABASE_DATABASE_URL"

# ── Helper ────────────────────────────────────────────────────────────────────
run_sql() {
    psql "$PGURL" -v ON_ERROR_STOP=1 -c "SET statement_timeout = 0; SET lock_timeout = 0; $1"
}

echo ""
echo "==> [1/3] Dropping existing tables (reverse FK order)..."
run_sql "
DROP TABLE IF EXISTS customer_products_raw;
DROP TABLE IF EXISTS transactions_raw;
DROP TABLE IF EXISTS products_raw;
DROP TABLE IF EXISTS customers_raw;
"

echo ""
echo "==> [2/3] Creating tables from schema..."
psql "$PGURL" -v ON_ERROR_STOP=1 -f "$SCHEMA_FILE"

echo ""
echo "==> [3/3] Loading CSV files..."

echo "    customers_raw..."
psql "$PGURL" -v ON_ERROR_STOP=1 \
    -c "\COPY customers_raw FROM '$RAW_DIR/customers_raw.csv' WITH (FORMAT CSV, HEADER true)"

echo "    products_raw..."
psql "$PGURL" -v ON_ERROR_STOP=1 \
    -c "\COPY products_raw FROM '$RAW_DIR/products_raw.csv' WITH (FORMAT CSV, HEADER true)"

echo "    transactions_raw (~1.5M rows, may take 30-90s)..."
psql "$PGURL" -v ON_ERROR_STOP=1 \
    -c "\COPY transactions_raw FROM '$RAW_DIR/transactions_raw.csv' WITH (FORMAT CSV, HEADER true)"

echo "    customer_products_raw..."
psql "$PGURL" -v ON_ERROR_STOP=1 \
    -c "\COPY customer_products_raw FROM '$RAW_DIR/customer_products_raw.csv' WITH (FORMAT CSV, HEADER true)"

echo ""
echo "Done. All raw tables reloaded successfully."
