"""Unit tests for RFM / preprocessing feature builders."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from fintech_ai_segmentation.rfm_features import (
    LOG1P_COLS,
    MONETARY_SHARE_COLS,
    SQRT_COLS,
    add_monetary_type_shares,
    build_behavioral_features,
    build_customer_feature_matrix,
    build_preprocessing_pipeline,
    build_product_flag_features,
    build_product_monetary_shares,
    build_trajectory_features,
    drop_correlated_splits,
)


@pytest.fixture
def as_of() -> pd.Timestamp:
    return pd.Timestamp("2026-02-28")


def test_behavioral_rfm_and_refund_rate(as_of: pd.Timestamp) -> None:
    cid = "c1"
    df_tx = pd.DataFrame(
        {
            "customer_id": [cid, cid, cid, cid],
            "transaction_datetime": pd.to_datetime(
                ["2025-01-01", "2025-06-01", "2025-06-15", "2025-07-01"]
            ),
            "amount": [100.0, 50.0, -10.0, 20.0],
            "transaction_type": ["purchase", "purchase", "refund", "transfer"],
        }
    )
    df_cp = pd.DataFrame(
        {
            "customer_id": [cid],
            "product_id": ["p1"],
            "start_date": pd.to_datetime(["2024-01-01"]),
            "is_active": [True],
        }
    )

    out = build_behavioral_features(df_tx, df_cp, as_of)
    row = out.set_index("customer_id").loc[cid]

    assert row["frequency_total"] == 3
    assert row["monetary_total"] == pytest.approx(170.0)
    assert row["avg_ticket"] == pytest.approx(170.0 / 3.0)
    assert row["monetary_purchase"] == pytest.approx(150.0)
    assert row["monetary_transfer"] == pytest.approx(20.0)
    assert row["refund_rate"] == pytest.approx(1 / 4)
    assert row["products_owned"] == 1
    assert row["recency_days"] == (as_of - pd.Timestamp("2025-07-01")).days


def test_cadence_imputation_window_span(as_of: pd.Timestamp) -> None:
    cid = "c2"
    df_tx = pd.DataFrame(
        {
            "customer_id": [cid],
            "transaction_datetime": pd.to_datetime(["2025-01-01"]),
            "amount": [1.0],
            "transaction_type": ["purchase"],
        }
    )
    df_cp = pd.DataFrame(
        columns=["customer_id", "product_id", "start_date", "is_active"]
    )
    out = build_behavioral_features(df_tx, df_cp, as_of)
    expected = float((as_of - pd.Timestamp("2025-01-01")).days)
    assert out["avg_days_between_tx"].iloc[0] == pytest.approx(expected)


def test_add_monetary_type_shares_zero_total() -> None:
    df = pd.DataFrame(
        {
            "customer_id": ["x"],
            "monetary_total": [0.0],
            "monetary_purchase": [0.0],
            "monetary_transfer": [0.0],
            "monetary_cash_withdrawal": [0.0],
        }
    )
    out = add_monetary_type_shares(df)
    assert out["monetary_purchase_share"].iloc[0] == 0.0
    assert out["monetary_transfer_share"].iloc[0] == 0.0
    assert out["monetary_cash_withdrawal_share"].iloc[0] == 0.0


def test_add_monetary_type_shares_mix() -> None:
    df = pd.DataFrame(
        {
            "monetary_total": [100.0],
            "monetary_purchase": [60.0],
            "monetary_transfer": [30.0],
            "monetary_cash_withdrawal": [10.0],
        }
    )
    out = add_monetary_type_shares(df)
    assert out["monetary_purchase_share"].iloc[0] == pytest.approx(0.6)
    assert out["monetary_transfer_share"].iloc[0] == pytest.approx(0.3)
    assert out["monetary_cash_withdrawal_share"].iloc[0] == pytest.approx(0.1)


def test_drop_correlated_splits() -> None:
    df = pd.DataFrame(
        {
            "customer_id": ["a", "b", "c", "d"],
            "monetary_total": [10.0, 20.0, 30.0, 40.0],
            "monetary_purchase": [9.0, 18.0, 27.0, 36.0],  # perfect corr
            "monetary_transfer": [1.0, 2.0, 5.0, 6.0],
            "monetary_cash_withdrawal": [0.2, 0.1, 0.7, 0.4],
        }
    )
    cleaned, dropped, corr = drop_correlated_splits(df, threshold=0.9)
    assert corr is not None
    assert "monetary_purchase" in dropped
    assert "monetary_purchase" not in cleaned.columns


def test_full_matrix_merge_has_only_numeric_demographics(as_of: pd.Timestamp) -> None:
    cid = "c3"
    df_tx = pd.DataFrame(
        {
            "customer_id": [cid],
            "transaction_datetime": [pd.Timestamp("2025-12-01")],
            "amount": [10.0],
            "transaction_type": ["purchase"],
        }
    )
    df_cp = pd.DataFrame(
        {"customer_id": [], "product_id": [], "start_date": [], "is_active": []}
    )
    df_c = pd.DataFrame(
        {
            "customer_id": [cid],
            "acquisition_channel": ["organic"],
            "state": ["MG"],
            "age": [28.0],
            "acquisition_cost": [150.0],
            "registration_date": pd.to_datetime(["2024-06-15"]),
            "true_segment": ["mid_value_regular"],
        }
    )

    m = build_customer_feature_matrix(df_tx, df_cp, df_c, as_of)
    assert len(m) == 1
    for c in MONETARY_SHARE_COLS:
        assert c in m.columns
    assert m["monetary_purchase_share"].iloc[0] == pytest.approx(1.0)
    assert m["monetary_transfer_share"].iloc[0] == pytest.approx(0.0)
    assert m["monetary_cash_withdrawal_share"].iloc[0] == pytest.approx(0.0)
    assert "age" in m.columns
    assert "acquisition_cost" in m.columns
    assert "tenure_days" in m.columns
    expected_tenure = (as_of - pd.Timestamp("2024-06-15")).days
    assert m["tenure_days"].iloc[0] == pytest.approx(expected_tenure)
    assert "registration_date" not in m.columns
    assert "state_is_sp" not in m.columns
    assert "channel_organic" not in m.columns


def test_drop_correlated_splits_no_monetary_total() -> None:
    """When monetary_total is absent the function returns (df_unchanged, [], None)."""
    df = pd.DataFrame(
        {
            "customer_id": ["a", "b"],
            "monetary_purchase": [10.0, 20.0],
            "monetary_transfer": [5.0, 3.0],
        }
    )
    cleaned, dropped, corr = drop_correlated_splits(df, threshold=0.9)
    assert dropped == [], "No columns should be dropped when monetary_total is absent"
    assert corr is None, "corr_monetary_splits should be None when monetary_total is absent"
    assert list(cleaned.columns) == list(df.columns), "DataFrame should be unchanged"


def test_transform_group_membership() -> None:
    """Transform groups should reflect the selected feature strategy."""
    assert (
        "acquisition_cost" in LOG1P_COLS
    ), "acquisition_cost should receive log1p (multi-modal right tail)"
    assert (
        "avg_ticket" in LOG1P_COLS
    ), "avg_ticket should receive log1p (right-skewed spend intensity)"
    assert (
        "monetary_total" not in LOG1P_COLS
    ), "monetary_total should not be log-transformed for clustering"
    assert (
        "refund_rate" in SQRT_COLS
    ), "refund_rate should receive sqrt (bounded rate, spike at 0)"
    assert "refund_rate" not in LOG1P_COLS, "refund_rate must not also be in LOG1P_COLS"
    assert (
        "acquisition_cost" not in SQRT_COLS
    ), "acquisition_cost must not also be in SQRT_COLS"


def test_preprocessing_pipeline_shape_and_finiteness(as_of: pd.Timestamp) -> None:
    df = pd.DataFrame(
        {
            "recency_days": [1.0, 5.0, 10.0],
            "frequency_total": [1.0, 2.0, 3.0],
            "avg_ticket": [10.0, 20.0, 30.0],
            "avg_days_between_tx": [2.0, 3.0, 5.0],
            "acquisition_cost": [100.0, 200.0, 300.0],
            "refund_rate": [0.1, 0.2, 0.0],
            "products_owned": [1, 2, 3],
            "age": [25.0, 35.0, 45.0],
            "tenure_days": [365.0, 730.0, 180.0],
            "monetary_transfer": [1.0, 2.0, 3.0],
        }
    )
    pipe = build_preprocessing_pipeline(df.columns.tolist())
    X = pipe.fit_transform(df)
    assert X.shape == (3, len(df.columns))
    assert np.all(np.isfinite(X))


def test_preprocessing_pipeline_sqrt_applied_to_refund_rate() -> None:
    """After pipeline, refund_rate column should reflect sqrt transform (not log1p).

    With identical values for refund_rate and a log1p column, after StandardScaler
    the scaled values must differ because sqrt(x) != log1p(x) for x > 0.
    """
    df = pd.DataFrame(
        {
            "recency_days": [1.0, 4.0, 9.0],  # log1p col
            "refund_rate": [1.0, 4.0, 9.0],  # sqrt col — same raw values
        }
    )
    pipe = build_preprocessing_pipeline(df.columns.tolist())
    X = pipe.fit_transform(df)
    # log1p([1,4,9]) = [0.693, 1.609, 2.303]; sqrt([1,4,9]) = [1, 2, 3]
    # After StandardScaler both are centered, but std-normalised values differ.
    col_recency = X[:, 0]
    col_refund = X[:, 1]
    assert not np.allclose(
        col_recency, col_refund
    ), "recency_days (log1p) and refund_rate (sqrt) should produce different scaled values"


# ---------------------------------------------------------------------------
# Trajectory feature tests
# ---------------------------------------------------------------------------


def _tx_df(
    customer_id: str, dates: list[str], tx_type: str = "purchase"
) -> pd.DataFrame:
    """Helper: build a minimal transaction DataFrame for one customer."""
    return pd.DataFrame(
        {
            "customer_id": customer_id,
            "transaction_datetime": pd.to_datetime(dates),
            "transaction_type": tx_type,
        }
    )


@pytest.fixture
def window_start() -> pd.Timestamp:
    return pd.Timestamp("2024-03-01")


def test_activity_trend_ratio_decay_vs_growth(
    as_of: pd.Timestamp, window_start: pd.Timestamp
) -> None:
    """Churner (all activity in first half) gets ratio < 1; grower gets ratio > 1."""
    # Customer A: all transactions in first half (2024-03 to 2024-08) — decay pattern
    df_decay = _tx_df(
        "decay",
        ["2024-04-01", "2024-05-15", "2024-06-20", "2024-07-10"],
    )
    # Customer B: all transactions in second half (2025-03 to 2026-02) — growth pattern
    df_growth = _tx_df(
        "growth",
        ["2025-04-01", "2025-07-15", "2025-11-01", "2026-01-20"],
    )
    df_tx = pd.concat([df_decay, df_growth], ignore_index=True)

    out = build_trajectory_features(df_tx, as_of, window_start).set_index("customer_id")

    assert (
        out.loc["decay", "activity_trend_ratio"] < 1.0
    ), "Customer with only early activity should have trend ratio < 1"
    assert (
        out.loc["growth", "activity_trend_ratio"] > 1.0
    ), "Customer with only recent activity should have trend ratio > 1"


def test_active_months_ratio_calculation(
    as_of: pd.Timestamp, window_start: pd.Timestamp
) -> None:
    """Customer active in 6 out of ~24 possible months from first-tx to as_of."""
    # First transaction: 2024-03-15 → first month = 2024-03
    # as_of = 2026-02-28 → ~24 months span
    # Transactions in exactly 6 distinct months
    dates = [
        "2024-03-15",
        "2024-06-01",
        "2024-09-10",
        "2024-12-05",
        "2025-03-20",
        "2025-09-01",
    ]
    df_tx = _tx_df("c1", dates)
    out = build_trajectory_features(df_tx, as_of, window_start).set_index("customer_id")

    ratio = out.loc["c1", "active_months_ratio"]
    # 6 active months / ~24 months ≈ 0.25  (within 10% tolerance)
    assert (
        0.15 <= ratio <= 0.40
    ), f"active_months_ratio={ratio:.3f} out of expected range"


def test_tenure_utilization_calculation(
    as_of: pd.Timestamp, window_start: pd.Timestamp
) -> None:
    """Customer with 6 active months out of 24-month tenure → utilization ~0.25."""
    dates = [
        "2024-03-15",
        "2024-06-01",
        "2024-09-10",
        "2024-12-05",
        "2025-03-20",
        "2025-09-01",
    ]
    # Provide registration_date so tenure_utilization uses it as anchor
    df_tx = _tx_df("c1", dates)
    # tenure_utilization falls back to first_tx_date when no registration_date column
    out = build_trajectory_features(df_tx, as_of, window_start).set_index("customer_id")

    util = out.loc["c1", "tenure_utilization"]
    assert 0.15 <= util <= 0.40, f"tenure_utilization={util:.3f} out of expected range"


def test_trajectory_features_single_tx_customer(
    as_of: pd.Timestamp, window_start: pd.Timestamp
) -> None:
    """Customer with a single transaction gets sensible, finite trajectory values."""
    df_tx = _tx_df("solo", ["2025-06-01"])
    out = build_trajectory_features(df_tx, as_of, window_start).set_index("customer_id")

    row = out.loc["solo"]
    # With Laplace smoothing, ratio = (0+1)/(0+1) = 1.0 or (1+1)/(0+1) = 2.0
    assert np.isfinite(row["activity_trend_ratio"]), "trend ratio must be finite"
    assert (
        0.0 <= row["active_months_ratio"] <= 1.0
    ), "active_months_ratio must be in [0,1]"
    assert (
        0.0 <= row["tenure_utilization"] <= 1.0
    ), "tenure_utilization must be in [0,1]"


def test_build_customer_feature_matrix_includes_trajectory(as_of: pd.Timestamp) -> None:
    """Updated build_customer_feature_matrix output includes all 3 trajectory columns."""
    cid = "c_traj"
    df_tx = pd.DataFrame(
        {
            "customer_id": [cid, cid, cid],
            "transaction_datetime": pd.to_datetime(
                ["2024-04-01", "2025-01-15", "2025-10-20"]
            ),
            "amount": [100.0, 80.0, 60.0],
            "transaction_type": ["purchase", "purchase", "transfer"],
        }
    )
    df_cp = pd.DataFrame(
        {
            "customer_id": [cid],
            "product_id": ["p1"],
            "start_date": pd.to_datetime(["2024-01-01"]),
            "is_active": [True],
        }
    )
    df_c = pd.DataFrame(
        {
            "customer_id": [cid],
            "age": [32.0],
            "acquisition_cost": [120.0],
            "registration_date": pd.to_datetime(["2024-01-01"]),
            "true_segment": ["mid_value_regular"],
        }
    )

    matrix = build_customer_feature_matrix(df_tx, df_cp, df_c, as_of)

    for col in ("activity_trend_ratio", "active_months_ratio", "tenure_utilization"):
        assert col in matrix.columns, f"Expected column '{col}' in feature matrix"
    # All trajectory values for a real customer must be finite and non-negative
    row = matrix.set_index("customer_id").loc[cid]
    assert row["activity_trend_ratio"] >= 0
    assert 0.0 <= row["active_months_ratio"] <= 1.0
    assert 0.0 <= row["tenure_utilization"] <= 1.0


def test_trajectory_transform_group_membership() -> None:
    """Trajectory features must be in the correct transform groups."""
    assert (
        "activity_trend_ratio" in LOG1P_COLS
    ), "activity_trend_ratio should receive log1p (right-skewed ratio)"
    assert (
        "active_months_ratio" not in LOG1P_COLS
    ), "active_months_ratio is bounded [0,1] and should be passthrough"
    assert (
        "tenure_utilization" not in LOG1P_COLS
    ), "tenure_utilization is bounded [0,1] and should be passthrough"


# ---------------------------------------------------------------------------
# Product flag feature tests
# ---------------------------------------------------------------------------


def test_build_product_flag_features_basic() -> None:
    """Test binary product flags and cancellation rate computation."""
    products = pd.DataFrame(
        [
            ("p1", "wallet"),
            ("p2", "credit_card"),
            ("p3", "investment"),
            ("p4", "insurance"),
            ("p5", "loan"),
        ],
        columns=["product_id", "product_type"],
    )
    cp = pd.DataFrame(
        [
            ("c1", "p1", "2024-01-01", True),
            ("c1", "p2", "2024-01-01", True),
            ("c1", "p3", "2024-01-01", True),
            ("c2", "p1", "2024-01-01", True),
            ("c2", "p5", "2024-01-01", False),  # cancelled loan
        ],
        columns=["customer_id", "product_id", "start_date", "is_active"],
    )
    result = build_product_flag_features(cp, products)
    assert set(result.columns) == {
        "customer_id",
        "has_wallet",
        "has_credit_card",
        "has_investment",
        "has_insurance",
        "has_loan",
        "product_cancellation_rate",
    }
    c1 = result[result["customer_id"] == "c1"].iloc[0]
    assert c1["has_investment"] == 1
    assert c1["has_credit_card"] == 1
    assert c1["product_cancellation_rate"] == 0.0
    c2 = result[result["customer_id"] == "c2"].iloc[0]
    assert c2["has_investment"] == 0
    assert c2["has_loan"] == 1
    assert abs(c2["product_cancellation_rate"] - 0.5) < 0.01


def test_build_product_flag_features_no_products() -> None:
    """Test that empty customer_products DataFrame returns empty result."""
    products = pd.DataFrame(
        [("p1", "wallet"), ("p2", "credit_card")],
        columns=["product_id", "product_type"],
    )
    cp = pd.DataFrame(
        columns=["customer_id", "product_id", "start_date", "is_active"]
    )
    result = build_product_flag_features(cp, products)
    assert result.empty


def test_build_product_flag_features_selective_ownership() -> None:
    """Customer owning only wallet must get has_loan=0 (guards against closure bug)."""
    products = pd.DataFrame(
        [
            ("p1", "wallet"),
            ("p2", "loan"),
        ],
        columns=["product_id", "product_type"],
    )
    cp = pd.DataFrame(
        [
            ("c1", "p1", "2024-01-01", True),  # only wallet, no loan
        ],
        columns=["customer_id", "product_id", "start_date", "is_active"],
    )
    result = build_product_flag_features(cp, products)
    c1 = result[result["customer_id"] == "c1"].iloc[0]
    assert c1["has_wallet"] == 1
    assert c1["has_loan"] == 0
    assert c1["product_cancellation_rate"] == 0.0


# ---------------------------------------------------------------------------
# Product monetary shares feature tests
# ---------------------------------------------------------------------------


def test_build_product_monetary_shares_basic() -> None:
    """Test basic product monetary share calculation."""
    from datetime import datetime

    tx = pd.DataFrame(
        {
            "customer_id": ["c1", "c1", "c1", "c2"],
            "transaction_datetime": [datetime(2025, 1, 1)] * 4,
            "amount": [100.0, 500.0, 200.0, 300.0],
            "product_type": ["wallet", "investment", "credit_card", "wallet"],
            "status": ["completed"] * 4,
            "transaction_type": ["purchase", "transfer", "purchase", "purchase"],
        }
    )
    result = build_product_monetary_shares(tx)
    c1 = result[result["customer_id"] == "c1"].iloc[0]
    # wallet=100, investment=500, credit_card=200 → total=800
    assert abs(c1["wallet_monetary_share"] - 100 / 800) < 0.01
    assert abs(c1["investment_monetary_share"] - 500 / 800) < 0.01
    assert abs(c1["credit_card_monetary_share"] - 200 / 800) < 0.01
    assert abs(c1["loan_monetary_share"] - 0.0) < 0.01
    assert abs(c1["insurance_monetary_share"] - 0.0) < 0.01


def test_build_product_monetary_shares_zero_monetary() -> None:
    """Refunds and zero-amount transactions are filtered out; only positive amounts count."""
    from datetime import datetime

    tx = pd.DataFrame(
        {
            "customer_id": ["c1", "c1", "c1", "c2"],
            "transaction_datetime": [datetime(2025, 1, 1)] * 4,
            "amount": [100.0, -50.0, 0.0, 200.0],  # one positive, one refund, one zero, one positive
            "product_type": ["wallet", "wallet", "wallet", "wallet"],
            "status": ["completed"] * 4,
            "transaction_type": ["purchase", "refund", "purchase", "purchase"],
        }
    )
    result = build_product_monetary_shares(tx)
    # c1: only 100.0 (wallet) is counted (refund and zero excluded)
    c1 = result[result["customer_id"] == "c1"].iloc[0]
    assert abs(c1["wallet_monetary_share"] - 1.0) < 0.01
    # c2: 200.0 (wallet)
    c2 = result[result["customer_id"] == "c2"].iloc[0]
    assert abs(c2["wallet_monetary_share"] - 1.0) < 0.01
