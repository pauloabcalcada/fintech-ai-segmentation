"""Faker-based generation of raw SynaptiqPay tables.

This module is responsible ONLY for creating base tables that mimic a real
data warehouse:

- customers_raw
- transactions_raw
- products_raw
- customer_products_raw

All analytical columns (RFM scores, LTV, churn probability, cohort metrics,
etc.) must be computed later in notebooks / ETL code from these raw tables.
"""

from __future__ import annotations

import re
import unicodedata
import uuid
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from faker import Faker

from .base_tables import (
    CustomerProductRaw,
    CustomerRaw,
    ProductRaw,
    SegmentLabel,
    TransactionRaw,
)


RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
fake = Faker("pt_BR")
Faker.seed(RANDOM_SEED)


TODAY = datetime(2026, 3, 1)

# Mid-stage fintech: customer history extends ~4 years back so that the
# observation window (Apr 2024 – Mar 2026) begins with an already-mature
# portfolio rather than starting near zero.
REGISTRATION_START = datetime(2022, 1, 1)
MAX_HISTORY_MONTHS = 50  # approx months from REGISTRATION_START to TODAY

SEGMENT_DISTRIBUTION: Dict[SegmentLabel, int] = {
    "high_value_active": 1_600,
    "mid_value_regular": 2_400,
    "low_value_dormant": 2_400,
    "at_risk_churner": 1_600,
}

ACQUISITION_CHANNELS = ["paid_ads", "organic", "referral", "partnership"]
EMAIL_DOMAINS = ["gmail.com", "outlook.com", "hotmail.com", "yahoo.com.br"]

# Cost-per-acquisition profile per channel (R$).
CHANNEL_CAC_PROFILES: Dict[str, Dict[str, float]] = {
    "organic":     {"mean": 25.0,  "std": 10.0},
    "referral":    {"mean": 55.0,  "std": 15.0},
    "partnership": {"mean": 110.0, "std": 25.0},
    "paid_ads":    {"mean": 230.0, "std": 50.0},
}

# P(segment | channel) — channels naturally attract different segment profiles.
# Order: [high_value_active, mid_value_regular, low_value_dormant, at_risk_churner]
CHANNEL_SEGMENT_BIAS: Dict[str, List[float]] = {
    "organic":     [0.15, 0.35, 0.30, 0.20],
    "referral":    [0.45, 0.35, 0.15, 0.05],
    "partnership": [0.20, 0.40, 0.25, 0.15],
    "paid_ads":    [0.10, 0.20, 0.30, 0.40],
}

# Derive P(channel | segment) via Bayes with uniform channel priors.
# Rows are channels (ACQUISITION_CHANNELS order), cols are segments
# (SEGMENT_DISTRIBUTION order).
_bias_matrix = np.array([CHANNEL_SEGMENT_BIAS[ch] for ch in ACQUISITION_CHANNELS])
_channel_probs_by_segment = (_bias_matrix / _bias_matrix.sum(axis=0, keepdims=True)).T
# Shape: (n_segments, n_channels) — one row per segment, probabilities over channels.
_SEGMENT_ORDER = ["high_value_active", "mid_value_regular", "low_value_dormant", "at_risk_churner"]
CHANNEL_PROBS_BY_SEGMENT: Dict[str, List[float]] = {
    seg: _channel_probs_by_segment[i].tolist()
    for i, seg in enumerate(_SEGMENT_ORDER)
}

# Monthly transaction-volume multiplier (Brazilian calendar).
# Captures the 13th-salary bonus (Nov/Dec), Black Friday (Nov),
# Carnival lull (Feb), and the post-holiday drop (Jan).
MONTHLY_SEASONALITY_FACTOR: Dict[int, float] = {
    1:  0.80,   # January  — post-holiday financial hangover
    2:  0.85,   # February — Carnival (spending shifts, not increases)
    3:  0.95,
    4:  0.95,
    5:  1.05,   # May      — Mother's Day (2nd Sunday)
    6:  1.05,   # June     — mid-year 13th-salary advance starts
    7:  0.95,   # July     — winter school holidays
    8:  0.95,
    9:  1.00,
    10: 1.05,   # October  — Children's Day (Oct 12)
    11: 1.20,   # November — Black Friday + 13th-salary 1st installment
    12: 1.30,   # December — Christmas + 13th-salary 2nd installment
}

