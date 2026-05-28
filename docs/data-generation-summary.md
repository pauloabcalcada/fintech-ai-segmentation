# Data Generation Distributions Summary

This document provides a plain English overview of the statistical distributions used in `src/fintech_ai_segmentation/faker_base_generation.py` to generate synthetic customer and transaction data for SynaptiqPay.

## Overview

The synthetic data generator creates four interconnected tables (`customers_raw`, `transactions_raw`, `products_raw`, `customer_products_raw`) that mimic a real fintech data warehouse. The distributions are intentionally designed to create realistic segment separation (high-value, mid-value, dormant, at-risk churners) rather than uniform random data.

---

## Customer Attributes

### Registration Date (Gamma Distribution)

- **Distribution**: Gamma(shape=2.0, scale=360 days)
- **Purpose**: Models a realistic acquisition lifecycle for a startup fintech
- **Behavior**:
  - Starts from January 2022 (company launch)
  - Peaks around January 2023 (hyper-growth phase)
  - Gradually declines but remains visible through February 2026
  - Approximately 65% of customers registered before January 2024
  - Maintains 50–60 customers/month in the tail (not near-zero)
- **Why**: Avoids the "Beta tail-collapse" problem where later periods have almost zero registrations, ensuring a stable legacy baseline for the observation window

### Age (Normal Distribution)

- **Distribution**: Normal distribution, segment-specific parameters
- **Segment-specific profiles**:
  - **High-value**: μ=38 years, σ=9 years (slightly older, more affluent)
  - **Mid-value**: μ=33 years, σ=10 years (younger professionals)
  - **Low-value**: μ=42 years, σ=12 years (broader age range)
  - **At-risk**: μ=45 years, σ=11 years (older demographic)
- **Clipping**: All ages bounded to [18, 80] years

### Acquisition Cost (Normal Distribution)

- **Distribution**: Normal distribution, channel-specific parameters
- **Channel-specific profiles** (Mean ± Std in BRL):
  - **Organic**: 25 ± 10 BRL
  - **Referral**: 55 ± 15 BRL
  - **Partnership**: 110 ± 25 BRL
  - **Paid Ads**: 230 ± 50 BRL
- **Minimum**: 10 BRL (floored)
- **Why**: Higher-cost channels (paid ads, partnerships) naturally attract different customer segments

### State Distribution (Categorical)

- **Distribution**: Brazilian states with weighted probabilities
- **Tier-1 states** (highest economic activity): SP, RJ, MG
- **Tier-2 states**: Moderate representation
- **Tail states**: Lower but non-zero representation (min 0.3%)
- **Purpose**: Geographically realistic customer distribution

### Acquisition Channel (Categorical, Segment-Biased)

- **Distribution**: Multinomial, conditioned on segment via Bayesian inversion
- **Channel bias by segment**:
  - **Referral** attracts high-value customers (45% of referral customers are high-value)
  - **Organic** attracts mid-value (35%) and low-value (30%)
  - **Paid Ads** attracts low-value (30%) and at-risk (40%)
  - **Partnership** has balanced distribution across segments
- **Why**: Channels naturally have different segment quality; this is calibrated via customer-segment-channel relationships

---

## Transaction Activity

### Monthly Activity Probability (Bernoulli)

- **Distribution**: Bernoulli(p), segment-specific
- **Purpose**: Creates realistic inactivity gaps (dormancy) instead of scattering transactions uniformly
- **Segment profiles**:
  - **High-value**: p=0.95 (95% likely active in any given month)
  - **Mid-value**: p=0.85 (85% likely)
  - **Low-value**: p=0.40 (40% likely; often skips months)
  - **At-risk**: p=0.15 (15% likely; rarely active)

### Monthly Decay for Churn-Prone Segments (Exponential Decay)

- **Distribution**: Exponential decay applied to at-risk and low-value segments
- **Formula**: decay = exp(-0.25 × month_index)
- **Purpose**: As customers age, at-risk and dormant segments show accelerating inactivity/churn
- **Effect**: Recent months have lower expected activity for at-risk and low-value segments

### Transactions Per Active Month (Poisson)

- **Distribution**: Poisson(λ), segment-specific
- **Segment profiles** (average transactions per active month):
  - **High-value**: λ=40
  - **Mid-value**: λ=18
  - **Low-value**: λ=4
  - **At-risk**: λ=2
