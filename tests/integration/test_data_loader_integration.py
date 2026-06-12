"""Integration tests for scripts/data_loader.py.

These tests verify observable outcomes against a real Postgres connection.
They are skipped when SUPABASE_DATABASE_URL is not set — consistent with the
project's no-mock-database policy (see CLAUDE.md).

Run after the loader has completed at least once:
    pytest tests/integration/test_data_loader_integration.py -v

Run including the slow idempotency test:
    pytest tests/integration/test_data_loader_integration.py -v -m integration_slow
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
LOADER_SCRIPT = REPO_ROOT / "scripts" / "data_loader.py"

DB_URL = os.environ.get("SUPABASE_DATABASE_URL", "").strip()
skip_no_db = pytest.mark.skipif(
    not DB_URL,
    reason="SUPABASE_DATABASE_URL not set — skipping integration tests",
)

# Expected tables and a representative subset of required columns for each.
EXPECTED_TABLES: dict[str, list[str]] = {
    "customers_raw": [
        "customer_id",
        "age",
        "state",
        "acquisition_channel",
        "acquisition_cost",
        "registration_date",
        "true_segment",
    ],
    "products_raw": ["product_id", "product_name", "product_type"],
    "transactions_raw": [
        "transaction_id",
        "customer_id",
        "transaction_datetime",
        "amount",
        "transaction_type",
        "product_type",
        "channel",
        "status",
    ],
    "customer_products_raw": ["customer_id", "product_id", "start_date", "is_active"],
    "recommendation_log": [
        "id",
        "customer_id",
        "ip_address",
        "model_used",
        "generated_at",
        "recommendation_json",
    ],
    "cohort_activity_matrix": [
        "cohort_month",
        "activity_month",
        "active_rate",
        "cohort_size",
    ],
    "channel_m6_retention": [
        "acquisition_channel",
        "cohort_month",
        "m6_active_rate",
        "cohort_size",
    ],
    "customer_analysis": [
        "customer_id",
        "cluster_km",
        "cluster_name",
        "lifecycle_stage",
        "rfm_score",
        "recency_days",
        "tenure_months",
        "has_wallet",
        "has_credit_card",
    ],
}

CUSTOMERS_EXPECTED = 8_000
TRANSACTIONS_EXPECTED = 2_200_000
TOLERANCE = 0.05  # ±5%


@pytest.fixture(scope="module")
def engine():
    sqlalchemy = pytest.importorskip("sqlalchemy")
    eng = sqlalchemy.create_engine(DB_URL, pool_pre_ping=True)
    yield eng
    eng.dispose()


def _row_count(engine, table: str) -> int:
    from sqlalchemy import text

    with engine.connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()


def _column_names(engine, table: str) -> set[str]:
    from sqlalchemy import inspect

    insp = inspect(engine)
    return {col["name"] for col in insp.get_columns(table)}


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


@skip_no_db
def test_all_expected_tables_exist(engine) -> None:
    from sqlalchemy import inspect

    insp = inspect(engine)
    existing = set(insp.get_table_names())
    missing = set(EXPECTED_TABLES) - existing
    assert not missing, f"Tables missing from database: {missing}"


@skip_no_db
@pytest.mark.parametrize("table,columns", EXPECTED_TABLES.items())
def test_table_has_required_columns(engine, table: str, columns: list[str]) -> None:
    existing_cols = _column_names(engine, table)
    missing = set(columns) - existing_cols
    assert not missing, f"{table} is missing columns: {missing}"


# ---------------------------------------------------------------------------
# Row count tests
# ---------------------------------------------------------------------------


@skip_no_db
def test_customers_raw_row_count(engine) -> None:
    count = _row_count(engine, "customers_raw")
    lo = int(CUSTOMERS_EXPECTED * (1 - TOLERANCE))
    hi = int(CUSTOMERS_EXPECTED * (1 + TOLERANCE))
    assert (
        lo <= count <= hi
    ), f"customers_raw has {count:,} rows, expected {lo:,}–{hi:,}"


@skip_no_db
def test_transactions_raw_row_count(engine) -> None:
    count = _row_count(engine, "transactions_raw")
    lo = int(TRANSACTIONS_EXPECTED * (1 - TOLERANCE))
    hi = int(TRANSACTIONS_EXPECTED * (1 + TOLERANCE))
    assert (
        lo <= count <= hi
    ), f"transactions_raw has {count:,} rows, expected {lo:,}–{hi:,}"


@skip_no_db
def test_customer_analysis_row_count_matches_customers_raw(engine) -> None:
    customers_count = _row_count(engine, "customers_raw")
    mart_count = _row_count(engine, "customer_analysis")
    assert (
        mart_count == customers_count
    ), f"customer_analysis has {mart_count:,} rows but customers_raw has {customers_count:,}"


# ---------------------------------------------------------------------------
# Mart completeness tests
# ---------------------------------------------------------------------------


@skip_no_db
def test_active_clustered_customers_have_no_null_cluster_km(engine) -> None:
    from sqlalchemy import text

    with engine.connect() as conn:
        null_count = conn.execute(
            text(
                "SELECT COUNT(*) FROM customer_analysis "
                "WHERE lifecycle_stage = 'active_clustered' AND cluster_km IS NULL"
            )
        ).scalar()
    assert (
        null_count == 0
    ), f"{null_count} active_clustered customers have NULL cluster_km"


@skip_no_db
def test_active_clustered_customers_have_no_null_cluster_name(engine) -> None:
    from sqlalchemy import text

    with engine.connect() as conn:
        null_count = conn.execute(
            text(
                "SELECT COUNT(*) FROM customer_analysis "
                "WHERE lifecycle_stage = 'active_clustered' AND cluster_name IS NULL"
            )
        ).scalar()
    assert (
        null_count == 0
    ), f"{null_count} active_clustered customers have NULL cluster_name"


@skip_no_db
def test_active_clustered_customers_have_no_null_rfm_score(engine) -> None:
    from sqlalchemy import text

    with engine.connect() as conn:
        null_count = conn.execute(
            text(
                "SELECT COUNT(*) FROM customer_analysis "
                "WHERE lifecycle_stage = 'active_clustered' AND rfm_score IS NULL"
            )
        ).scalar()
    assert (
        null_count == 0
    ), f"{null_count} active_clustered customers have NULL rfm_score"


@skip_no_db
def test_cluster_name_values_are_valid(engine) -> None:
    from sqlalchemy import text

    valid = {"at_risk_churner", "low_value_dormant", "high_value_active"}
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT DISTINCT cluster_name FROM customer_analysis WHERE cluster_name IS NOT NULL"
            )
        ).fetchall()
    found = {r[0] for r in rows}
    unexpected = found - valid
    assert not unexpected, f"Unexpected cluster_name values: {unexpected}"


# ---------------------------------------------------------------------------
# Idempotency test (slow — runs the full loader twice)
# ---------------------------------------------------------------------------


@skip_no_db
@pytest.mark.slow
def test_loader_is_idempotent(engine) -> None:
    """Re-run the loader and assert row counts are unchanged."""
    counts_before = {t: _row_count(engine, t) for t in EXPECTED_TABLES}

    result = subprocess.run(
        [sys.executable, str(LOADER_SCRIPT)],
        capture_output=True,
        text=True,
        env={**os.environ, "SUPABASE_DATABASE_URL": DB_URL},
        timeout=1200,
    )
    assert (
        result.returncode == 0
    ), f"Loader failed on second run.\nstdout: {result.stdout[-2000:]}\nstderr: {result.stderr[-2000:]}"

    counts_after = {t: _row_count(engine, t) for t in EXPECTED_TABLES}
    for table in EXPECTED_TABLES:
        assert (
            counts_after[table] == counts_before[table]
        ), f"{table}: count changed from {counts_before[table]:,} to {counts_after[table]:,} after second run"