# How strongly each segment's activity responds to seasonal peaks.
# Applied as: effective_factor = 1 + (base_factor - 1) * sensitivity
# so a sensitivity of 0 means no seasonal effect at all.
SEASONAL_SENSITIVITY: Dict[str, float] = {
    "high_value_active": 1.00,  # full effect — engaged, discretionary spenders
    "mid_value_regular": 0.70,  # moderate response
    "low_value_dormant": 0.30,  # barely moves regardless of season
    "at_risk_churner":   0.20,  # disengaged — seasonality won't wake them up
}

STATE_PROBS: Dict[str, float] = {
    "SP": 0.30,
    "RJ": 0.12,
    "MG": 0.10,
    "ES": 0.02,
    "BA": 0.06,
    "PE": 0.04,
    "CE": 0.04,
    "PR": 0.06,
    "RS": 0.05,
    "SC": 0.04,
    "DF": 0.03,
    "GO": 0.03,
    "PA": 0.02,
    "AM": 0.02,
    "MA": 0.02,
    "PB": 0.01,
    "RN": 0.01,
    "PI": 0.01,
    "AL": 0.01,
    "SE": 0.01,
    "MT": 0.01,
    "MS": 0.01,
    "RO": 0.006,
    "TO": 0.006,
    "AC": 0.003,
    "AP": 0.003,
    "RR": 0.003,
}


def _random_registration_date() -> datetime:
    """Sample a registration date following a Gamma(2, 360) acquisition curve.

    Gamma(shape=2, scale=360 days) naturally models a startup's acquisition life-cycle:
      - Ramps from zero in Jan 2022 (company just launched).
      - Peaks around month 12 (Jan 2023) — the hyper-growth phase.
      - Declines gradually but stays visible all the way to Feb 2026
        (~50-60 customers/month in the tail, not near-zero).

    This avoids the Beta tail-collapse problem (Beta(2,4) → ~1 customer in
    the last month) while keeping ~65 % of customers registered before
    Jan 2024, giving the observation window a stable legacy baseline.
    """
    total_days = (TODAY - REGISTRATION_START).days
    for _ in range(500):
        days_offset = int(np.random.gamma(shape=2.0, scale=360.0))
        if 0 <= days_offset < total_days:
            return REGISTRATION_START + timedelta(days=days_offset)
    # Fallback: uniform (triggered only if Gamma tail overshoots repeatedly).
    return REGISTRATION_START + timedelta(days=int(np.random.randint(0, total_days)))


def _choice_with_probs(options: Iterable[str], probs: Iterable[float]) -> str:
    return str(np.random.choice(list(options), p=list(probs)))


def _sample_state() -> str:
    states = list(STATE_PROBS.keys())
    probs = np.array(list(STATE_PROBS.values()), dtype=float)
    probs = probs / probs.sum()
    return str(np.random.choice(states, p=probs))


# Tier-1 (high-activity) states for economic effects
_TIER_1_STATES = {"SP", "RJ", "MG"}

# Segment-specific age parameters for mild demographic correlation.
# Updated 2026-04-10: Younger skew toward high-value (digital native), older toward dormant.
_AGE_PARAMS_BY_SEGMENT: Dict[str, Dict[str, float]] = {
    "high_value_active": {"loc": 38, "scale": 9},   # slightly older, more affluent
    "mid_value_regular": {"loc": 33, "scale": 10},  # younger professional
    "low_value_dormant": {"loc": 42, "scale": 12},  # broader range
    "at_risk_churner":   {"loc": 27, "scale": 8},   # youngest, less committed
}


