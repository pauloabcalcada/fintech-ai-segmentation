"""Base table schemas for SynaptiqPay synthetic data.

These definitions separate **raw Faker-generated tables** from
**derived analytical tables** built later in the EDA pipeline.

Only the tables in this module are created directly by Faker.
All metrics like RFM, LTV, churn probability, and cohort retention
are computed downstream from these raw tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


SegmentLabel = Literal[
    "high_value_active",
    "mid_value_regular",
    "low_value_dormant",
    "at_risk_churner",
]


@dataclass(frozen=True)
class CustomerRaw:
    """
    One row per customer (static attributes + acquisition data).

    """

    customer_id: str          # UUID
    name: str
    email: str
    age: int
    state: str                # Brazilian state code (e.g. 'SP')
    registration_date: datetime
    acquisition_channel: Literal["paid_ads", "organic", "referral", "partnership"]
    acquisition_cost: float   # CAC (R$)

    # Ground-truth behavioral segment used only for evaluation.
    # Downstream clustering models should try to recover this.
    true_segment: SegmentLabel


@dataclass(frozen=True)
class TransactionRaw:
    """One row per financial transaction.

    This table captures the event-level behavior over time that will later be
    aggregated into customer-level features (RFM, balances, revenue, etc.).
    """

    transaction_id: str       # UUID
    customer_id: str          # FK -> customers_raw.customer_id
    transaction_datetime: datetime
    amount: float             # positive for debit/spend, negative for refunds, etc.
    transaction_type: Literal["purchase", "transfer", "cash_withdrawal", "fee", "refund"]
    product_type: Literal["wallet", "credit_card", "investment", "insurance", "loan"]
    channel: Literal["in_app", "card_present", "online", "atm"]
    status: Literal["completed", "pending", "failed", "reversed"]


@dataclass(frozen=True)
class ProductRaw:
    """Product catalog for SynaptiqPay."""

    product_id: str          # UUID
    product_name: str        # e.g. "Digital Wallet", "Credit Card"
    product_type: Literal["wallet", "credit_card", "investment", "insurance", "loan"]


@dataclass(frozen=True)
class CustomerProductRaw:
    """Bridge table: which customer owns which products and since when."""

    customer_id: str         # FK -> customers_raw.customer_id
    product_id: str          # FK -> products_raw.product_id
    start_date: datetime
    is_active: bool


__all__ = [
    "SegmentLabel",
    "CustomerRaw",
    "TransactionRaw",
    "ProductRaw",
    "CustomerProductRaw",
]

