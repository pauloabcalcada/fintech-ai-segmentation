-- Supabase base schema for SynaptiqPay raw tables.
-- These tables are populated from Faker-generated CSV/Parquet files.

create table if not exists customers_raw (
    customer_id uuid primary key,
    name text not null,
    email text not null,
    age integer not null check (age between 18 and 110),
    state text not null,
    registration_date timestamp with time zone not null,
    acquisition_channel text not null check (acquisition_channel in ('paid_ads', 'organic', 'referral', 'partnership')),
    acquisition_cost numeric(12,2) not null check (acquisition_cost >= 0),
    true_segment text not null check (true_segment in ('high_value_active', 'mid_value_regular', 'low_value_dormant', 'at_risk_churner'))
);


create table if not exists products_raw (
    product_id uuid primary key,
    product_name text not null,
    product_type text not null check (product_type in ('wallet', 'credit_card', 'investment', 'insurance', 'loan'))
);


create table if not exists transactions_raw (
    transaction_id uuid primary key,
    customer_id uuid not null references customers_raw(customer_id),
    transaction_datetime timestamp with time zone not null,
    amount numeric(14,2) not null,
    transaction_type text not null check (transaction_type in ('purchase', 'transfer', 'cash_withdrawal', 'fee', 'refund')),
    product_type text not null check (product_type in ('wallet', 'credit_card', 'investment', 'insurance', 'loan')),
    channel text not null check (channel in ('in_app', 'card_present', 'online', 'atm')),
    status text not null check (status in ('completed', 'pending', 'failed', 'reversed'))
);


create table if not exists customer_products_raw (
    customer_id uuid not null references customers_raw(customer_id),
    product_id uuid not null references products_raw(product_id),
    start_date timestamp with time zone not null,
    is_active boolean not null default true,
    primary key (customer_id, product_id)
);


-- Suggested loading strategy (documentation):
-- 1. Generate base tables in a notebook or script using `faker_base_generation.generate_all_base_tables`.
-- 2. Export each DataFrame to CSV (UTF-8, with header).
-- 3. Use Supabase UI or a scripted COPY command to load:
--      customers_raw.csv       -> customers_raw
--      products_raw.csv        -> products_raw
--      transactions_raw.csv    -> transactions_raw
--      customer_products_raw.csv -> customer_products_raw
-- 4. Add indexes as needed for query performance (e.g. on customer_id, transaction_datetime).