- **Adjustment**: Scaled by day_fraction (for M0 partial month) and seasonal factor
- **Why**: Poisson naturally captures the variation in transaction frequency; higher-value segments have more transactions when active

### Churn Event (Geometric Distribution)

- **Distribution**: Geometric(p), segment-specific hazard rates
- **Monthly hazard rates** (probability of churn each month):
  - **High-value**: 1% (11% churn within 12 months)
  - **Mid-value**: 4% (38% churn within 12 months)
  - **Low-value**: 8% (62% churn within 12 months)
  - **At-risk**: 18% (90% churn within 12 months)
- **Interpretation**: Once a customer churns, they stop transacting permanently
- **Why**: Different segments have fundamentally different lifetime expectations; mid-value is aggressive (intentionally) to show meaningful retention decline

---

## Transaction Details

### Transaction Amount (Normal Distribution)

- **Distribution**: Normal distribution, product-type-specific with segment-level baseline
- **Base**: Segment-specific average ticket amount
- **Product-type scaling** (multiplier on segment average):
  - **Wallet**: 0.30× (R$5–80 typical; small frequent transfers)
  - **Credit Card**: 1.00× (baseline; R$45–220 typical)
  - **Investment**: 6.00× (large deposits; R$270–1320+)
  - **Insurance**: 0.60× (fixed premium-like; R$27–132)
  - **Loan**: 8.00× (large periodic drawdowns; R$360–1760+)
- **Variability** (coefficient of variation):
  - **Wallet**: 25% (relatively consistent)
  - **Credit Card**: 40% (moderate variation)
  - **Investment**: 250% (high variation)
  - **Insurance**: 15% (low variation, premium-like)
  - **Loan**: 200% (high variation)
- **Minimum floor**: Product-specific to prevent unrealistic micro-transactions

### Transaction Type (Categorical)

- **Distribution**: Multinomial, product-type-specific (not segment-based)
- **Types**: purchase, transfer, cash_withdrawal, fee, refund
- **Order**: [purchase, transfer, cash_withdrawal, fee, refund]
- **Product-specific profiles** (updated 2026-04-10 for realism):
  - **Wallet**: 55% purchase, 30% transfer, 8% cash_withdrawal, 4% fee, 3% refund (daily spending & P2P)
  - **Credit Card**: 70% purchase, 0% transfer, 5% cash_withdrawal, 15% fee, 10% refund (card transactions & fees)
  - **Investment**: 0% purchase, 75% transfer, 0% cash_withdrawal, 25% fee, 0% refund (deposits/withdrawals & management fees)
  - **Insurance**: 0% purchase, 10% transfer, 0% cash_withdrawal, 75% fee, 15% refund (premium payments & claim refunds)
  - **Loan**: 0% purchase, 70% transfer, 0% cash_withdrawal, 30% fee, 0% refund (disbursements/repayments & fees)
- **Realism**: Eliminates unrealistic combos (e.g., no `cash_withdrawal` on investment, no `purchase` on loan)

### Transaction Channel (Categorical)

- **Distribution**: Multinomial, product-type-specific
- **Channels**: in_app, card_present, online, atm
- **Product-specific profiles**:
  - **Wallet**: 55% in_app, 32% online, 8% card_present, 5% atm (cash withdrawal via debit card)
  - **Credit Card**: 45% online, 38% card_present, 12% in_app, 5% atm
  - **Investment**: 50% in_app, 50% online, 0% card_present, 0% atm (digital-only; no card/ATM access)
  - **Insurance**: 54% in_app, 46% online, 0% card_present, 0% atm (digital-only; no card/ATM access)
  - **Loan**: 50% in_app, 50% online, 0% card_present, 0% atm (digital-only; no card/ATM access)

### Transaction Status (Categorical)

- **Distribution**: Multinomial (fixed)
- **Probabilities**: 93% completed, 3% pending, 2% failed, 2% reversed
- **Purpose**: Realistic operational variation without segment-level differences

### Product Selection Within Customer Pool (Weighted Sampling)

