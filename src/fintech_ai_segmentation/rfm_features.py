"""Customer-level RFM and preprocessing helpers for k-means clustering.

This module is the feature engineering layer for the SynaptiqPay segmentation
pipeline. It produces a fully numeric customer-level matrix from four raw tables
(transactions, customers, products, customer_products) and wraps the
preprocessing steps (log-transform + scaling) into a reproducible sklearn
Pipeline that can be serialised and applied consistently across runs.

Design decisions captured here:
- No categorical encodings. Nominal variables like ``acquisition_channel`` and
  ``state`` are intentionally replaced by numeric proxies (``acquisition_cost``
  for channel quality; state is dropped as a weak signal). K-means uses
  Euclidean distance, so all-numeric features avoid the asymmetric-distance
  problem introduced by one-hot reference-level dropping.
- ``true_segment`` is never used as a feature. It is the ground-truth label that
  the clustering model is meant to recover; including it would be data leakage.
- Refunds are excluded from Frequency and Monetary aggregations (they represent
  reversals, not genuine engagement), but are captured separately as
  ``refund_rate`` to surface customers with a high reversal pattern.
- Monetary type splits (purchase, transfer, cash_withdrawal) are kept by default
  because they carry behavioural mix signal, but removed by ``drop_correlated_splits``
  if they correlate too strongly with ``monetary_total`` (redundant information
  that would double-count the same dimension in Euclidean space).

All public functions in this module return plain pandas DataFrames or sklearn
objects, keeping orchestration (windowing, eligibility filtering) in the
notebook rather than baked in here.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

# Columns that receive a log1p transform before scaling.
# These are right-skewed counts and sums typical of transaction data. log1p
# softens extreme spender / high-frequency outliers without removing them,
# keeping the "whale" customer distinguishable from the median while preventing
# a single extreme value from collapsing the majority of points into a thin
# band after StandardScaler.
# acquisition_cost is included here because its distribution is multi-modal
# (each channel has a distinct cost cluster) and has a mild right tail; log1p
# flattens the inter-cluster gaps enough for StandardScaler to spread them
# more evenly without distorting the channel-quality ordering.
LOG1P_COLS = [
    "recency_days",
    "frequency_total",
    "avg_ticket",
    "avg_days_between_tx",
    "acquisition_cost",
]

# refund_rate receives a square-root transform (sqrt) rather than log1p.
# It is bounded in [0, 1] and heavily concentrated near 0, so sqrt softens
# the spike at zero and stretches the long right tail while keeping all values
# in [0, 1] — no risk of mapping to negative space as log1p could for values
# between 0 and 1 if not shifted.
SQRT_COLS = ["refund_rate"]

# Columns that pass through to StandardScaler without any non-linear transform.
# age: near-uniform distribution, no meaningful skew to correct.
# tenure_days: registration dates follow a gamma-shaped curve producing a
#   spread that is closer to uniform than the extreme right-skew of monetary
#   or frequency features; passthrough keeps the natural spacing.
# products_owned: discrete low-cardinality integer (1–5); log/sqrt would
#   compress the already tight spacing between categories.
# Monetary splits: handled conditionally by ``drop_correlated_splits`` before
#   the pipeline is built; if they survive they go straight to scaling.
PASSTHROUGH_COLS = [
    "products_owned",
    "age",
    "tenure_days",
    "monetary_purchase",
    "monetary_transfer",
    "monetary_cash_withdrawal",
]


def _as_timestamp(x: pd.Timestamp | str) -> pd.Timestamp:
    """Normalise input to a timezone-naive pandas Timestamp.

    Supabase returns timezone-aware datetimes; stripping tz-info lets us
    compare safely with ``as_of_date`` regardless of whether the caller passes
    a naive or aware timestamp.
    """
    ts = pd.Timestamp(x)
    if ts.tzinfo is not None:
        ts = ts.tz_localize(None)
    return ts


def _non_refund_mask(df: pd.DataFrame) -> pd.Series:
    """Boolean mask selecting non-refund rows.

    Refund transactions represent money flowing back to the customer and should
    not count toward Frequency (engagement) or Monetary (value) in the RFM
    framework. They are tracked separately via ``refund_rate``.
    """
    return df["transaction_type"].ne("refund")


def _mean_days_between_transactions(nr: pd.DataFrame) -> pd.Series:
    """Compute mean inter-transaction gap in days per customer (cadence feature).

    Cadence measures how regularly a customer transacts, which is complementary
    to raw frequency: two customers with the same transaction count can have very
    different behaviour if one transacts every week and the other in a single
    burst. This distinction helps the clustering model separate consistently
    engaged customers from intermittent ones.

    Only non-refund transactions are used (same population as Frequency / Monetary)
    so the gap signal is not diluted by reversal events.

    Returns NaN for customers with fewer than two qualifying transactions; the
    caller is responsible for imputing those values.
    """
    if nr.empty:
        return pd.Series(dtype="float64", name="avg_days_between_tx")

    out: dict[object, float] = {}
    for cid, g in nr.groupby("customer_id", sort=False):
        if len(g) < 2:
            out[cid] = np.nan
            continue
        t = g["transaction_datetime"].sort_values()
        delta_days = t.diff().dt.total_seconds() / 86400.0
        out[cid] = float(delta_days.iloc[1:].mean())

    return pd.Series(out, name="avg_days_between_tx")


def build_behavioral_features(
    df_tx: pd.DataFrame,
    df_customer_products: pd.DataFrame,
    as_of_date: pd.Timestamp | str,
) -> pd.DataFrame:
    """Aggregate transaction-level data into one behavioural row per customer.

    This is the core RFM aggregation step. The caller is expected to pass
    ``df_tx`` already restricted to the analysis window (completed transactions
    only) so this function focuses purely on the per-customer roll-up.

    Columns produced
    ----------------
    recency_days : float
        Days elapsed between ``as_of_date`` and the customer's last non-refund
        transaction. Lower values mean a more recently active customer.
    frequency_total : int
        Count of non-refund completed transactions in the window. Refunds are
        excluded because they represent reversals, not genuine engagement.
    monetary_total : float
        Sum of ``amount`` across non-refund transactions. Kept for diagnostics
        and decomposition checks (e.g. residual fee sanity checks).
    avg_ticket : float
        Mean amount per non-refund transaction (``monetary_total`` /
        ``frequency_total``). This is the primary monetary-intensity feature
        used for clustering to avoid double-weighting the same spend signal
        when ``frequency_total`` is also included.
    monetary_purchase / monetary_transfer / monetary_cash_withdrawal : float
        Transaction-type sub-totals. These capture the behavioural mix
        (spending vs moving money vs cash) which is useful for cluster
        interpretability. They may be dropped later if they correlate too
        strongly with ``monetary_total`` (see ``drop_correlated_splits``).
    refund_rate : float in [0, 1]
        Refund count divided by total completed transaction count (including
        refunds). A high rate can flag low product-market fit, fraud exposure,
        or a particular product line dominated by reversals.
    avg_days_between_tx : float
        Mean inter-transaction gap in days; measures cadence / regularity.
        Imputed with the observed analysis-window span (earliest to ``as_of_date``)
        for customers with fewer than two non-refund transactions. This avoids
        NaN propagation in the sklearn Pipeline while still placing infrequent
        customers at the "low cadence" end of the feature space.
    products_owned : int
        Count of active products held by the customer at ``as_of_date``
        (point-in-time join to ``customer_products_raw``). Captures
        cross-sell depth as a proxy for relationship breadth.
    """
    as_of = _as_timestamp(as_of_date)
    df = df_tx.copy()
    df["transaction_datetime"] = pd.to_datetime(df["transaction_datetime"])
    if getattr(df["transaction_datetime"].dt, "tz", None) is not None:
        df["transaction_datetime"] = df["transaction_datetime"].dt.tz_localize(None)

    completed = df
    nr = completed.loc[_non_refund_mask(completed)]

    last_ts = nr.groupby("customer_id", sort=False)["transaction_datetime"].max()
    recency_days = (as_of - last_ts).dt.days.astype("float64")

    freq = nr.groupby("customer_id", sort=False).size().rename("frequency_total")

    def _sum_type(tt: str) -> pd.Series:
        return (
            nr.loc[nr["transaction_type"].eq(tt)]
            .groupby("customer_id", sort=False)["amount"]
            .sum()
        )

    monetary_total = nr.groupby("customer_id", sort=False)["amount"].sum().rename(
        "monetary_total"
    )
    monetary_purchase = _sum_type("purchase").rename("monetary_purchase")
    monetary_transfer = _sum_type("transfer").rename("monetary_transfer")
    monetary_cw = _sum_type("cash_withdrawal").rename("monetary_cash_withdrawal")

    refund_count = (
        completed.loc[completed["transaction_type"].eq("refund")]
        .groupby("customer_id", sort=False)
        .size()
        .rename("refund_count")
    )
    total_tx = completed.groupby("customer_id", sort=False).size().rename("total_tx_count")

    out = pd.concat(
        [
            recency_days.rename("recency_days"),
            freq,
            monetary_total,
            monetary_purchase,
            monetary_transfer,
            monetary_cw,
            refund_count,
            total_tx,
        ],
        axis=1,
    )
    out["refund_rate"] = out["refund_count"].fillna(0) / out["total_tx_count"].replace(0, np.nan)
    out["refund_rate"] = out["refund_rate"].fillna(0.0)
    out = out.drop(columns=["refund_count", "total_tx_count"])
    out["avg_ticket"] = out["monetary_total"] / out["frequency_total"].replace(0, np.nan)
    out["avg_ticket"] = out["avg_ticket"].fillna(0.0)

    # Zero-fill split columns for customers who never used that transaction type.
    for col in (
        "monetary_purchase",
        "monetary_transfer",
        "monetary_cash_withdrawal",
    ):
        out[col] = out[col].fillna(0.0)

    cadence = _mean_days_between_transactions(nr)
    out = out.join(cadence, how="left")

    # Impute NaN cadence with the window span so single-transaction customers
    # land at the "slow" end of the cadence axis rather than being dropped.
    window_span_days = (
        float((as_of - completed["transaction_datetime"].min()).days)
        if len(completed) > 0
        else 730.0
    )
    out["avg_days_between_tx"] = out["avg_days_between_tx"].fillna(window_span_days)

    cp = df_customer_products.copy()
    cp["start_date"] = pd.to_datetime(cp["start_date"])
    if getattr(cp["start_date"].dt, "tz", None) is not None:
        cp["start_date"] = cp["start_date"].dt.tz_localize(None)
    active = cp["is_active"].astype(bool) & (cp["start_date"] <= as_of)
    products_owned = (
        cp.loc[active].groupby("customer_id", sort=False).size().rename("products_owned")
    )
    out = out.join(products_owned, how="left")
    out["products_owned"] = out["products_owned"].fillna(0).astype("int64")

    return out.reset_index()


def build_customer_feature_matrix(
    df_tx: pd.DataFrame,
    df_customer_products: pd.DataFrame,
    df_customers: pd.DataFrame,
    as_of_date: pd.Timestamp | str,
) -> pd.DataFrame:
    """Combine behavioural features with numeric customer attributes.

    Joins the output of ``build_behavioral_features`` (transaction-derived
    metrics) with numeric attributes from ``customers_raw``:

    age : float
        Raw customer age in years. Kept as a continuous variable rather than
        binned; binning can be revisited if the distribution is strongly
        multi-modal, but binning introduces ordering ambiguity and dummy
        complexity that we want to avoid for k-means.
    acquisition_cost : float
        Cost-per-acquisition (CAC) in BRL. Used as a numeric proxy for
        acquisition channel quality instead of one-hot encoding
        ``acquisition_channel``. This preserves the channel signal in a single
        continuous dimension, avoids the symmetric-distance argument against
        drop-first dummies, and captures meaningful ordering (e.g. paid_ads
        tends to have higher CAC than organic referrals).
    tenure_days : float
        Days elapsed between ``registration_date`` and ``as_of_date``.
        Complementary to ``recency_days``: two customers can have the same
        recency but very different tenure (a new user who just transacted vs a
        mature user who also just transacted). Cohort analysis (notebook 2)
        showed that tenure-based cohorts have meaningfully different retention
        patterns, making this a strong clustering signal.

    ``state``, ``acquisition_channel``, and ``true_segment`` are intentionally
    excluded: state is a weak geographic signal at this stage, channel is
    replaced by cost, and true_segment is the label we are trying to discover.

    Returns one row per ``customer_id`` with all-numeric columns ready for
    ``drop_correlated_splits`` and ``build_preprocessing_pipeline``.
    """
    as_of = _as_timestamp(as_of_date)
    beh = build_behavioral_features(df_tx, df_customer_products, as_of_date)
    customer_num = df_customers[
        ["customer_id", "age", "acquisition_cost", "registration_date"]
    ].drop_duplicates(subset=["customer_id"]).copy()

    customer_num["registration_date"] = pd.to_datetime(customer_num["registration_date"])
    if getattr(customer_num["registration_date"].dt, "tz", None) is not None:
        customer_num["registration_date"] = customer_num["registration_date"].dt.tz_localize(None)
    customer_num["tenure_days"] = (as_of - customer_num["registration_date"]).dt.days.astype(
        "float64"
    )
    customer_num = customer_num.drop(columns=["registration_date"])

    return customer_num.merge(beh, on="customer_id", how="left")


def drop_correlated_splits(
    df: pd.DataFrame,
    *,
    threshold: float = 0.9,
) -> tuple[pd.DataFrame, list[str]]:
    """Remove monetary split columns that are near-linearly redundant with ``monetary_total``.

    K-means computes Euclidean distances. If ``monetary_purchase`` is almost
    perfectly correlated with ``monetary_total`` (which it often is when
    purchases dominate spend), keeping both effectively double-weights the
    monetary dimension in every inter-customer distance calculation. This
    inflates the contribution of that axis beyond what the other features
    contribute and can pull centroids toward high-spend customers independent
    of their recency or cadence behaviour.

    The default threshold of 0.9 is deliberately conservative: split columns
    with genuine mix signal (e.g. a meaningful transfer vs purchase trade-off)
    will survive and add interpretability to cluster profiles, while purely
    redundant splits are removed. Caller can adjust ``threshold`` if the
    correlation structure of a specific data window differs.

    This step is intentionally performed *outside* the sklearn Pipeline because
    the decision to drop a column is data-dependent and should be inspected and
    logged (see the notebook correlation heatmap) before fitting. Fitted
    transformers inside a Pipeline must be deterministic given the same input
    schema, whereas this function changes the schema itself.

    Returns
    -------
    (cleaned_df, dropped_column_names)
    """
    split_cols = [
        "monetary_purchase",
        "monetary_transfer",
        "monetary_cash_withdrawal",
    ]
    dropped: list[str] = []
    keep_df = df.copy()
    if "monetary_total" not in keep_df.columns:
        return keep_df, dropped

    corr_candidates = ["monetary_total"] + [c for c in split_cols if c in keep_df.columns]
    if len(corr_candidates) > 1:
        corr_matrix = keep_df[corr_candidates].corr()
        print("Correlation matrix (monetary_total and split columns):")
        print(corr_matrix)

    for col in split_cols:
        if col not in keep_df.columns:
            continue
        corr = keep_df[["monetary_total", col]].corr().iloc[0, 1]
        if np.isfinite(corr) and abs(float(corr)) > threshold:
            dropped.append(col)

    if dropped:
        keep_df = keep_df.drop(columns=dropped)
    return keep_df, dropped


def build_preprocessing_pipeline(feature_columns: Sequence[str]) -> Pipeline:
    """Build the sklearn preprocessing Pipeline ready for k-means input.

    The pipeline applies two sequential transforms:

    Step 1 — per-column non-linear transforms via ``ColumnTransformer``

        log1p on ``LOG1P_COLS`` (recency, frequency, average ticket, cadence,
        acquisition_cost):
            These are right-skewed counts and sums. log1p softens the long
            right tail so that extreme values do not dominate the Euclidean
            distance after scaling, while keeping all values non-negative and
            preserving the relative ordering between customers.

        sqrt on ``SQRT_COLS`` (refund_rate):
            refund_rate is bounded in [0, 1] with a heavy spike at zero.
            Square root is a gentler transform than log1p and is the canonical
            choice for bounded rates: it stretches the low end (most customers)
            without compressing the high end (fraud / reversal-heavy customers)
            as aggressively as log1p would.

        passthrough for remaining columns (age, products_owned, monetary
        splits if they survived ``drop_correlated_splits``):
            These have near-uniform or discrete distributions where a
            non-linear transform would distort spacing rather than improve it.

    Step 2 — StandardScaler on all columns
        After the non-linear transforms, all features are put on a common
        variance scale (mean ≈ 0, std ≈ 1). This is critical for k-means:
        the algorithm minimises within-cluster sum of squared Euclidean
        distances, so unscaled features with large numeric ranges (e.g.
        ``avg_ticket`` in BRL) would dominate relative to unit-scale
        features (e.g. ``refund_rate``).
        StandardScaler is preferred over MinMaxScaler because MinMax depends
        on observed min/max values, making it sensitive to outliers and less
        stable across different analysis windows.

    The pipeline is built dynamically from ``feature_columns``. The output
    contains the same surviving feature set after ``drop_correlated_splits``,
    but ordered by transformer groups (log1p, sqrt, passthrough). Use
    ``preproc.named_steps["pre"].get_feature_names_out()`` when labeling the
    transformed matrix.
    """
    log_cols = [c for c in LOG1P_COLS if c in feature_columns]
    sqrt_cols = [c for c in SQRT_COLS if c in feature_columns and c not in log_cols]
    pass_cols = [c for c in feature_columns if c not in log_cols and c not in sqrt_cols]

    pre = ColumnTransformer(
        transformers=[
            ("log1p", FunctionTransformer(np.log1p, validate=False), log_cols),
            ("sqrt", FunctionTransformer(np.sqrt, validate=False), sqrt_cols),
            ("pass", "passthrough", pass_cols),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )

    return Pipeline(
        steps=[
            ("pre", pre),
            ("scale", StandardScaler()),
        ]
    )


__all__ = [
    "LOG1P_COLS",
    "SQRT_COLS",
    "PASSTHROUGH_COLS",
    "build_behavioral_features",
    "build_customer_feature_matrix",
    "drop_correlated_splits",
    "build_preprocessing_pipeline",
]
