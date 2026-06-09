-- Phase 1 application layer tables for SynaptiqPay.
-- Execute in Supabase SQL editor. Safe to re-run (IF NOT EXISTS).

-- Append-only audit trail and rate-limit store for AI recommendations.
create table if not exists recommendation_log (
    id              uuid primary key default gen_random_uuid(),
    customer_id     uuid not null references customers_raw(customer_id),
    ip_address      text not null,
    model_used      text not null,
    language        text not null default 'en',
    generated_at    timestamptz not null default now(),
    recommendation_json jsonb not null
);

create index if not exists recommendation_log_customer_time
    on recommendation_log (customer_id, generated_at);

create index if not exists recommendation_log_ip_time
    on recommendation_log (ip_address, generated_at);


-- Pre-computed cohort heatmap data (written by Notebook 2).
create table if not exists cohort_activity_matrix (
    cohort_month    date not null,
    activity_month  date not null,
    active_rate     numeric not null,
    cohort_size     integer not null,
    primary key (cohort_month, activity_month)
);


-- Pre-computed M6 retention by acquisition channel (written by Notebook 2).
create table if not exists channel_m6_retention (
    acquisition_channel text not null,
    cohort_month        date not null,
    m6_active_rate      numeric not null,
    cohort_size         integer not null,
    primary key (acquisition_channel, cohort_month)
);
