-- customer_analysis mart — pre-computed RFM scores, K-Means labels, and lifecycle metadata.
-- Written by scripts/data_loader.py (Stage 4) and by notebooks/3.EDA_RFM_Clustering.ipynb.
-- Safe to re-run: CREATE TABLE IF NOT EXISTS.
--
-- Load order (three-file schema setup):
--   1. base_schema.sql            — raw tables (customers_raw, transactions_raw, etc.)
--   2. phase1_app_layer.sql       — app-layer tables (recommendation_log, cohort matrices)
--   3. customer_analysis_schema.sql — this file (mart depends on customers_raw FK)

create table if not exists customer_analysis (
    -- Identity (from customers_raw)
    customer_id             uuid primary key references customers_raw(customer_id),
    age                     integer,
    state                   text,
    acquisition_channel     text,
    acquisition_cost        numeric,
    registration_date       timestamp,
    true_segment            text,

    -- Behavioural features (from build_customer_feature_matrix)
    tenure_days             numeric,
    recency_days            numeric,
    frequency_total         integer,
    monetary_total          numeric,
    avg_ticket              numeric,
    monetary_purchase       numeric,
    monetary_transfer       numeric,
    monetary_cash_withdrawal        numeric,
    monetary_purchase_share         numeric,
    monetary_transfer_share         numeric,
    monetary_cash_withdrawal_share  numeric,
    refund_rate             numeric,
    avg_days_between_tx     numeric,
    products_owned          integer,
    activity_trend_ratio    numeric,
    active_months_ratio     numeric,
    last_6m_active_months   integer,
    tenure_utilization      numeric,
    early_window_freq_ratio numeric,
    tx_per_active_month     numeric,
    days_to_first_tx        numeric,

    -- Global transaction rollups (full history, not windowed)
    first_tx_global         timestamp,
    last_tx_global          timestamp,
    n_tx_completed_global   bigint,

    -- K-Means segment (active_clustered customers only; NULL for all other lifecycle stages)
    cluster_km              integer,
    cluster_name            text,

    -- Lifecycle
    lifecycle_stage         text,

    -- Group A: RFM quintile scores (active_clustered only; NULL otherwise)
    recency_score           integer,
    frequency_score         integer,
    monetary_score          integer,
    rfm_score               numeric,

    -- Group B: Product intelligence
    has_wallet              boolean,
    has_credit_card         boolean,
    has_investment          boolean,
    has_insurance           boolean,
    has_loan                boolean,
    primary_product_type    text,
    products_active_last_6m integer,

    -- Group C: Human-readable labels
    age_group               text,
    tenure_months           numeric,
    engagement_status       text,
    activity_health_label   text,
    annualized_revenue      numeric,
    cac_payback_months      numeric,

    -- Group D: Never-transacted signal
    days_registered_without_tx  numeric,

    -- Group E: Lineage and reproducibility metadata
    rfm_window_start        timestamp,
    rfm_window_end_excl     timestamp,
    analysis_as_of_date     timestamp,
    mart_built_at           timestamp
);
