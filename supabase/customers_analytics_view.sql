-- Final unified analytical view for SynaptiqPay customers.
-- This view assumes that downstream ETL has produced the following tables:
--   - customers_raw
--   - customers_features        (per-customer aggregates from transactions)
--   - customers_rfm             (RFM scores + predicted_segment)
--   - customers_cohorts         (cohort_retention_rate or similar metrics)
--   - customers_ml_features     (ltv, ltv_cac_ratio, payback_period_months, churn_probability)

create or replace view customers_analytics as
select
    c.customer_id,
    c.name,
    c.email,
    c.age,
    c.state,
    c.registration_date,
    c.acquisition_channel,
    c.acquisition_cost,
    c.true_segment,

    f.avg_monthly_balance,
    f.avg_transaction_ticket,
    f.monthly_transactions_count,
    f.total_spent_12m,
    f.total_deposits_12m,
    f.credit_limit,
    f.credit_utilization_pct,
    f.avg_monthly_revenue,

    f.days_since_last_transaction,
    f.days_since_last_login,
    f.monthly_app_logins,
    f.support_tickets_6m,

    f.products_owned,
    f.has_credit_card,
    f.has_investments,
    f.has_insurance,
    f.has_loans,

    r.recency_score,
    r.frequency_score,
    r.monetary_score,
    r.rfm_score,
    r.predicted_segment,

    coh.cohort_month,
    coh.cohort_retention_rate,
    coh.tenure_months,

    ml.ltv,
    ml.ltv_cac_ratio,
    ml.payback_period_months,
    ml.churn_probability
from customers_raw c
left join customers_features f
    on f.customer_id = c.customer_id
left join customers_rfm r
    on r.customer_id = c.customer_id
left join customers_cohorts coh
    on coh.customer_id = c.customer_id
left join customers_ml_features ml
    on ml.customer_id = c.customer_id;

