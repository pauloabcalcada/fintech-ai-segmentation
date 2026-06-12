"""Data loader: runs all four setup stages inside the backend Docker container.

Stage 1 — Schema:    create all tables from SQL files in dependency order
Stage 2 — Generate:  produce synthetic data via Faker and write CSVs to data/raw/
Stage 3 — Load:      bulk-load raw tables via COPY protocol (FK order)
Stage 4 — Mart:      compute RFM scores, K-Means clustering, write customer_analysis

Run:
    python scripts/data_loader.py

Requires SUPABASE_DATABASE_URL in the environment (or .env file).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Stage 4 helpers — imported here so _ts_naive / _build_mart can use them as globals.
# Placed after __future__ but before sys.path mutation so isort keeps them.
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

PROJECT_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

RAW_DIR = PROJECT_ROOT / "data" / "raw"
SUPABASE_DIR = PROJECT_ROOT / "supabase"

SCHEMA_FILES = [
    SUPABASE_DIR / "base_schema.sql",
    SUPABASE_DIR / "phase1_app_layer.sql",
    SUPABASE_DIR / "customer_analysis_schema.sql",
]

# FK dependency order for drop (reverse) and load (forward)
RAW_TABLES = [
    "products_raw",
    "customers_raw",
    "customer_products_raw",
    "transactions_raw",
]

CSV_NAMES = {
    "customers_raw": "customers_raw.csv",
    "transactions_raw": "transactions_raw.csv",
    "products_raw": "products_raw.csv",
    "customer_products_raw": "customer_products_raw.csv",
}


def _get_db_url() -> str:
    url = os.environ.get("SUPABASE_DATABASE_URL", "").strip()
    if not url:
        print(
            "ERROR: SUPABASE_DATABASE_URL is not set.\n"
            "Add it to your .env file or export it before running this script.\n"
            "Example: SUPABASE_DATABASE_URL=postgresql://user:pass@host:5432/db",
            file=sys.stderr,
        )
        sys.exit(1)
    return url


def _connect(url: str):
    try:
        import psycopg2

        conn = psycopg2.connect(url)
        conn.autocommit = True
        return conn
    except Exception as exc:
        print(
            f"ERROR: Could not connect to the database.\n"
            f"Check that SUPABASE_DATABASE_URL is correct and the host is reachable.\n"
            f"Details: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Stage 1 — Schema
# ---------------------------------------------------------------------------


def run_schema(conn) -> None:
    print("\n==> [Stage 1/4] Schema setup")
    with conn.cursor() as cur:
        # Drop raw tables in reverse FK order so recreate is clean
        print("    Dropping raw tables (reverse FK order)...")
        cur.execute("""
            DROP TABLE IF EXISTS customer_products_raw CASCADE;
            DROP TABLE IF EXISTS transactions_raw CASCADE;
            DROP TABLE IF EXISTS customers_raw CASCADE;
            DROP TABLE IF EXISTS products_raw CASCADE;
        """)
        for sql_file in SCHEMA_FILES:
            print(f"    Executing {sql_file.name}...")
            cur.execute(sql_file.read_text())
    print("    Schema ready.")


# ---------------------------------------------------------------------------
# Stage 2 — Generation
# ---------------------------------------------------------------------------


def run_generation() -> dict:
    print("\n==> [Stage 2/4] Generating synthetic data (Faker)")
    from fintech_ai_segmentation.faker_base_generation import generate_all_base_tables

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    tables = generate_all_base_tables()

    for name, df in tables.items():
        path = RAW_DIR / CSV_NAMES[name]
        df.to_csv(path, index=False)
        print(f"    {name}: {len(df):,} rows → {path.name}")

    return tables


# ---------------------------------------------------------------------------
# Stage 3 — Load raw tables via COPY
# ---------------------------------------------------------------------------


def run_load(conn) -> None:
    print("\n==> [Stage 3/4] Loading raw tables via COPY protocol (FK order)")
    with conn.cursor() as cur:
        for table in RAW_TABLES:
            csv_path = RAW_DIR / CSV_NAMES[table]
            print(f"    Loading {table} from {csv_path.name}...")
            with csv_path.open("r", encoding="utf-8") as fh:
                cur.copy_expert(
                    f"COPY {table} FROM STDIN WITH (FORMAT CSV, HEADER true)",
                    fh,
                )
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"    {table}: {count:,} rows loaded")
    print("    Raw tables loaded.")


# ---------------------------------------------------------------------------
# Stage 4 — RFM + K-Means + customer_analysis mart
# ---------------------------------------------------------------------------


_WINDOW_START_STR = "2022-01-01"
_WINDOW_END_EXCL_STR = "2026-02-28"
_NEW_NO_TX_TENURE_DAYS_MAX = 60.0

_MULTICOLLINEARITY_DROP = [
    "monetary_purchase",
    "monetary_cash_withdrawal",
    "monetary_transfer",
    "tenure_utilization",
    "last_6m_active_months",
]
_KMEANS_TAIL_DROP = {"monetary_total", "monetary_cash_withdrawal_share"}
_NOISE_FEATURES = {"age", "acquisition_cost"}

CLUSTER_KM_NAMES = {
    0: "at_risk_churner",
    1: "low_value_dormant",
    2: "high_value_active",
}


def _ts_naive(x) -> pd.Timestamp:
    if pd.isna(x):
        return pd.NaT
    t = pd.to_datetime(x)
    if getattr(t, "tzinfo", None) is not None:
        return t.tz_convert(None)
    return t


def _build_mart(
    df_customers: pd.DataFrame,
    df_features: pd.DataFrame,
    df_transactions: pd.DataFrame,
    df_customer_products: pd.DataFrame,
    df_products: pd.DataFrame,
    cluster_map: pd.DataFrame,
    as_of_date: pd.Timestamp,
) -> pd.DataFrame:
    """Assemble df_customer_analysis mirroring notebook 3 cell 56."""
    feat_cols = [
        c
        for c in df_features.columns
        if c != "customer_id" and c not in {"age", "acquisition_cost"}
    ]
    df = df_customers.merge(
        df_features[feat_cols + ["customer_id"]], on="customer_id", how="left"
    )

    # Global tx rollups
    _tx_times = pd.to_datetime(df_transactions["transaction_datetime"], errors="coerce")
    glob = (
        df_transactions.assign(transaction_datetime=_tx_times)
        .dropna(subset=["transaction_datetime"])
        .groupby("customer_id")["transaction_datetime"]
        .agg(first_tx_global="min", last_tx_global="max", n_tx_completed_global="count")
        .reset_index()
    )
    df = df.merge(glob, on="customer_id", how="left")
    df = df.merge(cluster_map, on="customer_id", how="left")

    # Lifecycle
    ws = _ts_naive(pd.Timestamp(_WINDOW_START_STR))

    def _lifecycle(row: pd.Series) -> str:
        freq = row.get("frequency_total")
        if pd.notna(freq) and float(freq) >= 1.0:
            return "active_clustered"
        last_g = _ts_naive(row.get("last_tx_global"))
        ten = float(row.get("tenure_days") or 0)
        if pd.isna(last_g):
            return (
                "new_no_tx" if ten <= _NEW_NO_TX_TENURE_DAYS_MAX else "inactive_no_tx"
            )
        if last_g < ws:
            return "churned_pre_window"
        return "refunds_only_in_window"

    df["lifecycle_stage"] = df.apply(_lifecycle, axis=1)
    not_clustered = df["lifecycle_stage"] != "active_clustered"
    df.loc[not_clustered, "cluster_km"] = pd.NA
    df.loc[not_clustered, "cluster_name"] = pd.NA

    # Group A: RFM quintile scores
    active = df["lifecycle_stage"] == "active_clustered"
    for col in ("recency_score", "frequency_score", "monetary_score"):
        df[col] = pd.array([pd.NA] * len(df), dtype=pd.Int64Dtype())
    df.loc[active, "recency_score"] = pd.qcut(
        df.loc[active, "recency_days"], q=5, labels=[5, 4, 3, 2, 1]
    ).astype("Int64")
    df.loc[active, "frequency_score"] = pd.qcut(
        df.loc[active, "frequency_total"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype("Int64")
    df.loc[active, "monetary_score"] = pd.qcut(
        df.loc[active, "monetary_total"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype("Int64")
    df["rfm_score"] = (
        df[["recency_score", "frequency_score", "monetary_score"]]
        .apply(pd.to_numeric, errors="coerce")
        .mean(axis=1)
    )

    # Group B: Product intelligence
    cp = df_customer_products[
        df_customer_products.get(
            "is_active", pd.Series([True] * len(df_customer_products))
        )
    ]
    if "is_active" in df_customer_products.columns:
        cp = df_customer_products[df_customer_products["is_active"]]
    cp_prod = cp.merge(
        df_products[["product_id", "product_type"]], on="product_id", how="left"
    )
    owned = cp_prod.groupby("customer_id")["product_type"].apply(set)
    for pt in ["wallet", "credit_card", "investment", "insurance", "loan"]:
        df[f"has_{pt}"] = df["customer_id"].map(
            lambda cid, _pt=pt: _pt in owned.get(cid, set())
        )

    # Primary product type (most transacted in window)
    _df_tx_window = df_transactions.copy()
    _tx_dt = pd.to_datetime(_df_tx_window["transaction_datetime"], errors="coerce")
    if isinstance(_tx_dt.dtype, pd.DatetimeTZDtype):
        _tx_dt = _tx_dt.dt.tz_convert(None)
    _df_tx_window = _df_tx_window[
        (_tx_dt >= pd.Timestamp(_WINDOW_START_STR))
        & (_tx_dt < pd.Timestamp(_WINDOW_END_EXCL_STR))
    ]
    primary = (
        _df_tx_window.groupby(["customer_id", "product_type"])
        .size()
        .reset_index(name="tx_count")
        .sort_values("tx_count", ascending=False)
        .drop_duplicates(subset="customer_id", keep="first")[
            ["customer_id", "product_type"]
        ]
        .rename(columns={"product_type": "primary_product_type"})
    )
    df = df.merge(primary, on="customer_id", how="left")

    # Products active last 6m
    as_of_ts = _ts_naive(as_of_date)
    window_6m = as_of_ts - pd.DateOffset(months=6)
    tx6m = _df_tx_window.copy()
    tx6m_dt = pd.to_datetime(tx6m["transaction_datetime"], errors="coerce")
    if isinstance(tx6m_dt.dtype, pd.DatetimeTZDtype):
        tx6m_dt = tx6m_dt.dt.tz_convert(None)
    else:
        tx6m_dt = tx6m_dt
    tx6m = tx6m[tx6m_dt >= window_6m]
    prod_active_6m = (
        tx6m.groupby("customer_id")["product_type"]
        .nunique()
        .reset_index(name="products_active_last_6m")
    )
    df = df.merge(prod_active_6m, on="customer_id", how="left")
    df["products_active_last_6m"] = (
        df["products_active_last_6m"]
        .where(df["lifecycle_stage"] == "active_clustered", other=pd.NA)
        .astype("Int64")
    )

    # Group C: Human-readable labels
    def _age_group(age):
        if pd.isna(age):
            return pd.NA
        a = int(age)
        if a < 25:
            return "18-24"
        if a < 35:
            return "25-34"
        if a < 45:
            return "35-44"
        if a < 55:
            return "45-54"
        return "55+"

    df["age_group"] = df["age"].apply(_age_group)
    df["tenure_months"] = (df["tenure_days"] / 30.4375).round(1)

    def _engagement(row):
        stage = row.get("lifecycle_stage")
        if stage == "new_no_tx":
            return "new_unactivated"
        if stage == "inactive_no_tx":
            return "never_activated"
        if stage == "churned_pre_window":
            return "churned"
        if stage == "refunds_only_in_window":
            return "refunds_only"
        days = row.get("recency_days")
        if pd.isna(days):
            return pd.NA
        return "recent" if days <= 30 else ("at_risk" if days <= 90 else "dormant")

    df["engagement_status"] = df.apply(_engagement, axis=1)

    def _activity_health(row):
        if row.get("lifecycle_stage") != "active_clustered":
            return pd.NA
        amr = row.get("active_months_ratio") or 0
        l6m = row.get("last_6m_active_months") or 0
        if amr >= 0.7 and l6m >= 4:
            return "strong"
        if amr >= 0.4 or l6m >= 2:
            return "moderate"
        return "weak"

    df["activity_health_label"] = df.apply(_activity_health, axis=1)
    df["annualized_revenue"] = (
        df["monetary_total"] / (df["tenure_days"] / 365.25)
    ).round(2)
    df["cac_payback_months"] = (
        (df["acquisition_cost"] / (df["annualized_revenue"] / 12))
        .replace([float("inf"), -float("inf")], pd.NA)
        .round(1)
    )

    # Group D: Never-transacted signal
    never_tx = df["n_tx_completed_global"].isna() | (df["n_tx_completed_global"] == 0)
    df["days_registered_without_tx"] = df["tenure_days"].where(never_tx, other=pd.NA)

    # Group E: Lineage
    df["rfm_window_start"] = pd.Timestamp(_WINDOW_START_STR)
    df["rfm_window_end_excl"] = pd.Timestamp(_WINDOW_END_EXCL_STR)
    df["analysis_as_of_date"] = pd.Timestamp(as_of_date)
    df["mart_built_at"] = pd.Timestamp.utcnow()

    # Tidy: strip timezone from timestamp columns
    for col in (
        "registration_date",
        "first_tx_global",
        "last_tx_global",
        "analysis_as_of_date",
        "mart_built_at",
    ):
        if col not in df.columns:
            continue
        s = pd.to_datetime(df[col], errors="coerce")
        if isinstance(s.dtype, pd.DatetimeTZDtype):
            s = s.dt.tz_convert(None)
        df[col] = s

    # Normalise nullable integer columns
    for col in ("cluster_km",):
        if col in df.columns:
            df[col] = pd.array(df[col], dtype=pd.Int64Dtype())

    return df


def run_mart(db_url: str) -> None:
    print("\n==> [Stage 4/4] Computing RFM scores, K-Means clustering, writing mart")
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sqlalchemy import create_engine, text

    from fintech_ai_segmentation.rfm_features import (
        build_customer_feature_matrix,
        build_preprocessing_pipeline,
    )

    engine = create_engine(db_url, pool_pre_ping=True)

    print("    Loading tables from database...")
    with engine.connect() as conn:
        df_customers = pd.read_sql(
            text(
                "SELECT customer_id, age, state, acquisition_channel, acquisition_cost, registration_date, true_segment FROM customers_raw"
            ),
            conn,
        )
        df_transactions = pd.read_sql(
            text(
                "SELECT transaction_id, customer_id, transaction_datetime, amount, transaction_type, product_type, channel, status FROM transactions_raw WHERE status = 'completed'"
            ),
            conn,
        )
        df_products = pd.read_sql(
            text("SELECT product_id, product_name, product_type FROM products_raw"),
            conn,
        )
        df_customer_products = pd.read_sql(
            text(
                "SELECT customer_id, product_id, start_date, is_active FROM customer_products_raw"
            ),
            conn,
        )

    # Window filter
    tx_dt = pd.to_datetime(df_transactions["transaction_datetime"], errors="coerce")
    if isinstance(tx_dt.dtype, pd.DatetimeTZDtype):
        tx_dt = tx_dt.dt.tz_convert(None)
    df_tx = df_transactions[
        (
            (tx_dt >= pd.Timestamp(_WINDOW_START_STR))
            & (tx_dt < pd.Timestamp(_WINDOW_END_EXCL_STR))
        )
    ].copy()
    as_of_date = tx_dt[
        (tx_dt >= pd.Timestamp(_WINDOW_START_STR))
        & (tx_dt < pd.Timestamp(_WINDOW_END_EXCL_STR))
    ].max()
    print(f"    as_of_date: {as_of_date}")

    print("    Building feature matrix...")
    df_features = build_customer_feature_matrix(
        df_tx,
        df_customer_products,
        df_customers,
        as_of_date,
        window_start=pd.Timestamp(_WINDOW_START_STR),
        df_tx_full=df_transactions,
    )
    if "days_to_first_tx" in df_features.columns:
        df_features.loc[df_features["days_to_first_tx"] < 0, "days_to_first_tx"] = 0.0

    # Clustering frame: active customers only
    df_clustering = df_features[df_features["frequency_total"] >= 1].copy()
    present_drop = [c for c in _MULTICOLLINEARITY_DROP if c in df_clustering.columns]
    df_clustering = df_clustering.drop(columns=present_drop)

    feature_cols = [c for c in df_clustering.columns if c != "customer_id"]
    feature_cols = [c for c in feature_cols if c not in _KMEANS_TAIL_DROP]
    core_feature_cols = [c for c in feature_cols if c not in _NOISE_FEATURES]

    print(f"    Clustering on {len(core_feature_cols)} core features (PCA-reduced)...")
    X_pre = (
        df_clustering[core_feature_cols]
        .copy()
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
    )
    preproc = build_preprocessing_pipeline(core_feature_cols)
    X_core = preproc.fit_transform(X_pre)
    X_pca = PCA(random_state=42).fit(X_core)
    cumvar = X_pca.explained_variance_ratio_.cumsum()
    n_comp = int((cumvar >= 0.80).argmax()) + 1
    X_for_km = PCA(n_components=n_comp, random_state=42).fit_transform(X_core)

    print(f"    Fitting KMeans (k=3, {n_comp} PCA components)...")
    km = KMeans(n_clusters=3, random_state=42, n_init=20)
    labels = km.fit_predict(X_for_km)

    cluster_map = df_clustering[["customer_id"]].copy()
    cluster_map["cluster_km"] = labels
    cluster_map["cluster_name"] = cluster_map["cluster_km"].map(CLUSTER_KM_NAMES)

    print("    Building customer_analysis mart...")
    df_mart = _build_mart(
        df_customers,
        df_features,
        df_transactions,
        df_customer_products,
        df_products,
        cluster_map,
        as_of_date,
    )

    print(f"    Writing {len(df_mart):,} rows to customer_analysis...")
    with engine.begin() as conn:
        try:
            conn.execute(text("TRUNCATE TABLE public.customer_analysis"))
        except Exception:
            conn.execute(text("DELETE FROM public.customer_analysis"))

    df_mart.to_sql(
        "customer_analysis",
        engine,
        schema="public",
        if_exists="append",
        index=False,
        chunksize=500,
        method="multi",
    )
    print(f"    Done. {len(df_mart):,} rows written.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    db_url = _get_db_url()
    conn = _connect(db_url)

    try:
        run_schema(conn)
        run_generation()
        run_load(conn)
    finally:
        conn.close()

    run_mart(db_url)
    print("\nData loader complete. Run `docker compose up` to start the app.")


if __name__ == "__main__":
    main()
