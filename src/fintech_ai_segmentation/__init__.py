"""Fintech AI Segmentation — synthetic data generation and feature engineering."""

from .rfm_features import (
    LOG1P_COLS,
    PASSTHROUGH_COLS,
    SQRT_COLS,
    build_behavioral_features,
    build_customer_feature_matrix,
    build_preprocessing_pipeline,
    drop_correlated_splits,
)

__all__ = [
    "LOG1P_COLS",
    "SQRT_COLS",
    "PASSTHROUGH_COLS",
    "build_behavioral_features",
    "build_customer_feature_matrix",
    "build_preprocessing_pipeline",
    "drop_correlated_splits",
]