def _normalize_email_token(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", ".", normalized)
    normalized = re.sub(r"\.+", ".", normalized).strip(".")
    return normalized or "cliente"


def _generate_unique_identity(used_names: set[str], used_emails: set[str]) -> Tuple[str, str]:
    for _ in range(200):
        full_name = " ".join(fake.name().split())
        if full_name in used_names:
            continue

        parts = [part for part in full_name.split(" ") if part]
        first_name = parts[0] if parts else "cliente"
        last_name = parts[-1] if len(parts) > 1 else "cliente"
        email_local = f"{_normalize_email_token(first_name)}.{_normalize_email_token(last_name)}"
        email_domain = str(np.random.choice(EMAIL_DOMAINS))
        email = f"{email_local}@{email_domain}"

        if email in used_emails:
            suffix = np.random.randint(10, 9999)
            email = f"{email_local}{suffix}@{email_domain}"

        if email in used_emails:
            continue

        used_names.add(full_name)
        used_emails.add(email)
        return full_name, email

    # Fallback for very high collision scenarios.
    fallback_idx = len(used_names) + 1
    full_name = f"Cliente {fallback_idx}"
    email = f"cliente.{fallback_idx}@synaptiqpay.com.br"
    used_names.add(full_name)
    used_emails.add(email)
    return full_name, email


def generate_customers_raw() -> pd.DataFrame:
    """Generate the `customers_raw` table.

    Only static / registration-time attributes are created here.
    """

    rows: List[CustomerRaw] = []
    used_names: set[str] = set()
    used_emails: set[str] = set()

    for segment_label, segment_size in SEGMENT_DISTRIBUTION.items():
        for _ in range(segment_size):
            age_params = _AGE_PARAMS_BY_SEGMENT.get(segment_label, {"loc": 35, "scale": 10})
            age = int(np.random.normal(loc=age_params["loc"], scale=age_params["scale"]))
            age = int(np.clip(age, 18, 80))

            state = _sample_state()
            registration_date = _random_registration_date()

            acq_channel = _choice_with_probs(
                ACQUISITION_CHANNELS,
                probs=CHANNEL_PROBS_BY_SEGMENT[segment_label],
            )
            cac_profile = CHANNEL_CAC_PROFILES[acq_channel]
            acquisition_cost = float(
                max(np.random.normal(cac_profile["mean"], cac_profile["std"]), 10.0)
            )
            name, email = _generate_unique_identity(used_names, used_emails)

            rows.append(
                CustomerRaw(
                    customer_id=str(uuid.uuid4()),
                    name=name,
                    email=email,
                    age=age,
                    state=state,
                    registration_date=registration_date,
                    acquisition_channel=acq_channel,  # type: ignore[arg-type]
                    acquisition_cost=acquisition_cost,
                    true_segment=segment_label,
                )
            )

    df = pd.DataFrame([row.__dict__ for row in rows])
    return df


def _segment_transaction_profile(segment: SegmentLabel) -> Tuple[float, float, float]:
    """Return (avg_tx_per_active_month, avg_ticket, p_active_per_month) for a segment.

    ``p_active_per_month`` is the probability that a customer in this segment
    transacts *at all* in any given calendar month of their tenure.  This drives
    realistic inactivity gaps rather than scattering transactions uniformly across
    every month (which inflated cohort M0-M6 active rates).

    Segment profiles:
    - high_value_active : very likely to transact every month, high frequency
    - mid_value_regular : likely every month, moderate frequency
    - low_value_dormant : often skips months, low frequency when active
    - at_risk_churner   : rarely active, even lower frequency, lower ticket to differentiate from dormant

    Updated 2026-04-10: Widened behavioral gap between low_value_dormant and at_risk_churner
    to enable K-Means to recover k=4 clusters instead of collapsing to k=3.
    """

    if segment == "high_value_active":
        return 40.0, 220.0, 0.95
    if segment == "mid_value_regular":
        return 18.0, 160.0, 0.85
    if segment == "low_value_dormant":
        return 4.0, 100.0, 0.40  # avg_ticket: 90 → 100 (increased to distance from churner)
    # at_risk_churner
    return 2.0, 45.0, 0.15  # avg_tx: 3→2, avg_ticket: 70→45, p_active: 0.25→0.15


# Monthly churn hazard rate per segment.
# Each month the customer "survives" with probability (1 - hazard).
# The number of full M1+ months before permanent churn is
# Geometric(hazard) - 1  (0-indexed: 0 means churn after M0, no M1+ activity).
# Customers whose drawn churn month exceeds their observable tenure are
# right-censored — they appear active for the whole window.
#
# Calibration targets (fraction churning within 12 months):
#   high_value_active  ~ 11 %   → hazard = 0.010
#   mid_value_regular  ~ 38 %   → hazard = 0.040
#   low_value_dormant  ~ 62 %   → hazard = 0.080
#   at_risk_churner    ~ 90 %   → hazard = 0.180
#
# mid_value is intentionally more aggressive than the default "loyal" assumption
# so that the aggregate TPV curve visibly bends after ~12 months and the M1→M6
# retention decline is meaningful (~15-20 pp) rather than flat.
_CHURN_HAZARD: Dict[str, float] = {
    "high_value_active": 0.010,
    "mid_value_regular": 0.040,
    "low_value_dormant": 0.080,
    "at_risk_churner":   0.180,
}

_PRODUCT_CANCELLATION_RATE_BY_SEGMENT: Dict[str, float] = {
    "high_value_active": 0.05,
    "mid_value_regular": 0.12,
    "low_value_dormant": 0.25,
    "at_risk_churner":   0.40,
}

# Channel order: in_app, card_present, online, atm — sums must be 1.0 per product.
_TX_CHANNELS: Tuple[str, ...] = ("in_app", "card_present", "online", "atm")
_CHANNEL_PROBS_BY_PRODUCT_TYPE: Dict[str, Tuple[float, float, float, float]] = {
    # Wallet: app + ATM cash-like usage (via debit card).
    "wallet": (0.55, 0.08, 0.32, 0.05),
    # Card product: physical + e-commerce.
    "credit_card": (0.12, 0.38, 0.45, 0.05),
    # Investment: digital only (no physical card, no ATM access).
    "investment": (0.50, 0.00, 0.50, 0.00),
    # Insurance: digital only (no physical card, no ATM access).
    "insurance": (0.54, 0.00, 0.46, 0.00),
    # Loan: digital only (disbursements via in-app/online, not ATM/card-present).
    "loan": (0.50, 0.00, 0.50, 0.00),
}

# Product-type-specific amount distribution parameters.
# Each product has a mean_scale (multiplier on segment avg_ticket) and std_scale
# (coefficient of variation on the final amount).
# Updated 2026-04-10 to add realism to transaction composition.
_PRODUCT_AMOUNT_PARAMS: Dict[str, Dict[str, float]] = {
    "wallet":      {"mean_scale": 0.30, "std_scale": 0.25, "min": 5.0},      # R$30–80 typical
    "credit_card": {"mean_scale": 1.00, "std_scale": 0.40, "min": 15.0},     # segment avg_ticket
    "investment":  {"mean_scale": 6.00, "std_scale": 2.50, "min": 100.0},    # large deposits
    "insurance":   {"mean_scale": 0.60, "std_scale": 0.15, "min": 30.0},     # fixed premium-like
    "loan":        {"mean_scale": 8.00, "std_scale": 2.00, "min": 200.0},    # large, periodic
}

# Relative weights for sampling which product a customer transacts on.
# Daily-use products dominate; investment/insurance/loan are infrequent.
_PRODUCT_SELECTION_WEIGHT: Dict[str, float] = {
    "wallet":      3.0,
    "credit_card": 3.0,
    "investment":  0.5,
    "insurance":   0.3,
    "loan":        0.2,
}

# Transaction-type order: [purchase, transfer, cash_withdrawal, fee, refund]
# Keyed by product_type so that transaction types are realistic per instrument.
_TX_TYPES: Tuple[str, ...] = ("purchase", "transfer", "cash_withdrawal", "fee", "refund")
_TX_TYPE_PROBS_BY_PRODUCT_TYPE: Dict[str, Tuple[float, float, float, float, float]] = {
    "wallet":      (0.55, 0.30, 0.08, 0.04, 0.03),  # spending, P2P, ATM cash
    "credit_card": (0.70, 0.00, 0.05, 0.15, 0.10),  # purchases, cash advance, fee, refund
    "investment":  (0.00, 0.75, 0.00, 0.25, 0.00),  # deposits/withdrawals, management fees
    "insurance":   (0.00, 0.10, 0.00, 0.75, 0.15),  # premium fees, claim refunds
    "loan":        (0.00, 0.70, 0.00, 0.30, 0.00),  # disbursements/repayments, fees
}


def _active_product_types_by_customer(
    customer_products_raw: pd.DataFrame,
    products_raw: pd.DataFrame,
) -> Dict[str, List[str]]:
    """Map each customer_id to distinct product types from *active* bridge rows."""

    if customer_products_raw.empty:
        return {}

    merged = customer_products_raw.merge(
        products_raw[["product_id", "product_type"]],
        on="product_id",
        how="left",
    )
    active = merged.loc[merged["is_active"] == True]  # noqa: E712
    out: Dict[str, List[str]] = {}
    for cid, group in active.groupby("customer_id"):
        types = sorted({str(t) for t in group["product_type"].dropna().unique()})
        out[str(cid)] = types
    return out


def _product_types_for_transactions(
    customer_id: str,
    active_by_customer: Dict[str, List[str]],
) -> List[str]:
    """Product types to sample from; fallback to wallet when there are no active products."""

    owned = active_by_customer.get(str(customer_id), [])
    if owned:
        return owned
    return ["wallet"]


def _sample_channel_for_product_type(product_type: str) -> str:
    probs = _CHANNEL_PROBS_BY_PRODUCT_TYPE.get(
        product_type,
        _CHANNEL_PROBS_BY_PRODUCT_TYPE["wallet"],
    )
    return str(np.random.choice(_TX_CHANNELS, p=list(probs)))


def _sample_tx_type_for_product(product_type: str) -> str:
    probs = _TX_TYPE_PROBS_BY_PRODUCT_TYPE.get(
        product_type,
        _TX_TYPE_PROBS_BY_PRODUCT_TYPE["wallet"],
    )
    return str(np.random.choice(_TX_TYPES, p=list(probs)))


def _sample_transaction_amount(product_type: str, segment_avg_ticket: float) -> float:
    """Sample transaction amount conditioned on product type and segment.

    Product types have different realistic amount distributions:
    - Wallet: small frequent transfers (30% of segment avg)
    - Credit card: baseline (100% of segment avg)
    - Investment: large deposits (6x segment avg)
    - Insurance: fixed premiums (60% of segment avg)
    - Loan: large periodic drawdowns (8x segment avg)
    """
    params = _PRODUCT_AMOUNT_PARAMS.get(
        product_type,
        _PRODUCT_AMOUNT_PARAMS["wallet"],
    )
    mean_scale = params["mean_scale"]
    std_scale = params["std_scale"]
    min_amount = params["min"]

    product_amount_mean = segment_avg_ticket * mean_scale
    product_amount_std = product_amount_mean * std_scale
    amount = float(np.random.normal(product_amount_mean, product_amount_std))
    return float(max(amount, min_amount))


def _month_start(dt: datetime) -> datetime:
    """Return the first day of the month containing ``dt`` at midnight."""
    return datetime(dt.year, dt.month, 1)


def _add_months(dt: datetime, n: int) -> datetime:
    """Add ``n`` calendar months to a month-start datetime."""
    month = dt.month - 1 + n
    year = dt.year + month // 12
    month = month % 12 + 1
    return datetime(year, month, 1)


def generate_transactions_raw(
    customers_raw: pd.DataFrame,
    customer_products_raw: pd.DataFrame,
    products_raw: pd.DataFrame,
) -> pd.DataFrame:
    """Generate the `transactions_raw` table for all customers.

    Generation model (month-by-month with dropout):
    ─────────────────────────────────────────────────
    For each customer we iterate over calendar months from M0 (the
    registration month) through the last complete month before TODAY.

    M0 is a **partial month**: the window is [registration_date, end of
    registration month).  Both ``p_active`` and ``avg_tx`` are pro-rated by
    the fraction of the month remaining after registration so that a customer
    who registers on the 1st gets a nearly full M0 while one who registers
    on the 28th gets a very short window — consistent with the product-start
    dates already recorded in ``customer_products_raw``.

    M1 onward are full calendar months.

    Within each window the customer is active:
    1. Draw ``active`` ~ Bernoulli(p_active_per_month × day_fraction | segment).
    2. If active, draw ``n`` ~ Poisson(avg_tx_per_active_month × day_fraction).
    3. For each of the ``n`` transactions, place it on a random day (and time)
       within the available window.

    ``p_active_per_month`` encodes realistic inactivity gaps per segment
    instead of relying on Beta-distributed scattering to approximate them.

    Churn behaviour for ``at_risk_churner`` and ``low_value_dormant`` is
    reinforced by an additional per-month decay so that recent months have
    lower expected activity for these segments.

    Each row's ``product_type`` is sampled from that customer's **active**
    products in ``customer_products_raw`` (joined to ``products_raw``).
    Channel is sampled conditional on ``product_type``.
    """

    active_by_customer = _active_product_types_by_customer(
        customer_products_raw,
        products_raw,
    )

    # Last complete calendar month we can observe (exclusive upper bound).
    last_complete_month = _month_start(TODAY)

    tx_rows: List[TransactionRaw] = []

    for _, customer in customers_raw.iterrows():
        segment: SegmentLabel = customer["true_segment"]
        registration_date: datetime = customer["registration_date"]
        customer_id = str(customer["customer_id"])
        product_pool = _product_types_for_transactions(customer_id, active_by_customer)
        _raw_weights = np.array(
            [_PRODUCT_SELECTION_WEIGHT.get(pt, 1.0) for pt in product_pool], dtype=float
        )
        product_pool_weights = _raw_weights / _raw_weights.sum()

        avg_tx_per_active_month, avg_ticket, p_active_base = _segment_transaction_profile(segment)

        # ── M0: partial month [registration_date, end of registration month) ──
        reg_month_start = _month_start(registration_date)
        next_month_start = _add_months(reg_month_start, 1)

        days_in_reg_month = (next_month_start - reg_month_start).days
        days_remaining_m0 = (next_month_start - registration_date).days
        day_fraction_m0 = days_remaining_m0 / days_in_reg_month

        # M1 is the first full calendar month; M0 uses index -1 (before the main loop).
        # For decay purposes M0 counts as the earliest possible slot (index 0 in decay).

        # Seasonal multiplier for M0 (based on the registration calendar month).
        _m0_base_factor = MONTHLY_SEASONALITY_FACTOR[reg_month_start.month]
        _m0_sensitivity = SEASONAL_SENSITIVITY[segment]
        _m0_seasonal = 1.0 + (_m0_base_factor - 1.0) * _m0_sensitivity

        if segment == "at_risk_churner":
            p_active_m0 = min(p_active_base * day_fraction_m0 * (1.0 + (_m0_base_factor - 1.0) * _m0_sensitivity * 0.5), p_active_base)
        elif segment == "low_value_dormant":
            p_active_m0 = min(p_active_base * day_fraction_m0 * (1.0 + (_m0_base_factor - 1.0) * _m0_sensitivity * 0.5), p_active_base)
        else:
            p_active_m0 = min(p_active_base * day_fraction_m0 * (1.0 + (_m0_base_factor - 1.0) * _m0_sensitivity * 0.5), 0.99)

        if next_month_start <= last_complete_month and np.random.rand() <= p_active_m0:
            n_tx_m0 = int(np.random.poisson(max(avg_tx_per_active_month * day_fraction_m0 * _m0_seasonal, 0.5)))
            for _ in range(n_tx_m0):
                day_offset = np.random.randint(0, max(days_remaining_m0, 1))
                hour = np.random.randint(0, 24)
                minute = np.random.randint(0, 60)
                tx_dt = registration_date + timedelta(days=int(day_offset), hours=hour, minutes=minute)
                tx_dt = min(tx_dt, TODAY)
                product_type = str(np.random.choice(product_pool, p=product_pool_weights))
                amount = _sample_transaction_amount(product_type, avg_ticket)
                tx_type = _sample_tx_type_for_product(product_type)
                channel = _sample_channel_for_product_type(product_type)
                status = np.random.choice(
                    ["completed", "pending", "failed", "reversed"],
                    p=[0.93, 0.03, 0.02, 0.02],
                )
                tx_rows.append(
                    TransactionRaw(
                        transaction_id=str(uuid.uuid4()),
                        customer_id=customer_id,
                        transaction_datetime=tx_dt,
                        amount=amount,
                        transaction_type=tx_type,  # type: ignore[arg-type]
                        product_type=product_type,  # type: ignore[arg-type]
                        channel=channel,  # type: ignore[arg-type]
                        status=status,  # type: ignore[arg-type]
                    )
                )

        # ── M1 onward: full calendar months ──────────────────────────────────
        months: List[datetime] = []
        m = next_month_start
        while m < last_complete_month:
            months.append(m)
            m = _add_months(m, 1)

        if not months:
            continue

        tenure_len = len(months)

        # Draw the customer's permanent churn point.
        # churn_after_n_months = k means the customer is active during M1..Mk
        # and permanently gone from M(k+1) onward.  Drawing from Geometric(p)
        # and subtracting 1 gives the 0-indexed last active M1+ month.
        # A value >= tenure_len means the customer does not churn within the
        # observable window (right-censored).
        hazard = _CHURN_HAZARD[segment]
        churn_after_n_months: int = int(np.random.geometric(hazard)) - 1

        for month_idx, month_start_dt in enumerate(months):
            # Permanently churned customers stop transacting.
            if month_idx > churn_after_n_months:
                break

            # Seasonal factor for this calendar month.
            _base_factor = MONTHLY_SEASONALITY_FACTOR[month_start_dt.month]
            _sensitivity = SEASONAL_SENSITIVITY[segment]
            _seasonal = 1.0 + (_base_factor - 1.0) * _sensitivity
            _seasonal_p = 1.0 + (_base_factor - 1.0) * _sensitivity * 0.5

            # Decay p_active for churn-prone segments, then apply seasonal nudge.
            if segment == "at_risk_churner":
                decay = np.exp(-0.25 * month_idx)
                p_active = min((p_active_base * decay + 0.05) * _seasonal_p, p_active_base)
            elif segment == "low_value_dormant":
                decay = np.exp(-0.05 * month_idx)
                p_active = min((p_active_base * decay + 0.10) * _seasonal_p, p_active_base)
            else:
                recency_boost = 0.02 * (month_idx / max(tenure_len - 1, 1))
                p_active = min((p_active_base + recency_boost) * _seasonal_p, 0.99)

            if np.random.rand() > p_active:
                continue

            n_tx = int(np.random.poisson(avg_tx_per_active_month * _seasonal))
            if n_tx == 0:
                continue

            next_month = _add_months(month_start_dt, 1)
            days_in_month = (next_month - month_start_dt).days

            for _ in range(n_tx):
                day_offset = np.random.randint(0, days_in_month)
                hour = np.random.randint(0, 24)
                minute = np.random.randint(0, 60)
                tx_dt = month_start_dt + timedelta(days=int(day_offset), hours=hour, minutes=minute)
                tx_dt = min(tx_dt, TODAY)

                product_type = str(np.random.choice(product_pool, p=product_pool_weights))
                amount = _sample_transaction_amount(product_type, avg_ticket)
                tx_type = _sample_tx_type_for_product(product_type)
                channel = _sample_channel_for_product_type(product_type)
                status = np.random.choice(
                    ["completed", "pending", "failed", "reversed"],
                    p=[0.93, 0.03, 0.02, 0.02],
                )

                tx_rows.append(
                    TransactionRaw(
                        transaction_id=str(uuid.uuid4()),
                        customer_id=customer_id,
                        transaction_datetime=tx_dt,
                        amount=amount,
                        transaction_type=tx_type,  # type: ignore[arg-type]
                        product_type=product_type,  # type: ignore[arg-type]
                        channel=channel,  # type: ignore[arg-type]
                        status=status,  # type: ignore[arg-type]
                    )
                )

    df = pd.DataFrame([row.__dict__ for row in tx_rows])
    return df


def generate_products_raw() -> pd.DataFrame:
    """Generate a small static product catalog."""

    products: List[ProductRaw] = [
        ProductRaw(str(uuid.uuid4()), "Digital Wallet", "wallet"),
        ProductRaw(str(uuid.uuid4()), "SynaptiqPay Credit Card", "credit_card"),
        ProductRaw(str(uuid.uuid4()), "Investment Account", "investment"),
        ProductRaw(str(uuid.uuid4()), "Device Insurance", "insurance"),
        ProductRaw(str(uuid.uuid4()), "Personal Loan", "loan"),
    ]
    return pd.DataFrame([p.__dict__ for p in products])


def generate_customer_products_raw(
    customers_raw: pd.DataFrame,
    products_raw: pd.DataFrame,
) -> pd.DataFrame:
    """Generate the `customer_products_raw` bridge table."""

    rows: List[CustomerProductRaw] = []

    # Map product type to ID for easier sampling.
    products_by_type: Dict[str, str] = {
        row["product_type"]: row["product_id"] for _, row in products_raw.iterrows()
    }

    for _, customer in customers_raw.iterrows():
        segment: SegmentLabel = customer["true_segment"]
        registration_date: datetime = customer["registration_date"]

        # Segment-based probabilities of owning each product type.
        if segment == "high_value_active":
            probs = {"wallet": 0.98, "credit_card": 0.92, "investment": 0.65, "insurance": 0.45, "loan": 0.35}
        elif segment == "mid_value_regular":
            probs = {"wallet": 0.95, "credit_card": 0.85, "investment": 0.35, "insurance": 0.30, "loan": 0.30}
        elif segment == "low_value_dormant":
            probs = {"wallet": 0.90, "credit_card": 0.60, "investment": 0.15, "insurance": 0.20, "loan": 0.20}
        else:  # at_risk_churner
            # High loan rate = financial stress signal; investment low = no savings buffer.
            probs = {"wallet": 0.85, "credit_card": 0.50, "investment": 0.10, "insurance": 0.15, "loan": 0.25}

        for product_type, prob in probs.items():
            if np.random.rand() < prob:
                product_id = products_by_type[product_type]
                # Random start date between registration and today.
                days_since_reg = max((TODAY - registration_date).days, 1)
                start_offset = np.random.randint(0, days_since_reg)
                start_date = registration_date + timedelta(days=int(start_offset))

                # Some products may have been cancelled (rate varies by segment).
                cancel_rate = _PRODUCT_CANCELLATION_RATE_BY_SEGMENT.get(segment, 0.15)
                is_active = bool(np.random.rand() > cancel_rate)

                rows.append(
                    CustomerProductRaw(
                        customer_id=customer["customer_id"],
                        product_id=product_id,
                        start_date=start_date,
                        is_active=is_active,
                    )
                )

    df = pd.DataFrame([row.__dict__ for row in rows])
    return df


def validate_base_tables_consistency(
    transactions_raw: pd.DataFrame,
    customer_products_raw: pd.DataFrame,
    products_raw: pd.DataFrame,
) -> None:
    """Raise ``AssertionError`` if transactions reference unknown or disallowed product types.

    Each transaction's ``product_type`` must appear in ``products_raw``. It must also
    be among the customer's **active** product types; if the customer has no active
    products, only ``wallet`` is allowed (matching the generator fallback).
    """

    catalog = set(products_raw["product_type"].astype(str).unique())
    if not transactions_raw.empty:
        tx_types = set(transactions_raw["product_type"].astype(str).unique())
        assert tx_types.issubset(catalog), (
            f"transactions_raw has product_type values not in catalog: {tx_types - catalog}"
        )

    active_by_customer = _active_product_types_by_customer(
        customer_products_raw,
        products_raw,
    )

    for customer_id, sub in transactions_raw.groupby("customer_id"):
        cid = str(customer_id)
        allowed = set(active_by_customer.get(cid, []))
        if not allowed:
            allowed = {"wallet"}
        bad_mask = ~sub["product_type"].astype(str).isin(allowed)
        assert not bool(bad_mask.any()), (
            f"customer {cid}: transaction product_type not in allowed set {allowed}"
        )


def generate_all_base_tables() -> Dict[str, pd.DataFrame]:
    """Convenience function: generate all raw tables as a dict of DataFrames."""

    customers_raw = generate_customers_raw()
    products_raw = generate_products_raw()
    customer_products_raw = generate_customer_products_raw(customers_raw, products_raw)
    transactions_raw = generate_transactions_raw(
        customers_raw,
        customer_products_raw,
        products_raw,
    )
    validate_base_tables_consistency(
        transactions_raw,
        customer_products_raw,
        products_raw,
    )

    return {
        "customers_raw": customers_raw,
        "transactions_raw": transactions_raw,
        "products_raw": products_raw,
        "customer_products_raw": customer_products_raw,
    }


__all__ = [
    "generate_customers_raw",
    "generate_transactions_raw",
    "generate_products_raw",
    "generate_customer_products_raw",
    "generate_all_base_tables",
    "validate_base_tables_consistency",
]