- **Distribution**: Multinomial with product-type weights (updated 2026-04-10)
- **Purpose**: Customers transact more frequently on daily-use products than occasional ones
- **Weights** (relative):
  - **Wallet**: 3.0 (high frequency; payments, transfers)
  - **Credit Card**: 3.0 (high frequency; purchases)
  - **Investment**: 0.5 (infrequent; periodic deposits)
  - **Insurance**: 0.3 (rare; premium payments)
  - **Loan**: 0.2 (rare; disbursements/repayments)
- **Effect**: Wallet + credit_card account for ~91% of transactions; investment/insurance/loan are appropriately sparse (5%, 2%, 1.5%)
- **Computation**: Weights are normalized once per customer from their active product pool; unknown product types fall back to weight 1.0

---

## Product Ownership & Lifecycle

### Product Cancellation Rate (Segment-Specific)

- **Distribution**: Bernoulli per product ownership, segment-specific (updated 2026-04-10)
- **Purpose**: Reflects different churn and disengagement patterns across segments
- **Cancellation rates** (probability product is inactive):
  - **High-value**: 5% cancelled (95% active; strong engagement)
  - **Mid-value**: 12% cancelled (88% active)
  - **Low-value**: 25% cancelled (75% active; higher dormancy)
  - **At-risk**: 40% cancelled (58% active; many abandoned products)
- **At-risk churner note**: High loan ownership (25% vs 10% investment) reflects financial stress; loan dependency increases as customer deteriorates

---

## Seasonal Effects

### Monthly Seasonality Factor (Multiplicative)

- **Distribution**: Month-specific multiplier (fixed calendar pattern)
- **Range**: 0.85 (low season) to 1.15 (high season)
- **Purpose**: Realistic monthly variation (e.g., higher spending in December)
- **Application**: Scales both probability of activity and expected transaction count

### Seasonal Sensitivity (Segment-Specific)

- **Distribution**: Segment-specific weight on seasonal effect
- **Purpose**: Different segments respond differently to calendar seasonality
- **High-value**: Smaller response (stable spending year-round)
- **At-risk**: Larger response (amplified seasonal dropout)

---

## Timespan and Observation Window

- **Registration Window**: January 1, 2022 – Present
- **Observation Window**: April 2024 – March 2026 (2 years)
- **Data Cutoff**: March 1, 2026 (TODAY)
- **Maximum History**: ~50 months from registration to present
- **M0 (Registration Month)**: Partial month, pro-rated by day-of-registration
- **M1–M50**: Full calendar months

---

## Key Design Principles

1. **Segment Separation via Behavioral Realism**
   - Dormancy (monthly dropout) creates the main separation, not just lower transaction counts
   - Churn (permanent exit) is geometric, segment-specific, and irreversible

2. **Product-Level Differentiation**
   - Transaction amounts, channels, and types vary by product
   - Transaction types are product-specific (e.g., investment only has transfers & fees, never purchases)
   - Customers have realistic product portfolios (not every product for every customer)

3. **Weighted Product Selection**
   - Daily-use products (wallet, credit_card) dominate transaction composition
   - Occasional products (investment, insurance, loan) are appropriately rare
   - Weights are customer-specific, computed from their actual active product portfolio

4. **Segment-Specific Engagement**
   - Product cancellation rates vary by segment (5% high-value → 40% at-risk)
   - Reflects different levels of product disengagement across customer segments

5. **Channel-Segment Homophily**
   - Acquisition channels naturally bias toward different segments
   - CAC reflects channel-segment pairing

6. **Pro-Rated Registration Month (M0)**
   - Customers who register late in the month have fewer days in M0
   - Prevents artificial boost in M0 activity for late registrants

7. **Right-Censoring for Churn**
   - Customers whose drawn churn date exceeds observable tenure appear active throughout
   - Enables realistic survival analysis downstream

---

## Validation

All generated data is validated via `validate_base_tables_consistency()`:
- Every transaction's product_type belongs to an active product for that customer
- Every transaction's customer_id and product_type pair is in the customer_products bridge table
- Segment-level activity rates match generation assumptions

Additionally, the realism of transaction composition can be verified:
- `investment`, `insurance`, `loan` should have zero `purchase` and `cash_withdrawal` rows
- `wallet` and `credit_card` should dominate (~91%) of total transaction volume
- `at_risk_churner` product cancellation rate should be visibly higher (~40%) than `high_value_active` (~5%)
