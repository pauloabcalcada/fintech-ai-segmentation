"""Unit tests for cohort aggregate builders (cohort_activity_matrix, channel_m6_retention)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from fintech_ai_segmentation.cohort_aggregates import (
    build_channel_m6_retention,
    build_cohort_activity_matrix,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def simple_grid() -> pd.DataFrame:
    """Minimal grid: 2 cohorts, each customer belongs to exactly one cohort.

    Jan cohort (c1, c2, c3): tenure slots jan + feb
    Feb cohort (c4, c5):     tenure slots feb + mar
    """
    jan = pd.Timestamp("2024-01-01")
    feb = pd.Timestamp("2024-02-01")
    mar = pd.Timestamp("2024-03-01")

    return pd.DataFrame(
        {
            "customer_id": ["c1", "c1", "c2", "c2", "c3", "c3", "c4", "c4", "c5", "c5"],
            "cohort_month": [jan, jan, jan, jan, jan, jan, feb, feb, feb, feb],
            "calendar_month": [jan, feb, jan, feb, jan, feb, feb, mar, feb, mar],
            "has_tx": [True, True, True, False, False, True, True, True, False, True],
            "acquisition_channel": ["A", "A", "A", "A", "A", "A", "B", "B", "B", "B"],
        }
    )
    # Jan cohort, calendar=feb: c1=True, c2=False, c3=True → active_rate=2/3, cohort_size=3
    # Feb cohort, calendar=mar: c4=True, c5=True → active_rate=1.0, cohort_size=2


@pytest.fixture
def simple_channel_kpi() -> pd.DataFrame:
    """Minimal channel_kpi: 2 channels × 2 cohort months."""
    jan = pd.Timestamp("2024-01-01")
    feb = pd.Timestamp("2024-02-01")

    return pd.DataFrame(
        {
            "cohort_month": [jan, jan, feb, feb],
            "acquisition_channel": ["organic", "referral", "organic", "referral"],
            "eligible_n_h6": [100, 50, 80, 0],
            "m6_active_count": [60, 30, 40, 0],
            "m6_active_rate": [0.60, 0.60, 0.50, np.nan],
            "eligible_n_h3": [120, 60, 100, 20],
            "m3_active_rate": [0.70, 0.65, 0.55, 0.30],
        }
    )


# ---------------------------------------------------------------------------
# build_cohort_activity_matrix
# ---------------------------------------------------------------------------


def test_cohort_activity_matrix_one_row_per_pair(simple_grid: pd.DataFrame) -> None:
    result = build_cohort_activity_matrix(simple_grid)

    pairs = result[["cohort_month", "activity_month"]].drop_duplicates()
    assert len(pairs) == len(result), "Duplicate (cohort_month, activity_month) pairs found"


def test_cohort_activity_matrix_active_rate_is_fraction_of_cohort(simple_grid: pd.DataFrame) -> None:
    result = build_cohort_activity_matrix(simple_grid)

    # Cohort jan, activity_month feb: c1 (True), c2 (True), c3 (False) → 2/3
    jan = pd.Timestamp("2024-01-01")
    feb = pd.Timestamp("2024-02-01")
    row = result[(result["cohort_month"] == jan) & (result["activity_month"] == feb)]
    assert len(row) == 1
    assert pytest.approx(row.iloc[0]["active_rate"]) == 2 / 3


def test_cohort_activity_matrix_cohort_size_counts_unique_customers(simple_grid: pd.DataFrame) -> None:
    result = build_cohort_activity_matrix(simple_grid)

    jan = pd.Timestamp("2024-01-01")
    jan_rows = result[result["cohort_month"] == jan]
    # cohort_size must be 3 (c1, c2, c3) for every activity_month in the jan cohort
    assert (jan_rows["cohort_size"] == 3).all(), "cohort_size must equal total unique customers in that cohort"


def test_cohort_activity_matrix_schema(simple_grid: pd.DataFrame) -> None:
    result = build_cohort_activity_matrix(simple_grid)

    assert set(result.columns) == {"cohort_month", "activity_month", "active_rate", "cohort_size"}


def test_cohort_activity_matrix_empty_input() -> None:
    empty = pd.DataFrame(
        columns=["customer_id", "cohort_month", "calendar_month", "has_tx", "acquisition_channel"]
    )
    result = build_cohort_activity_matrix(empty)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0


# ---------------------------------------------------------------------------
# build_channel_m6_retention
# ---------------------------------------------------------------------------


def test_channel_m6_retention_one_row_per_channel_cohort(simple_channel_kpi: pd.DataFrame) -> None:
    result = build_channel_m6_retention(simple_channel_kpi)

    pairs = result[["acquisition_channel", "cohort_month"]].drop_duplicates()
    assert len(pairs) == len(result)


def test_channel_m6_retention_drops_ineligible_rows(simple_channel_kpi: pd.DataFrame) -> None:
    result = build_channel_m6_retention(simple_channel_kpi)

    # Row with eligible_n_h6=0 and m6_active_rate=NaN must be excluded
    feb = pd.Timestamp("2024-02-01")
    ineligible = result[
        (result["acquisition_channel"] == "referral") & (result["cohort_month"] == feb)
    ]
    assert len(ineligible) == 0, "Ineligible row (eligible_n_h6=0) was not dropped"


def test_channel_m6_retention_maps_eligible_n_h6_to_cohort_size(simple_channel_kpi: pd.DataFrame) -> None:
    result = build_channel_m6_retention(simple_channel_kpi)

    jan = pd.Timestamp("2024-01-01")
    row = result[(result["acquisition_channel"] == "organic") & (result["cohort_month"] == jan)]
    assert row.iloc[0]["cohort_size"] == 100


def test_channel_m6_retention_schema(simple_channel_kpi: pd.DataFrame) -> None:
    result = build_channel_m6_retention(simple_channel_kpi)

    assert set(result.columns) == {"acquisition_channel", "cohort_month", "m6_active_rate", "cohort_size"}


def test_channel_m6_retention_empty_input() -> None:
    empty = pd.DataFrame(
        columns=["cohort_month", "acquisition_channel", "eligible_n_h6", "m6_active_rate"]
    )
    result = build_channel_m6_retention(empty)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0
