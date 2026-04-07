"""Unit tests for RFM / preprocessing feature builders."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from fintech_ai_segmentation.rfm_features import (
    LOG1P_COLS,
    SQRT_COLS,
    build_behavioral_features,
    build_customer_feature_matrix,
    build_preprocessing_pipeline,
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
    df_cp = pd.DataFrame(columns=["customer_id", "product_id", "start_date", "is_active"])
    out = build_behavioral_features(df_tx, df_cp, as_of)
    expected = float((as_of - pd.Timestamp("2025-01-01")).days)
    assert out["avg_days_between_tx"].iloc[0] == pytest.approx(expected)


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
    cleaned, dropped = drop_correlated_splits(df, threshold=0.9)
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
    assert "age" in m.columns
    assert "acquisition_cost" in m.columns
    assert "tenure_days" in m.columns
    expected_tenure = (as_of - pd.Timestamp("2024-06-15")).days
    assert m["tenure_days"].iloc[0] == pytest.approx(expected_tenure)
    assert "registration_date" not in m.columns
    assert "state_is_sp" not in m.columns
    assert "channel_organic" not in m.columns


def test_transform_group_membership() -> None:
    """Transform groups should reflect the selected feature strategy."""
    assert "acquisition_cost" in LOG1P_COLS, "acquisition_cost should receive log1p (multi-modal right tail)"
    assert "avg_ticket" in LOG1P_COLS, "avg_ticket should receive log1p (right-skewed spend intensity)"
    assert "monetary_total" not in LOG1P_COLS, "monetary_total should not be log-transformed for clustering"
    assert "refund_rate" in SQRT_COLS, "refund_rate should receive sqrt (bounded rate, spike at 0)"
    assert "refund_rate" not in LOG1P_COLS, "refund_rate must not also be in LOG1P_COLS"
    assert "acquisition_cost" not in SQRT_COLS, "acquisition_cost must not also be in SQRT_COLS"


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
            "recency_days": [1.0, 4.0, 9.0],   # log1p col
            "refund_rate":  [1.0, 4.0, 9.0],   # sqrt col — same raw values
        }
    )
    pipe = build_preprocessing_pipeline(df.columns.tolist())
    X = pipe.fit_transform(df)
    # log1p([1,4,9]) = [0.693, 1.609, 2.303]; sqrt([1,4,9]) = [1, 2, 3]
    # After StandardScaler both are centered, but std-normalised values differ.
    col_recency = X[:, 0]
    col_refund  = X[:, 1]
    assert not np.allclose(col_recency, col_refund), (
        "recency_days (log1p) and refund_rate (sqrt) should produce different scaled values"
    )
