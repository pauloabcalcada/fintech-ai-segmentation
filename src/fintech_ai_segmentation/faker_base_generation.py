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
    "high_value_active": 2_000,
    "mid_value_regular": 3_000,
    "low_value_dormant": 3_000,
    "at_risk_churner": 2_000,
}

ACQUISITION_CHANNELS = ["paid_ads", "organic", "referral", "partnership"]


def _random_registration_date() -> datetime:
    """Sample a registration date within the last 24 months."""

    days_offset = np.random.randint(0, (TODAY - REGISTRATION_START).days + 1)
    return REGISTRATION_START + timedelta(days=int(days_offset))


def _choice_with_probs(options: Iterable[str], probs: Iterable[float]) -> str:
    return str(np.random.choice(list(options), p=list(probs)))


def generate_customers_raw() -> pd.DataFrame:
    """Generate the `customers_raw` table.

    Only static / registration-time attributes are created here.
    """

    rows: List[CustomerRaw] = []

    for segment_label, segment_size in SEGMENT_DISTRIBUTION.items():
        for _ in range(segment_size):
            age = int(np.random.normal(loc=35, scale=10))
            age = int(np.clip(age, 18, 80))

            state = fake.estado_sigla()
            registration_date = _random_registration_date()

            if segment_label == "high_value_active":
                acq_channel = _choice_with_probs(
                    ACQUISITION_CHANNELS,
                    probs=[0.30, 0.20, 0.30, 0.20],
                )
                acquisition_cost = float(np.random.normal(180, 40))
            elif segment_label == "mid_value_regular":
                acq_channel = _choice_with_probs(
                    ACQUISITION_CHANNELS,
                    probs=[0.25, 0.30, 0.25, 0.20],
                )
                acquisition_cost = float(np.random.normal(150, 35))
            elif segment_label == "low_value_dormant":
                acq_channel = _choice_with_probs(
                    ACQUISITION_CHANNELS,
                    probs=[0.20, 0.40, 0.20, 0.20],
                )
                acquisition_cost = float(np.random.normal(110, 25))
            else:
                acq_channel = _choice_with_probs(
                    ACQUISITION_CHANNELS,
                    probs=[0.35, 0.15, 0.30, 0.20],
                )
                acquisition_cost = float(np.random.normal(190, 45))

            acquisition_cost = float(max(acquisition_cost, 20.0))

            rows.append(
                CustomerRaw(
                    customer_id=str(uuid.uuid4()),
                    name=fake.name(),
                    email=fake.email(),
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

