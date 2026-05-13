"""Cohort aggregate builders for Supabase materialisation."""

from __future__ import annotations

import pandas as pd


def build_cohort_activity_matrix(grid: pd.DataFrame) -> pd.DataFrame:
    """Aggregate a customer-level activity grid into a (cohort_month, activity_month) matrix.

    Parameters
    ----------
    grid:
        DataFrame with columns [customer_id, cohort_month, calendar_month, has_tx].
        Each row is one (customer, tenure-slot) observation from the cohort analysis.

    Returns
    -------
    DataFrame with columns [cohort_month, activity_month, active_rate, cohort_size].
    One row per unique (cohort_month, calendar_month) pair.
    """
    if grid.empty:
        return pd.DataFrame(columns=["cohort_month", "activity_month", "active_rate", "cohort_size"])

    cohort_sizes = (
        grid.groupby("cohort_month")["customer_id"]
        .nunique()
        .rename("cohort_size")
        .reset_index()
    )

    activity = (
        grid.groupby(["cohort_month", "calendar_month"])["has_tx"]
        .sum()
        .rename("active_count")
        .reset_index()
    )

    result = activity.merge(cohort_sizes, on="cohort_month")
    result["active_rate"] = result["active_count"] / result["cohort_size"]

    return (
        result
        .rename(columns={"calendar_month": "activity_month"})
        .drop(columns="active_count")
        [["cohort_month", "activity_month", "active_rate", "cohort_size"]]
        .reset_index(drop=True)
    )


def build_channel_m6_retention(channel_kpi: pd.DataFrame) -> pd.DataFrame:
    """Extract M6 retention per (acquisition_channel, cohort_month) from channel_kpi.

    Parameters
    ----------
    channel_kpi:
        DataFrame produced by the channel KPI aggregation in Notebook 2.
        Must contain [cohort_month, acquisition_channel, eligible_n_h6, m6_active_rate].

    Returns
    -------
    DataFrame with columns [acquisition_channel, cohort_month, m6_active_rate, cohort_size].
    Rows with no M6-eligible customers (eligible_n_h6 == 0 or m6_active_rate is NaN) are dropped.
    """
    if channel_kpi.empty:
        return pd.DataFrame(
            columns=["acquisition_channel", "cohort_month", "m6_active_rate", "cohort_size"]
        )

    result = (
        channel_kpi[["cohort_month", "acquisition_channel", "eligible_n_h6", "m6_active_rate"]]
        .rename(columns={"eligible_n_h6": "cohort_size"})
        .dropna(subset=["m6_active_rate"])
        .loc[lambda df: df["cohort_size"] > 0]
        .reset_index(drop=True)
    )

    return result[["acquisition_channel", "cohort_month", "m6_active_rate", "cohort_size"]]
