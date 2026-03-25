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
REGISTRATION_START = TODAY - timedelta(days=730)  # ~24 months
MAX_HISTORY_MONTHS = 24

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
    """Sample a registration date within the last 24 months."""

    days_offset = np.random.randint(0, (TODAY - REGISTRATION_START).days + 1)
    return REGISTRATION_START + timedelta(days=int(days_offset))


def _choice_with_probs(options: Iterable[str], probs: Iterable[float]) -> str:
    return str(np.random.choice(list(options), p=list(probs)))


def _sample_state() -> str:
    states = list(STATE_PROBS.keys())
    probs = np.array(list(STATE_PROBS.values()), dtype=float)
    probs = probs / probs.sum()
    return str(np.random.choice(states, p=probs))


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
            age = int(np.random.normal(loc=35, scale=10))
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


def _segment_transaction_profile(segment: SegmentLabel) -> Tuple[float, float]:
    """Return (avg_tx_per_month, avg_ticket) for a segment."""

    if segment == "high_value_active":
        return 40.0, 220.0
    if segment == "mid_value_regular":
        return 18.0, 160.0
    if segment == "low_value_dormant":
        return 4.0, 90.0
    return 1.5, 70.0


def generate_transactions_raw(customers_raw: pd.DataFrame) -> pd.DataFrame:
    """Generate the `transactions_raw` table for all customers.

    The planted `true_segment` drives:
    - average number of transactions per month
    - average ticket size
    - basic recency behavior (some segments more active recently than others)
    """

    tx_rows: List[TransactionRaw] = []

    for _, customer in customers_raw.iterrows():
        segment: SegmentLabel = customer["true_segment"]
        registration_date: datetime = customer["registration_date"]

        avg_tx_per_month, avg_ticket = _segment_transaction_profile(segment)

        # Number of months the customer could have been active.
        tenure_months = max(
            int((TODAY.year - registration_date.year) * 12 + (TODAY.month - registration_date.month)),
            1,
        )
        tenure_months = int(min(tenure_months, MAX_HISTORY_MONTHS))

        # Draw actual number of transactions with Poisson noise.
        expected_txs = max(avg_tx_per_month * tenure_months, 0.5)
        n_transactions = np.random.poisson(expected_txs)
        n_transactions = int(max(n_transactions, 0))

        if n_transactions == 0:
            continue

        # Older / at-risk segments should concentrate more activity in the past.
        for _ in range(n_transactions):
            months_offset = np.random.uniform(0, tenure_months)

            if segment == "at_risk_churner":
                months_offset = np.random.beta(0.6, 2.5) * tenure_months
            elif segment == "low_value_dormant":
                months_offset = np.random.beta(0.8, 2.0) * tenure_months
            else:
                months_offset = np.random.beta(2.0, 1.0) * tenure_months

            tx_month = registration_date + timedelta(days=30 * months_offset)
            tx_month = min(tx_month, TODAY)

            amount = float(max(np.random.normal(avg_ticket, avg_ticket * 0.4), 5.0))

            tx_type = np.random.choice(
                ["purchase", "transfer", "cash_withdrawal", "fee", "refund"],
                p=[0.65, 0.15, 0.10, 0.07, 0.03],
            )
            channel = np.random.choice(
                ["in_app", "card_present", "online", "atm"],
                p=[0.55, 0.20, 0.20, 0.05],
            )
            # Simple mapping from channel to product_type to tie behavior
            # back to the product catalog. This can be refined later.
            if channel in ("card_present", "online"):
                product_type = "credit_card"
            elif channel == "atm":
                product_type = "wallet"
            else:  # in_app
                product_type = "wallet"
            status = np.random.choice(
                ["completed", "pending", "failed", "reversed"],
                p=[0.93, 0.03, 0.02, 0.02],
            )

            tx_rows.append(
                TransactionRaw(
                    transaction_id=str(uuid.uuid4()),
                    customer_id=customer["customer_id"],
                    transaction_datetime=tx_month,
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
            probs = {"wallet": 0.85, "credit_card": 0.50, "investment": 0.10, "insurance": 0.15, "loan": 0.25}

        for product_type, prob in probs.items():
            if np.random.rand() < prob:
                product_id = products_by_type[product_type]
                # Random start date between registration and today.
                days_since_reg = max((TODAY - registration_date).days, 1)
                start_offset = np.random.randint(0, days_since_reg)
                start_date = registration_date + timedelta(days=int(start_offset))

                # Some products may have been cancelled.
                is_active = bool(np.random.rand() > 0.15)

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


def generate_all_base_tables() -> Dict[str, pd.DataFrame]:
    """Convenience function: generate all raw tables as a dict of DataFrames."""

    customers_raw = generate_customers_raw()
    products_raw = generate_products_raw()
    transactions_raw = generate_transactions_raw(customers_raw)
    customer_products_raw = generate_customer_products_raw(customers_raw, products_raw)

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
]
