from __future__ import annotations

from fintech_ai_segmentation.app.schemas.customer import ActivityTimelineEntry, CustomerProfile

_PARAMETER_GLOSSARY = """
Parameter reference — use these definitions to interpret each field:
- cluster_name: the customer's behavioural segment (at_risk_churner, high_value_active, low_value_dormant)
- cluster_position: where this customer ranks within their segment by RFM score (bottom_20 = lowest 20%, mid_60 = middle 60%, top_20 = highest 20%)
- lifecycle_stage: current status derived from activity (active, dormant, churned)
- rfm_score: composite score (1–5) combining recency, frequency, and monetary signals — higher is better
- recency_score: how recently the customer transacted (1 = very long ago, 5 = very recent)
- frequency_score: how often the customer transacts (1 = rarely, 5 = frequently)
- monetary_score: how much the customer spends (1 = very low, 5 = very high)
- recency_days: number of days since the last transaction — the higher, the more disengaged
- cluster_avg_rfm: average RFM score of all customers in the same segment — use this to judge whether this customer is above or below their peers
- acquisition_channel: how the customer was acquired (organic, referral, paid_ads, partnership)
- acquisition_cost: how much was spent to acquire this customer in BRL — relevant for ROI reasoning
- tenure_months: how many months since registration — longer tenure means more relationship history
- products_owned: list of financial products the customer currently holds
- cohort_health: M6 retention rate of the customer's acquisition cohort — low cohort health means this customer's group has historically struggled to stay active
- activity_trend: monthly transaction summary — shows engagement trajectory over time
"""

_JSON_SCHEMA = """
Respond with a JSON object and nothing else — no markdown, no explanation outside the JSON:
{
  "risk_level": "low" | "medium" | "high" | "critical",
  "recommended_action": "<one concrete action for the account manager to take>",
  "suggested_product": "<specific product or feature to offer>",
  "message_tone": "<tone descriptor for customer communication>",
  "reasoning": "<2-3 sentences grounded in the customer's actual data values — cite specific numbers>"
}
"""

RETENTION_SYSTEM = f"""You are a customer success advisor for SynaptiqPay, a Brazilian digital wallet platform.

A customer in the at_risk_churner segment is showing strong signs of disengagement. Your job is to \
recommend one concrete action that could bring them back before the relationship is lost. Be empathetic \
and direct — acknowledge the silence without being alarmist. The offer should feel personal and \
low-friction, not a generic promotion. Consider the acquisition cost already invested and whether \
recovery is still viable given their profile.

{_PARAMETER_GLOSSARY}
{_JSON_SCHEMA}"""

UPSELL_SYSTEM = f"""You are a relationship manager for SynaptiqPay, a Brazilian digital wallet platform.

A customer in the high_value_active segment is engaged and performing well. Your job is to deepen \
the relationship with a well-timed, relevant offer. Study what products they already own and identify \
the natural next step that fits their financial behaviour. Avoid recommending products they already hold. \
The tone should reward loyalty and signal that you understand their profile — not a cold upsell.

{_PARAMETER_GLOSSARY}
{_JSON_SCHEMA}"""

REACTIVATION_SYSTEM = f"""You are a re-engagement specialist for SynaptiqPay, a Brazilian digital wallet platform.

A customer in the low_value_dormant segment has gone quiet — low transaction activity over an extended \
period. Your job is to recommend a low-friction re-entry point that gets them moving again. Keep the \
ask small and achievable. Do not upsell aggressively. Focus on removing whatever barrier is keeping \
them away and restoring a basic habit of engagement.

{_PARAMETER_GLOSSARY}
{_JSON_SCHEMA}"""

ACTIVATION_SYSTEM = f"""You are an onboarding specialist for SynaptiqPay, a Brazilian digital wallet platform.

This customer has registered but has no transaction history — they have never made a move. Your job is \
to recommend a first activation offer that lowers the barrier to their first transaction. Consider how \
long they have been registered without acting, which products they own, and what channel brought them in. \
The tone should be welcoming and encouraging, not pressuring. A small, tangible incentive often works better \
than a feature pitch.

{_PARAMETER_GLOSSARY}
{_JSON_SCHEMA}"""


def _products_list(profile: CustomerProfile) -> str:
    owned = [
        name for name, flag in [
            ("wallet", profile.has_wallet),
            ("credit card", profile.has_credit_card),
            ("investment account", profile.has_investment),
            ("insurance", profile.has_insurance),
            ("loan", profile.has_loan),
        ] if flag
    ]
    return ", ".join(owned) if owned else "none"


def _timeline_summary(timeline: list[ActivityTimelineEntry]) -> str:
    if not timeline:
        return "no transaction history"
    last = timeline[-6:]
    return "; ".join(f"{e.year_month}: {e.tx_count} tx (R${e.total_amount:.0f})" for e in last)


def build_user_message(
    profile: CustomerProfile,
    timeline: list[ActivityTimelineEntry],
    cluster_avg_rfm: float | None,
    cohort_health: str | None,
) -> str:
    avg = f"{cluster_avg_rfm:.2f}" if cluster_avg_rfm is not None else "n/a"
    health = cohort_health or "n/a"
    return f"""Customer profile:
- cluster_name: {profile.cluster_name or "none (no transaction history)"}
- cluster_position: {profile.cluster_position or "n/a"}
- lifecycle_stage: {profile.lifecycle_stage or "n/a"}
- rfm_score: {profile.rfm_score or "n/a"} (cluster_avg_rfm: {avg})
- recency_score: {profile.recency_score or "n/a"}
- frequency_score: {profile.frequency_score or "n/a"}
- monetary_score: {profile.monetary_score or "n/a"}
- recency_days: {profile.recency_days or "n/a"}
- products_owned: {_products_list(profile)}
- acquisition_channel: {profile.acquisition_channel}
- acquisition_cost: R${profile.acquisition_cost:.0f}
- tenure_months: {profile.tenure_months}
- cohort_health: {health}
- activity_trend: {_timeline_summary(timeline)}"""
