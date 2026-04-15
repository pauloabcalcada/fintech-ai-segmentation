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
- ``monetary_*_share`` columns (composition of spend by transaction type) are
  always added in ``build_customer_feature_matrix`` via ``add_monetary_type_shares``
  and typically retained for clustering even when raw splits are dropped.

All public functions in this module return plain pandas DataFrames or sklearn
objects, keeping orchestration (windowing, eligibility filtering) in the
notebook rather than baked in here.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta

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
# activity_trend_ratio is included because values can range well above 1.0 for
# growing customers (many recent transactions, few early ones), producing a
# right-skewed distribution that benefits from compression.
LOG1P_COLS = [
    "recency_days",
    "frequency_total",
    "avg_ticket",
    "avg_days_between_tx",
    "acquisition_cost",
    "activity_trend_ratio",
    # Derived-intensity feature: avg transactions per month when active.
    # Right-skewed (high-value: ~40/month; churner: ~2/month); log1p compresses tail.
    "tx_per_active_month",
    # Global activation speed: days from registration to first ever transaction.
    # Right-skewed (quick activators: 0–30 days; slow/never: 200–400+ days).
    "days_to_first_tx",
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
# Monetary type shares: compositional mix (purchase / transfer / cash_withdrawal
#   as fractions of monetary_total). Kept even when raw splits are dropped for
#   collinearity; bounded in [0, 1], passthrough-scaled like refund_rate.
PASSTHROUGH_COLS = [
    "products_owned",
    "age",
    "tenure_days",
    "monetary_purchase",
    "monetary_transfer",
    "monetary_cash_withdrawal",
    "monetary_purchase_share",
    "monetary_transfer_share",
    "monetary_cash_withdrawal_share",
    "active_months_ratio",
    "tenure_utilization",
    # Recency-related features added alongside trajectory features:
    # last_6m_active_months: count of months with ≥1 tx in final 6 months of window.
    #   Churners score 0 (already gone); dormant score 1–2; mid ~5; high ~6.
    #   Integer-valued discrete [0, 6]; passthrough keeps integer spacing.
    "last_6m_active_months",
    # early_window_freq_ratio: fraction of total window tx that fell in the FIRST half.
    #   Churners concentrate activity early (ratio → 1.0); stable customers score ~0.5.
    #   Bounded [0, 1]; passthrough.
    "early_window_freq_ratio",
]

# Output column names for ``add_monetary_type_shares`` (clustering mix signal).
MONETARY_SHARE_COLS = [
    "monetary_purchase_share",
    "monetary_transfer_share",
    "monetary_cash_withdrawal_share",
]


def _as_timestamp(x: pd.Timestamp | str) -> pd.Timestamp:
    """Normalise input to a timezone-naive pandas Timestamp.

    Supabase returns timezone-aware datetimes; stripping tz-info lets us
    compare safely with ``as_of_date`` regardless of whether the caller passes
    a naive or aware timestamp.
    """
    ts = pd.Timestamp(x)
    if ts.tzinfo is not None:
        ts = ts.tz_convert(None)  # tz_localize(None) raises TypeError on aware Timestamps
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

    monetary_total = (
        nr.groupby("customer_id", sort=False)["amount"].sum().rename("monetary_total")
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
    total_tx = (
        completed.groupby("customer_id", sort=False).size().rename("total_tx_count")
    )

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
    out["refund_rate"] = out["refund_count"].fillna(0) / out["total_tx_count"].replace(
        0, np.nan
    )
    out["refund_rate"] = out["refund_rate"].fillna(0.0)
    out = out.drop(columns=["refund_count", "total_tx_count"])
    out["avg_ticket"] = out["monetary_total"] / out["frequency_total"].replace(
        0, np.nan
    )
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
        cp.loc[active]
        .groupby("customer_id", sort=False)
        .size()
        .rename("products_owned")
    )
    out = out.join(products_owned, how="left")
    out["products_owned"] = out["products_owned"].fillna(0).astype("int64")

    return out.reset_index()


def build_trajectory_features(
    df_tx: pd.DataFrame,
    as_of_date: pd.Timestamp | str,
    window_start: pd.Timestamp | str,
) -> pd.DataFrame:
    """Compute activity trajectory features that capture how engagement changed over time.

    Point-in-time RFM features (recency, frequency, avg_ticket) cannot distinguish
    customers who were always low-activity (dormant pattern) from those who were
    briefly active and then completely stopped (churner pattern). These trajectory
    features expose the temporal *shape* of engagement by splitting the analysis
    window and measuring continuity.

    Columns produced
    ----------------
    activity_trend_ratio : float
        (recent_half_count + 1) / (early_half_count + 1).  Laplace smoothing
        avoids division-by-zero for customers with no transactions in one half.
        Values < 1 indicate declining activity (churner pattern); values ≈ 1
        indicate stable engagement; values > 1 indicate growing engagement.
        Receives log1p transform (right-skewed; growing customers can produce
        ratios well above 1).
    active_months_ratio : float in [0, 1]
        Distinct calendar months with ≥1 non-refund transaction divided by the
        number of months from the customer's first transaction to ``as_of_date``
        (minimum denominator = 1).  Measures continuity of engagement: a
        customer active every month scores 1.0; one who transacted once and
        never again scores close to 0.  Bounded in [0, 1], passthrough.
    tenure_utilization : float in [0, 1]
        Distinct active months divided by months since ``registration_date``
        (derived from ``df_tx`` column if present, otherwise falls back to
        months since first transaction).  Captures customers who registered long
        ago but were never truly engaged vs those who hit the ground running.
        Bounded in [0, 1], passthrough.

    Parameters
    ----------
    df_tx :
        Transaction DataFrame for the analysis window (completed transactions
        only).  Must have columns: ``customer_id``, ``transaction_datetime``,
        ``transaction_type``.  If a ``registration_date`` column is present it
        will be used for ``tenure_utilization``; otherwise the first transaction
        date is used as the registration proxy.
    as_of_date :
        End of the analysis window (inclusive).
    window_start :
        Start of the analysis window.  The midpoint for ``activity_trend_ratio``
        is computed as ``window_start + (as_of_date - window_start) / 2``.
    """
    as_of = _as_timestamp(as_of_date)
    w_start = _as_timestamp(window_start)
    midpoint = w_start + (as_of - w_start) / 2

    df = df_tx.copy()
    df["transaction_datetime"] = pd.to_datetime(df["transaction_datetime"])
    if getattr(df["transaction_datetime"].dt, "tz", None) is not None:
        df["transaction_datetime"] = df["transaction_datetime"].dt.tz_localize(None)

    nr = df.loc[_non_refund_mask(df)]

    # --- activity_trend_ratio ---
    early = nr.loc[nr["transaction_datetime"] < midpoint]
    recent = nr.loc[nr["transaction_datetime"] >= midpoint]

    early_counts = early.groupby("customer_id", sort=False).size().rename("early_count")
    recent_counts = (
        recent.groupby("customer_id", sort=False).size().rename("recent_count")
    )
    all_customers = nr["customer_id"].unique()
    trend_df = pd.DataFrame(index=all_customers)
    trend_df.index.name = "customer_id"
    trend_df = trend_df.join(early_counts).join(recent_counts)
    trend_df["early_count"] = trend_df["early_count"].fillna(0)
    trend_df["recent_count"] = trend_df["recent_count"].fillna(0)
    trend_df["activity_trend_ratio"] = (trend_df["recent_count"] + 1) / (
        trend_df["early_count"] + 1
    )

    # --- active_months_ratio and tenure_utilization ---
    nr_with_month = nr.copy()
    nr_with_month["year_month"] = nr_with_month["transaction_datetime"].dt.to_period(
        "M"
    )

    active_months = (
        nr_with_month.groupby("customer_id", sort=False)["year_month"]
        .nunique()
        .rename("active_months")
    )

    first_tx = (
        nr.groupby("customer_id", sort=False)["transaction_datetime"]
        .min()
        .rename("first_tx_date")
    )

    traj = trend_df[["activity_trend_ratio"]].join(active_months).join(first_tx)
    traj["active_months"] = traj["active_months"].fillna(0)

    # months from first transaction to as_of_date (denominator for active_months_ratio)
    traj["months_since_first_tx"] = (
        (as_of - traj["first_tx_date"]).dt.days / 30.44
    ).clip(lower=1.0)
    traj["active_months_ratio"] = (
        traj["active_months"] / traj["months_since_first_tx"]
    ).clip(0.0, 1.0)

    # tenure_utilization: use registration_date from df_tx if available,
    # otherwise fall back to first_tx_date
    if "registration_date" in df.columns:
        reg_dates = df.drop_duplicates(subset=["customer_id"])[
            ["customer_id", "registration_date"]
        ].set_index("customer_id")["registration_date"]
        reg_dates = pd.to_datetime(reg_dates)
        if getattr(reg_dates.dt, "tz", None) is not None:
            reg_dates = reg_dates.dt.tz_localize(None)
        traj = traj.join(reg_dates.rename("registration_date"), how="left")
        traj["registration_date"] = traj["registration_date"].fillna(
            traj["first_tx_date"]
        )
    else:
        traj["registration_date"] = traj["first_tx_date"]

    traj["months_since_registration"] = (
        (as_of - traj["registration_date"]).dt.days / 30.44
    ).clip(lower=1.0)
    traj["tenure_utilization"] = (
        traj["active_months"] / traj["months_since_registration"]
    ).clip(0.0, 1.0)

    # --- last_6m_active_months ---
    # Count of distinct calendar months with ≥1 non-refund tx in the 6-month
    # period ending at as_of_date. This is the sharpest single-feature test for
    # whether a customer is in the final stages of churn: churners score 0 or 1
    # while high/mid-value customers score 5–6.
    window_6m_start = as_of - timedelta(days=182)
    nr_6m = nr.loc[nr["transaction_datetime"] >= window_6m_start].copy()
    nr_6m["year_month_6m"] = nr_6m["transaction_datetime"].dt.to_period("M")
    last_6m_active = (
        nr_6m.groupby("customer_id", sort=False)["year_month_6m"]
        .nunique()
        .rename("last_6m_active_months")
    )
    traj = traj.join(last_6m_active, how="left")
    traj["last_6m_active_months"] = (
        traj["last_6m_active_months"].fillna(0).astype("float64")
    )

    # --- early_window_freq_ratio ---
    # Share of total window transactions that occurred in the FIRST half of the
    # window. Churners front-load their activity (ratio → 1.0); customers with
    # stable engagement score ~0.5; growing customers score < 0.5.
    # Uses early_count / (early_count + recent_count); add 1e-9 to avoid 0/0.
    total_count = trend_df["early_count"] + trend_df["recent_count"]
    traj["early_window_freq_ratio"] = (
        (trend_df["early_count"] / (total_count + 1e-9))
        .clip(0.0, 1.0)
        .reindex(traj.index)
    )
    traj["early_window_freq_ratio"] = traj["early_window_freq_ratio"].fillna(0.5)

    out = traj[
        [
            "activity_trend_ratio",
            "active_months_ratio",
            "tenure_utilization",
            "last_6m_active_months",
            "early_window_freq_ratio",
        ]
    ].copy()
    out.index.name = "customer_id"
    return out.reset_index()


def build_customer_feature_matrix(
    df_tx: pd.DataFrame,
    df_customer_products: pd.DataFrame,
    df_customers: pd.DataFrame,
    as_of_date: pd.Timestamp | str,
    *,
    window_start: pd.Timestamp | str | None = None,
    df_tx_full: pd.DataFrame | None = None,
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

    After the merge, ``add_monetary_type_shares`` appends
    ``monetary_purchase_share``, ``monetary_transfer_share``, and
    ``monetary_cash_withdrawal_share`` (composition of spend by transaction type).

    Trajectory features from ``build_trajectory_features`` are also merged in
    (``activity_trend_ratio``, ``active_months_ratio``, ``tenure_utilization``,
    ``last_6m_active_months``, ``early_window_freq_ratio``) to capture how
    engagement evolved over the analysis window.

    Two derived intensity features are computed post-merge:

    tx_per_active_month : float
        ``frequency_total`` divided by the estimated number of active months
        (``active_months_ratio × tenure_days / 30.44``).  This directly
        encodes the per-segment *transaction intensity when active*: high-value
        ~40/month, mid-value ~18/month, dormant ~4/month, churner ~2/month.
        Receives log1p transform.
    days_to_first_tx : float (optional — added when ``df_tx_full`` is provided)
        Days from ``registration_date`` to a customer's first ever transaction
        in the *full* (non-windowed) transaction history.  Quick activators
        score 0–30 days (high-value pattern); slow / never-activated customers
        score 200+ days (at-risk pattern).  Receives log1p transform.
        Pass the unwindowed transaction DataFrame as ``df_tx_full`` to enable.

    Parameters
    ----------
    window_start :
        Start of the analysis window used for trajectory feature computation.
        Defaults to ``as_of_date - 730 days`` (approximately 24 months).
    df_tx_full :
        Optional full (non-windowed) transaction DataFrame used to compute
        ``days_to_first_tx``.  Must have ``customer_id`` and
        ``transaction_datetime`` columns.  If ``None``, the feature is not
        added.

    Parameters
    ----------
    window_start :
        Start of the analysis window used for trajectory feature computation.
        Defaults to ``as_of_date - 730 days`` (approximately 24 months).

    Returns one row per ``customer_id`` with all-numeric columns ready for
    ``drop_correlated_splits`` and ``build_preprocessing_pipeline``.
    """
    as_of = _as_timestamp(as_of_date)
    if window_start is None:
        w_start: pd.Timestamp = as_of - timedelta(days=730)
    else:
        w_start = _as_timestamp(window_start)

    beh = build_behavioral_features(df_tx, df_customer_products, as_of_date)
    customer_num = (
        df_customers[["customer_id", "age", "acquisition_cost", "registration_date"]]
        .drop_duplicates(subset=["customer_id"])
        .copy()
    )

    customer_num["registration_date"] = pd.to_datetime(
        customer_num["registration_date"]
    )
    if getattr(customer_num["registration_date"].dt, "tz", None) is not None:
        customer_num["registration_date"] = customer_num[
            "registration_date"
        ].dt.tz_localize(None)
    customer_num["tenure_days"] = (
        as_of - customer_num["registration_date"]
    ).dt.days.astype("float64")
    customer_num = customer_num.drop(columns=["registration_date"])

    merged = customer_num.merge(beh, on="customer_id", how="left")
    merged = add_monetary_type_shares(merged)

    # Merge trajectory features (activity decay / continuity signals)
    traj = build_trajectory_features(df_tx, as_of_date, w_start)
    merged = merged.merge(traj, on="customer_id", how="left")
    # Customers with no transactions in the window get neutral trajectory values
    merged["activity_trend_ratio"] = merged["activity_trend_ratio"].fillna(1.0)
    merged["active_months_ratio"] = merged["active_months_ratio"].fillna(0.0)
    merged["tenure_utilization"] = merged["tenure_utilization"].fillna(0.0)
    merged["last_6m_active_months"] = merged["last_6m_active_months"].fillna(0.0)
    merged["early_window_freq_ratio"] = merged["early_window_freq_ratio"].fillna(0.5)

    # --- tx_per_active_month ---
    # Avg transactions per calendar month when active.  Encodes per-segment
    # intensity (high-value: ~40/month; churner: ~2/month).  We approximate
    # active_months as active_months_ratio × tenure_days / 30.44 days; clip to
    # at least 1 to avoid division by zero for brand-new customers.
    _active_months_approx = (
        merged["active_months_ratio"] * merged["tenure_days"] / 30.44
    ).clip(lower=1.0)
    merged["tx_per_active_month"] = (
        merged["frequency_total"].fillna(0) / _active_months_approx
    ).clip(lower=0.0)

    # --- days_to_first_tx (optional — requires full transaction history) ---
    if df_tx_full is not None:
        _full = df_tx_full.copy()
        _full["transaction_datetime"] = pd.to_datetime(_full["transaction_datetime"])
        if getattr(_full["transaction_datetime"].dt, "tz", None) is not None:
            _full["transaction_datetime"] = _full[
                "transaction_datetime"
            ].dt.tz_localize(None)
        _first_global = (
            _full.groupby("customer_id", sort=False)["transaction_datetime"]
            .min()
            .rename("first_tx_date_global")
        )
        _reg = (
            df_customers[["customer_id", "registration_date"]]
            .drop_duplicates(subset=["customer_id"])
            .copy()
        )
        _reg["registration_date"] = pd.to_datetime(_reg["registration_date"])
        if getattr(_reg["registration_date"].dt, "tz", None) is not None:
            _reg["registration_date"] = _reg["registration_date"].dt.tz_localize(None)
        _act = _first_global.reset_index().merge(_reg, on="customer_id", how="left")
        _act["days_to_first_tx"] = (
            (_act["first_tx_date_global"] - _act["registration_date"])
            .dt.days.clip(lower=0)
            .astype("float64")
        )
        merged = merged.merge(
            _act[["customer_id", "days_to_first_tx"]], on="customer_id", how="left"
        )
        # Customers never seen in full history get tenure_days as fallback
        merged["days_to_first_tx"] = merged["days_to_first_tx"].fillna(
            merged["tenure_days"]
        )

    return merged


def add_monetary_type_shares(df: pd.DataFrame) -> pd.DataFrame:
    """Add purchase / transfer / cash_withdrawal shares of ``monetary_total``.

    Each share is the corresponding non-refund monetary split divided by
    ``monetary_total``, clipped to ``[0, 1]``. When ``monetary_total`` is zero or
    missing, all three shares are zero. Raw split columns are filled with 0.0
    if absent (same convention as ``build_behavioral_features``).

    These features capture *how* customers use the wallet (composition) rather
    than only intensity, and are safe to keep when ``drop_correlated_splits``
    removes redundant raw split columns that track ``monetary_total`` too
    closely.
    """
    out = df.copy()
    if "monetary_total" not in out.columns:
        for c in MONETARY_SHARE_COLS:
            out[c] = 0.0
        return out

    for col in ("monetary_purchase", "monetary_transfer", "monetary_cash_withdrawal"):
        if col not in out.columns:
            out[col] = 0.0
        else:
            out[col] = out[col].fillna(0.0)

    denom = out["monetary_total"].replace(0, np.nan)
    out["monetary_purchase_share"] = (
        (out["monetary_purchase"] / denom).fillna(0.0).clip(0.0, 1.0)
    )
    out["monetary_transfer_share"] = (
        (out["monetary_transfer"] / denom).fillna(0.0).clip(0.0, 1.0)
    )
    out["monetary_cash_withdrawal_share"] = (
        (out["monetary_cash_withdrawal"] / denom).fillna(0.0).clip(0.0, 1.0)
    )
    return out


def drop_correlated_splits(
    df: pd.DataFrame,
    *,
    threshold: float = 0.9,
) -> tuple[pd.DataFrame, list[str], pd.DataFrame | None]:
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
    cleaned_df : pd.DataFrame
    dropped_column_names : list[str]
    corr_monetary_splits : pd.DataFrame or None
        Pearson correlation matrix among ``monetary_total`` and present split
        columns (for notebooks: ``display(corr_monetary_splits)`` instead of
        printing a wide text block). ``None`` if ``monetary_total`` is absent.
    """
    split_cols = [
        "monetary_purchase",
        "monetary_transfer",
        "monetary_cash_withdrawal",
    ]
    dropped: list[str] = []
    keep_df = df.copy()
    if "monetary_total" not in keep_df.columns:
        return keep_df, dropped, None

    corr_candidates = ["monetary_total"] + [
        c for c in split_cols if c in keep_df.columns
    ]
    corr_monetary_splits: pd.DataFrame | None = None
    if len(corr_candidates) > 1:
        corr_monetary_splits = keep_df[corr_candidates].corr()

    for col in split_cols:
        if col not in keep_df.columns:
            continue
        corr = keep_df[["monetary_total", col]].corr().iloc[0, 1]
        if np.isfinite(corr) and abs(float(corr)) > threshold:
            dropped.append(col)

    if dropped:
        keep_df = keep_df.drop(columns=dropped)
    return keep_df, dropped, corr_monetary_splits


def build_product_flag_features(
    df_customer_products: pd.DataFrame,
    products_raw: pd.DataFrame,
) -> pd.DataFrame:
    """Return binary ownership flags and cancellation rate per customer.

    Columns returned (one row per customer_id):
    - has_wallet, has_credit_card, has_investment, has_insurance, has_loan (0/1 int)
    - product_cancellation_rate: fraction of acquired products that are inactive [0.0-1.0]

    Designed to expose the segment-specific ownership probabilities planted by
    the generator (e.g., investment: 65% high_value vs 10% at_risk_churner).

    Parameters
    ----------
    df_customer_products :
        DataFrame with columns ``customer_id``, ``product_id``, ``start_date``,
        ``is_active``. Each row represents a customer's product ownership record.
    products_raw :
        DataFrame with columns ``product_id``, ``product_type``. Used to map
        product types to customer ownership rows.

    Returns
    -------
    pd.DataFrame
        One row per unique customer_id with columns:
        ``["customer_id", "has_wallet", "has_credit_card", "has_investment",
        "has_insurance", "has_loan", "product_cancellation_rate"]``
        If ``df_customer_products`` is empty, returns an empty DataFrame with
        the correct column structure.
    """
    PRODUCT_TYPES = ["wallet", "credit_card", "investment", "insurance", "loan"]

    if df_customer_products.empty:
        return pd.DataFrame(
            columns=["customer_id"]
            + [f"has_{pt}" for pt in PRODUCT_TYPES]
            + ["product_cancellation_rate"]
        )

    # Merge to get product_type for each customer-product relationship
    merged = df_customer_products.merge(
        products_raw[["product_id", "product_type"]], on="product_id", how="left"
    )

    # Drop rows where product_id has no match in catalog (data integrity guard).
    # This prevents NaN product_type values from propagating into the flag logic.
    merged = merged.dropna(subset=["product_type"])

    if merged.empty:
        return pd.DataFrame(
            columns=["customer_id"]
            + [f"has_{pt}" for pt in PRODUCT_TYPES]
            + ["product_cancellation_rate"]
        )

    # Compute product cancellation rate before filtering to active-only.
    # Cancel rate = (total rows - active count) / total rows per customer.
    cancel_rate = (
        merged.groupby("customer_id")["is_active"]
        .apply(lambda grp: float((~grp.astype(bool)).sum() / len(grp)))
        .rename("product_cancellation_rate")
    )

    # Vectorized binary flags via pd.get_dummies + groupby.max().
    # get_dummies creates columns named after the product type values;
    # groupby.max() takes the max (1 if any row has that product type).
    dummies = pd.get_dummies(merged["product_type"].astype(str)).astype(int)
    dummies["customer_id"] = merged["customer_id"].values
    flags_df = dummies.groupby("customer_id", sort=False).max()

    # Ensure all product type columns exist (in case a type is missing from data).
    for pt in PRODUCT_TYPES:
        if pt not in flags_df.columns:
            flags_df[pt] = 0

    # Rename columns to has_<product_type> format
    rename_dict = {pt: f"has_{pt}" for pt in PRODUCT_TYPES}
    flags_df = flags_df.rename(columns=rename_dict)

    # Keep only the flag columns we care about and join with cancellation rate
    flag_cols = [f"has_{pt}" for pt in PRODUCT_TYPES]
    result = flags_df[flag_cols].join(cancel_rate)
    result["product_cancellation_rate"] = result["product_cancellation_rate"].fillna(0.0)
    return result.reset_index()


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
    "MONETARY_SHARE_COLS",
    "add_monetary_type_shares",
    "build_behavioral_features",
    "build_trajectory_features",
    "build_customer_feature_matrix",
    "build_product_flag_features",
    "drop_correlated_splits",
    "build_preprocessing_pipeline",
]
