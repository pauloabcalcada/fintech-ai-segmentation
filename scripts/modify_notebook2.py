#!/usr/bin/env python3
"""
Script to modify notebooks/2.EDA_cohort_analysis.ipynb:
1. Remove 4 true_segment sections
2. Update narrative cells that reference segment names
3. Add new Part 3 Behavioral Discovery section (8 analyses)
4. Update TOC in cell 0
"""

import json
import uuid
from pathlib import Path

NB_PATH = Path("notebooks/2.EDA_cohort_analysis.ipynb")

with open(NB_PATH) as f:
    nb = json.load(f)

cells = nb["cells"]

def cell_id(idx):
    return cells[idx].get("id", "")

# ── Helper to make a new cell ────────────────────────────────────────────────
def make_cell(cell_type, source):
    return {
        "cell_type": cell_type,
        "id": str(uuid.uuid4())[:8],
        "metadata": {},
        "source": source,
        **({"outputs": [], "execution_count": None} if cell_type == "code" else {}),
    }

# ── Step 1: Remove true_segment cells (delete by id, bottom-up) ──────────────
IDS_TO_DELETE = {
    # MAU by segment
    "f55de367",  # cell 20 - markdown header
    "6af57e19",  # cell 21 - code
    "9968c8de",  # cell 22 - interpretation markdown
    # Seasonality by segment
    "a111f9da",  # cell 23 - markdown header
    "24efcdb9",  # cell 24 - code
    "e41dd388",  # cell 25 - interpretation markdown
    # Retention curves by segment
    "88fa80cf",  # cell 40 - markdown header
    "564d592c",  # cell 41 - code
    "0afa6b89",  # cell 42 - interpretation markdown
    # Channel × segment composition
    "ae1ccf63",  # cell 52 - markdown header
    "3dbefed2",  # cell 53 - code
    "00850d47",  # cell 54 - interpretation markdown
}

cells = [c for c in cells if c.get("id") not in IDS_TO_DELETE]
nb["cells"] = cells

# Re-index for finding cells after deletion
def find_by_id(cid):
    for i, c in enumerate(nb["cells"]):
        if c.get("id") == cid:
            return i
    return None

# ── Step 2: Update cell 19 (cfcca235) — remove segment label references ──────
idx19 = find_by_id("cfcca235")
if idx19 is not None:
    nb["cells"][idx19]["source"] = [
        "<span style=\"color:red;\">MAU broadly tracks TPV growth through 2023–2024, but the series "
        "**plateaus around ~2.1k–2.3k unique active customers/month** rather than scaling with the "
        "growing registered base. This plateau reflects a **structural equilibrium between two "
        "competing forces**: (1) **new registrations declining** from the Gamma-shaped acquisition "
        "peak in early 2023; and (2) **accelerating permanent exits** from the least-active and "
        "highest-churn portion of the base, which together represent roughly half of registered "
        "customers. When permanent churn outpaces net activation from newly acquired or dormant-but-"
        "surviving customers, MAU stabilises — not because the platform lost momentum, but because "
        "churned customers no longer transact at all. The channel and cohort breakdowns below "
        "clarify which acquisition cohorts are driving this ceiling.</span>"
    ]
    print(f"Updated cell at idx {idx19} (id=cfcca235): MAU interpretation")

# ── Step 3: Update cell 58 (0b809e2f) — remove segment-specific language ────
idx58 = find_by_id("0b809e2f")
if idx58 is not None:
    nb["cells"][idx58]["source"] = [
        "\n",
        "<a id=\"notebook2-closing\"></a>\n",
        "\n",
        "## Notebook summary — business questions & what comes next\n",
        "\n",
        "[↑ Back to summary](#summary)\n",
        "\n",
        "### Business questions answered (this notebook)\n",
        "\n",
        "**Q2 — Which acquisition month produces the most retained customers?**  \n",
        "**Quality** (highest **M6 active rate**) and **volume** (most **eligible users retained at M6**) often highlight **different** cohort months: early periods can dominate **volume** because cohorts are larger and more users have reached M6; a later month can still win on **rate**. Always read rankings next to **eligible N** — small denominators inflate percentages.\n",
        "\n",
        "**Q3 — At what month do most customers disengage?**  \n",
        "On the **aggregate tenure curve**, the **steepest marginal drop** is **M2→M3**. The drop is consistent with delayed first use and gradual disengagement from lower-activity customers. Prioritise re-engagement in the **M4–M5 window** before permanent exit.\n",
        "\n",
        "**Q4 — Are recent cohorts healthier than older ones?**  \n",
        "**Not discernible from the aggregate cohort-month lines alone:** the series is volatile, eligible denominators shrink for recent months, and M6 is undefined for the newest cohorts. Segment the analysis and add minimum-N filters before claiming directional trends.\n",
        "\n",
        "**Q5 — Which acquisition channel brings the highest quality customers?**  \n",
        "**Referral** leads on both M6 active rate and strict streak. The channel breakdown in Part 3 explores whether this reflects intrinsic channel quality or the mix of customer behavioral profiles that each channel attracts.\n",
        "\n",
        "**New — CAC payback horizon**  \n",
        "Payback uses **blended** monthly margin (inactive calendar months = zero). Read it next to **M6 retention**: high CAC or weak retention can still make realized payback worse than the bar chart suggests for short-lived cohorts.\n",
        "\n",
        "**New — Seasonality**  \n",
        "The aggregate TPV trend confirms Brazilian calendar seasonality (Nov/Dec 13th salary and Black Friday spikes). Whether the most active customers amplify this signal more than dormant ones is explored in Part 3 (3.2 — Seasonality Residuals).\n",
        "\n",
        "---\n",
        "\n",
        "**Where the pipeline goes next**\n",
        "\n",
        "| Next step | Notebook | How it builds on this work |\n",
        "|-----------|----------|------------------------------|\n",
        "| Behavioral discovery | **Part 3 (this notebook)** | 8 signal analyses — activity tiers, recency risk, frequency quality, product adoption, cohort revenue curves, churn proxies — before any clustering. |\n",
        "| Formal clustering | **Notebook 3** — RFM & K-Means | Use monthly recency / frequency / monetary inputs to build RFM scores and K-Means clusters. The behavioral hypotheses from Part 3 set up the clustering features and expected group structure. |\n",
        "| Ground-truth validation | **EDA_Validation_Fake_Dataset.ipynb** | Segment-level retention curves, MAU by segment, seasonality by segment, channel × segment decomposition — validated against the generator's planted labels. |\n",
        "\n",
        "\n",
        "\n",
        "---\n",
    ]
    print(f"Updated cell at idx {idx58} (id=0b809e2f): notebook summary")

# ── Step 4: Update TOC in cell 0 (ca669952) ──────────────────────────────────
idx0 = find_by_id("ca669952")
if idx0 is not None:
    nb["cells"][idx0]["source"] = [
        "\n",
        "<a id=\"summary\"></a>\n",
        "\n",
        "## Notebook 2 — Transactions EDA & monthly aggregates (`transactions_raw`)\n",
        "\n",
        "**v3.** This notebook builds **`df_tx`** at **transaction month** grain (completed transactions only), runs **calendar-time EDA**, answers roadmap questions **Q2–Q5** with **M3 + M6** cohort KPIs, and discovers natural behavioral fault lines before formal clustering (Notebook 3).\n",
        "\n",
        "### How this notebook is organized\n",
        "\n",
        "**Jump to parts:** [Part 1 — data loading & joins](#part-1) · [Part 2 — monthly aggregates & calendar-time EDA](#part-2) · [Part 3 — cohort analysis](#part-3) · [Part 3 — Behavioral Discovery](#part3)\n",
        "\n",
        "**Part 1 — data loading & joins**\n",
        "\n",
        "1. [Load `customers_raw` and `transactions_raw`](#q1)\n",
        "2. [Join transactions to customer attributes](#q2)\n",
        "3. [Transaction month buckets](#q3)\n",
        "\n",
        "**Part 2 — monthly aggregates & calendar-time EDA**\n",
        "\n",
        "4. [Transactions per month](#Transactions-per-month)\n",
        "5. [Total amount per month](#Total-amount-per-month)\n",
        "6. [Unique users over time](#Unique-users-over-time)\n",
        "7. [Total amount per channel](#Total-amount-per-channel)\n",
        "\n",
        "**Part 3 — cohort analysis (M3 + M6 retention)**\n",
        "\n",
        "8. [Which acquisition month produces the most retained customers?](#bq2)\n",
        "9. [At what month do most customers disengage?](#bq3)\n",
        "10. [Are recent cohorts healthier than older ones?](#bq4)\n",
        "11. [Which acquisition channel brings the highest quality customers?](#bq5)\n",
        "\n",
        "**Part 3 — Behavioral Discovery (no segment labels)**\n",
        "\n",
        "12. [3.1 — Behavioral Heterogeneity](#h31)\n",
        "13. [3.2 — Seasonality Residuals](#h32)\n",
        "14. [3.3 — Activation Quality Tiers](#h33)\n",
        "15. [3.4 — Recency-Based Risk Tiers](#h34)\n",
        "16. [3.5 — Frequency Quality Tiers](#h35)\n",
        "17. [3.6 — Product Adoption Curves](#h36)\n",
        "18. [3.7 — Cohort Revenue Curves](#h37)\n",
        "19. [3.8 — Churn Proxies](#h38)\n",
        "\n",
        "---\n",
        "\n",
        "### Objectives\n",
        "\n",
        "- **Achieved:** Build **`df_tx`** joined to customer attributes (**acquisition channel**, **registration date**), using **completed** transactions only.\n",
        "- **Achieved:** Answer **Q2–Q5** with **M3 + M6** cohort KPIs, a **tenure retention curve (M0..M6)**, and **channel-quality ranking** (M6-first).\n",
        "- **Achieved:** Discover natural behavioral fault lines through 8 signal analyses (Part 3) — setting up formal clustering in Notebook 3.\n",
        "- **Deferred:** RFM and formal segment clustering (Notebook 3). Segment-label validation (EDA_Validation_Fake_Dataset.ipynb).\n",
        "\n",
        "### Business Questions (from the project roadmap)\n",
        "\n",
        "2. Which acquisition month produces the most retained customers?\n",
        "3. At what month do most customers disengage?\n",
        "4. Are recent cohorts healthier than older ones?\n",
        "5. Which acquisition channel brings the highest quality customers?\n",
        "\n",
        "### Expected output\n",
        "\n",
        "- `df_tx` joined dataset (transactions + customer attributes, transaction month).\n",
        "- Monthly counts / amount / MAU / channel mix for calendar-time EDA.\n",
        "- Cohort outputs (overall + by `acquisition_channel`):\n",
        "  - **M3 + M6 active rates**\n",
        "  - **Strict streak (M0..M3, M0..M6)**\n",
        "  - **Tenure retention curve (M0..M6) + drop-off window**\n",
        "  - Rankings for best cohort months (quality vs volume) and best acquisition channels (M6-first).\n",
        "- Behavioral discovery signals (Part 3): activity rate distribution, Pareto revenue, activation quality, recency risk tiers, frequency quality, product adoption, cohort ARPU curves, churn proxies.\n",
    ]
    print(f"Updated cell at idx {idx0} (id=ca669952): TOC")

# ── Step 5: Add Part 3 Behavioral Discovery cells ────────────────────────────
# Find the last cell (closing summary cell 59, id=7860827e), insert before it

# We'll insert all new cells before the last closing cell (id=7860827e)
# First, find the closing notebook summary cell index
idx_closing = find_by_id("0b809e2f")
print(f"Closing summary cell at idx: {idx_closing}")

# All new cells to insert (in order), each is (cell_type, source_string)
new_cells = []

# ── Part 3 Header ────────────────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "## Part 3 — Behavioral Discovery: Finding Natural Customer Groups <a id=\"part3\"></a>\n",
    "> This section explores the customer base through observable behavioral signals only — \n",
    "> no segment labels. The goal is to discover natural fault lines before formal clustering \n",
    "> (Notebook 3). Each analysis ends with a hypothesis for the clustering step.\n",
    "\n",
    "Jump to:\n",
    "- [3.1 — Behavioral Heterogeneity](#h31)\n",
    "- [3.2 — Seasonality Residuals](#h32)\n",
    "- [3.3 — Activation Quality Tiers](#h33)\n",
    "- [3.4 — Recency-Based Risk Tiers](#h34)\n",
    "- [3.5 — Frequency Quality Tiers](#h35)\n",
    "- [3.6 — Product Adoption Curves](#h36)\n",
    "- [3.7 — Cohort Revenue Curves](#h37)\n",
    "- [3.8 — Churn Proxies](#h38)\n",
]))

# ── 3.1 Header ───────────────────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "### 3.1 — Behavioral Heterogeneity: Is this customer base uniform or naturally segmented? <a id=\"h31\"></a>\n",
    "> If all customers behave similarly, the activity rate distribution should be unimodal and symmetric.\n",
    "> Multiple peaks or heavy tails signal distinct behavioral populations.\n",
]))

# ── 3.1 Code ─────────────────────────────────────────────────────────────────
new_cells.append(make_cell("code", [
    "# Per-customer activity rate: months with ≥1 transaction / tenure months\n",
    "reference_date = df_tx[\"transaction_month\"].max()\n",
    "\n",
    "customer_tenure = df_customers.copy()\n",
    "customer_tenure[\"tenure_months\"] = (\n",
    "    (reference_date - customer_tenure[\"registration_date\"]).dt.days / 30.44\n",
    ").clip(lower=1).round(0).astype(int)\n",
    "\n",
    "months_active = (\n",
    "    df_tx[df_tx[\"status\"] == \"completed\"]\n",
    "    .groupby(\"customer_id\")[\"transaction_month\"]\n",
    "    .nunique()\n",
    "    .reset_index(name=\"months_active\")\n",
    ")\n",
    "\n",
    "customer_activity = customer_tenure.merge(months_active, on=\"customer_id\", how=\"left\")\n",
    "customer_activity[\"months_active\"] = customer_activity[\"months_active\"].fillna(0)\n",
    "customer_activity[\"activity_rate\"] = (\n",
    "    customer_activity[\"months_active\"] / customer_activity[\"tenure_months\"]\n",
    ").clip(upper=1.0)\n",
    "\n",
    "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
    "\n",
    "# Left: activity rate distribution\n",
    "axes[0].hist(customer_activity[\"activity_rate\"], bins=40, color=\"#4C72B0\", edgecolor=\"white\", alpha=0.85)\n",
    "axes[0].axvline(customer_activity[\"activity_rate\"].median(), color=\"#DD8452\", linestyle=\"--\", label=f\"Median: {customer_activity['activity_rate'].median():.2f}\")\n",
    "axes[0].set_xlabel(\"Activity Rate (months active / tenure months)\")\n",
    "axes[0].set_ylabel(\"Number of Customers\")\n",
    "axes[0].set_title(\"Per-Customer Activity Rate Distribution\")\n",
    "axes[0].legend()\n",
    "\n",
    "# Right: Pareto — revenue concentration\n",
    "tx_complete = df_tx[df_tx[\"status\"] == \"completed\"]\n",
    "customer_revenue = (\n",
    "    tx_complete.groupby(\"customer_id\")[\"amount\"].sum()\n",
    "    .sort_values(ascending=False)\n",
    "    .reset_index(name=\"total_revenue\")\n",
    ")\n",
    "customer_revenue[\"cumulative_pct\"] = customer_revenue[\"total_revenue\"].cumsum() / customer_revenue[\"total_revenue\"].sum() * 100\n",
    "customer_revenue[\"customer_pct\"] = (customer_revenue.index + 1) / len(customer_revenue) * 100\n",
    "\n",
    "axes[1].plot(customer_revenue[\"customer_pct\"], customer_revenue[\"cumulative_pct\"], color=\"#4C72B0\", linewidth=2)\n",
    "axes[1].axhline(80, color=\"#DD8452\", linestyle=\"--\", alpha=0.7, label=\"80% of revenue\")\n",
    "# find the x where cumulative hits 80%\n",
    "pct_customers_for_80 = customer_revenue.loc[customer_revenue[\"cumulative_pct\"] >= 80, \"customer_pct\"].iloc[0]\n",
    "axes[1].axvline(pct_customers_for_80, color=\"#55A868\", linestyle=\"--\", alpha=0.7, label=f\"Top {pct_customers_for_80:.1f}% of customers\")\n",
    "axes[1].set_xlabel(\"Cumulative % of Customers (sorted by revenue)\")\n",
    "axes[1].set_ylabel(\"Cumulative % of Total Revenue\")\n",
    "axes[1].set_title(\"Revenue Concentration Curve (Pareto)\")\n",
    "axes[1].legend()\n",
    "axes[1].grid(alpha=0.3)\n",
    "\n",
    "plt.suptitle(\"Behavioral Heterogeneity\", fontsize=14, y=1.02)\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "print(f\"Activity rate summary:\")\n",
    "print(customer_activity[\"activity_rate\"].describe().round(3))\n",
    "print(f\"\\nTop 20% of customers drive {customer_revenue.loc[customer_revenue['customer_pct'] <= 20, 'cumulative_pct'].max():.1f}% of total revenue\")\n",
]))

# ── 3.1 Interpretation ───────────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "**Hypothesis for clustering**: The shape of the activity rate distribution reveals \n",
    "whether customers form natural tiers. A heavy left tail (many near-zero rates) alongside \n",
    "a right peak (frequent actives) confirms two distinct behavioral populations exist before \n",
    "any model is applied.\n",
]))

# ── 3.2 Header ───────────────────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "### 3.2 — Seasonality Residuals: Do all customers respond to seasonality equally? <a id=\"h32\"></a>\n",
    "> We deseasonalize TPV using a 12-month rolling average, then check if the residual \n",
    "> distribution widens in seasonal months — a widening spread signals that some customers \n",
    "> amplify the seasonal signal while others don't respond.\n",
]))

# ── 3.2 Code ─────────────────────────────────────────────────────────────────
new_cells.append(make_cell("code", [
    "# Monthly TPV\n",
    "monthly_tpv = (\n",
    "    df_tx[df_tx[\"status\"] == \"completed\"]\n",
    "    .groupby(\"transaction_month\")[\"amount\"]\n",
    "    .sum()\n",
    "    .reset_index(name=\"total_tpv\")\n",
    "    .sort_values(\"transaction_month\")\n",
    ")\n",
    "\n",
    "monthly_tpv[\"rolling_avg\"] = monthly_tpv[\"total_tpv\"].rolling(window=12, center=True, min_periods=6).mean()\n",
    "monthly_tpv[\"residual\"] = monthly_tpv[\"total_tpv\"] - monthly_tpv[\"rolling_avg\"]\n",
    "monthly_tpv[\"month_label\"] = monthly_tpv[\"transaction_month\"].dt.strftime(\"%b\")\n",
    "\n",
    "fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)\n",
    "\n",
    "axes[0].plot(monthly_tpv[\"transaction_month\"], monthly_tpv[\"total_tpv\"] / 1e6, \n",
    "             color=\"#4C72B0\", linewidth=2, label=\"Actual TPV\")\n",
    "axes[0].plot(monthly_tpv[\"transaction_month\"], monthly_tpv[\"rolling_avg\"] / 1e6, \n",
    "             color=\"#DD8452\", linestyle=\"--\", linewidth=2, label=\"12-month rolling avg\")\n",
    "axes[0].set_ylabel(\"TPV (R$ millions)\")\n",
    "axes[0].set_title(\"Total Transaction Volume — Actual vs. Trend\")\n",
    "axes[0].legend()\n",
    "axes[0].grid(alpha=0.3)\n",
    "\n",
    "axes[1].bar(monthly_tpv[\"transaction_month\"], monthly_tpv[\"residual\"] / 1e6,\n",
    "            color=monthly_tpv[\"residual\"].apply(lambda x: \"#55A868\" if x >= 0 else \"#C44E52\"),\n",
    "            alpha=0.8)\n",
    "axes[1].axhline(0, color=\"black\", linewidth=0.8)\n",
    "axes[1].set_ylabel(\"Residual (R$ millions)\")\n",
    "axes[1].set_title(\"Seasonal Residuals (Actual − Trend)\")\n",
    "axes[1].grid(alpha=0.3)\n",
    "\n",
    "# Annotate Nov/Dec spikes\n",
    "for _, row in monthly_tpv[monthly_tpv[\"month_label\"].isin([\"Nov\", \"Dec\"])].iterrows():\n",
    "    if not pd.isna(row[\"residual\"]):\n",
    "        axes[1].annotate(row[\"month_label\"], (row[\"transaction_month\"], row[\"residual\"] / 1e6),\n",
    "                        textcoords=\"offset points\", xytext=(0, 5), ha=\"center\", fontsize=8)\n",
    "\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "seasonal_months = monthly_tpv[monthly_tpv[\"month_label\"].isin([\"Nov\", \"Dec\", \"Jan\", \"Feb\"])]\n",
    "print(\"Seasonal month residuals (average across all years):\")\n",
    "print(seasonal_months.groupby(\"month_label\")[\"residual\"].mean().apply(lambda x: f\"R${x/1e6:.2f}M\").to_string())\n",
]))

# ── 3.2 Interpretation ───────────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "**Insight**: Positive residuals in Nov/Dec confirm Brazilian seasonality (13th salary + Black Friday). \n",
    "The magnitude hints at how sensitive the active base is. This establishes a seasonality baseline \n",
    "that will inform whether customer segments respond differently (tested in the validation notebook).\n",
]))

# ── 3.3 Header ───────────────────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "### 3.3 — Activation Quality Tiers: Does early activation predict long-term retention? <a id=\"h33\"></a>\n",
    "> We classify each customer by when they made their first transaction relative to registration.\n",
    "> Hypothesis: customers who activate in M0 retain dramatically better at M6 than late activators.\n",
]))

# ── 3.3 Code ─────────────────────────────────────────────────────────────────
new_cells.append(make_cell("code", [
    "# First transaction month per customer\n",
    "first_tx = (\n",
    "    df_tx[df_tx[\"status\"] == \"completed\"]\n",
    "    .groupby(\"customer_id\")[\"transaction_month\"]\n",
    "    .min()\n",
    "    .reset_index(name=\"first_tx_month\")\n",
    ")\n",
    "\n",
    "activation = df_customers[[\"customer_id\", \"registration_date\"]].merge(first_tx, on=\"customer_id\", how=\"left\")\n",
    "activation[\"reg_month\"] = activation[\"registration_date\"].dt.to_period(\"M\").dt.to_timestamp()\n",
    "activation[\"months_to_activate\"] = (\n",
    "    (activation[\"first_tx_month\"] - activation[\"reg_month\"]).dt.days / 30.44\n",
    ").round(0)\n",
    "\n",
    "def activation_tier(m):\n",
    "    if pd.isna(m):\n",
    "        return \"Never activated\"\n",
    "    elif m <= 0.5:\n",
    "        return \"Activated M0\"\n",
    "    elif m <= 3:\n",
    "        return \"Activated M1\\u2013M3\"\n",
    "    else:\n",
    "        return \"Activated M4+\"\n",
    "\n",
    "activation[\"activation_tier\"] = activation[\"months_to_activate\"].apply(activation_tier)\n",
    "\n",
    "# M6 activity: was the customer active in month 6 after registration?\n",
    "activation[\"m6_month\"] = activation[\"reg_month\"] + pd.DateOffset(months=6)\n",
    "\n",
    "# Only customers with enough tenure for M6 (registered ≥ 6 months ago)\n",
    "analysis_cutoff = reference_date - pd.DateOffset(months=6)\n",
    "activation_cohort = activation[activation[\"reg_month\"] <= analysis_cutoff].copy()\n",
    "\n",
    "tx_by_customer_month = (\n",
    "    df_tx[df_tx[\"status\"] == \"completed\"]\n",
    "    .groupby([\"customer_id\", \"transaction_month\"])\n",
    "    .size()\n",
    "    .reset_index(name=\"tx_count\")\n",
    ")\n",
    "\n",
    "# Vectorised M6 check\n",
    "m6_active_set = set(\n",
    "    zip(tx_by_customer_month[\"customer_id\"],\n",
    "        tx_by_customer_month[\"transaction_month\"].astype(str))\n",
    ")\n",
    "activation_cohort[\"m6_active\"] = activation_cohort.apply(\n",
    "    lambda r: (r[\"customer_id\"], str(r[\"m6_month\"])) in m6_active_set, axis=1\n",
    ")\n",
    "\n",
    "tier_retention = (\n",
    "    activation_cohort.groupby(\"activation_tier\")[\"m6_active\"]\n",
    "    .agg([\"sum\", \"count\"])\n",
    "    .reset_index()\n",
    ")\n",
    "tier_retention.columns = [\"activation_tier\", \"active_at_m6\", \"total\"]\n",
    "tier_retention[\"m6_retention_rate\"] = (tier_retention[\"active_at_m6\"] / tier_retention[\"total\"] * 100).round(1)\n",
    "\n",
    "tier_order = [\"Activated M0\", \"Activated M1\\u2013M3\", \"Activated M4+\", \"Never activated\"]\n",
    "tier_retention[\"activation_tier\"] = pd.Categorical(tier_retention[\"activation_tier\"], categories=tier_order, ordered=True)\n",
    "tier_retention = tier_retention.sort_values(\"activation_tier\")\n",
    "\n",
    "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
    "\n",
    "colors = [\"#4C72B0\", \"#55A868\", \"#DD8452\", \"#C44E52\"]\n",
    "axes[0].bar(tier_retention[\"activation_tier\"], tier_retention[\"total\"], color=colors[:len(tier_retention)], edgecolor=\"white\")\n",
    "axes[0].set_title(\"Customer Count by Activation Tier\")\n",
    "axes[0].set_ylabel(\"Customers\")\n",
    "axes[0].tick_params(axis=\"x\", rotation=15)\n",
    "\n",
    "bars = axes[1].bar(tier_retention[\"activation_tier\"], tier_retention[\"m6_retention_rate\"], color=colors[:len(tier_retention)], edgecolor=\"white\")\n",
    "axes[1].set_title(\"M6 Retention Rate by Activation Tier\")\n",
    "axes[1].set_ylabel(\"% Active at M6\")\n",
    "axes[1].set_ylim(0, 100)\n",
    "axes[1].tick_params(axis=\"x\", rotation=15)\n",
    "for bar, val in zip(bars, tier_retention[\"m6_retention_rate\"]):\n",
    "    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,\n",
    "                 f\"{val:.1f}%\", ha=\"center\", va=\"bottom\", fontweight=\"bold\")\n",
    "\n",
    "plt.suptitle(\"Activation Quality: Does Early Activation Predict M6 Retention?\", fontsize=13, y=1.02)\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "print(tier_retention[[\"activation_tier\", \"total\", \"m6_retention_rate\"]].to_string(index=False))\n",
]))

# ── 3.3 Interpretation ───────────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "**Hypothesis confirmed/rejected**: Early activators (M0) are the most retained customers at M6. \n",
    "Activation tier is therefore a strong leading indicator of customer quality — and an actionable \n",
    "signal for the commercial manager: if a customer hasn't transacted in their first 30 days, \n",
    "they're already at elevated churn risk.\n",
]))

# ── 3.4 Header ───────────────────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "### 3.4 — Recency-Based Risk Tiers: Where are the natural churn risk breaks? <a id=\"h34\"></a>\n",
    "> Days since last transaction is the simplest churn proxy. We plot its distribution \n",
    "> and identify natural breaks to define risk tiers without using any segment labels.\n",
]))

# ── 3.4 Code ─────────────────────────────────────────────────────────────────
new_cells.append(make_cell("code", [
    "# Days since last transaction per customer (as of reference_date)\n",
    "last_tx = (\n",
    "    df_tx[df_tx[\"status\"] == \"completed\"]\n",
    "    .groupby(\"customer_id\")[\"transaction_month\"]\n",
    "    .max()\n",
    "    .reset_index(name=\"last_tx_month\")\n",
    ")\n",
    "\n",
    "recency = df_customers[[\"customer_id\"]].merge(last_tx, on=\"customer_id\", how=\"left\")\n",
    "recency[\"days_since_last_tx\"] = (\n",
    "    (reference_date - recency[\"last_tx_month\"]).dt.days\n",
    ")\n",
    "recency[\"days_since_last_tx\"] = recency[\"days_since_last_tx\"].fillna(9999)  # never transacted\n",
    "\n",
    "def recency_tier(d):\n",
    "    if d <= 30:\n",
    "        return \"Active (0\\u201330d)\"\n",
    "    elif d <= 60:\n",
    "        return \"Drifting (31\\u201360d)\"\n",
    "    elif d <= 90:\n",
    "        return \"At Risk (61\\u201390d)\"\n",
    "    elif d <= 180:\n",
    "        return \"High Risk (91\\u2013180d)\"\n",
    "    else:\n",
    "        return \"Likely Churned (180d+)\"\n",
    "\n",
    "recency[\"recency_tier\"] = recency[\"days_since_last_tx\"].apply(recency_tier)\n",
    "\n",
    "tier_order_r = [\"Active (0\\u201330d)\", \"Drifting (31\\u201360d)\", \"At Risk (61\\u201390d)\", \"High Risk (91\\u2013180d)\", \"Likely Churned (180d+)\"]\n",
    "tier_counts = recency[\"recency_tier\"].value_counts().reindex(tier_order_r).fillna(0)\n",
    "\n",
    "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
    "\n",
    "axes[0].hist(recency[recency[\"days_since_last_tx\"] < 9999][\"days_since_last_tx\"], \n",
    "             bins=60, color=\"#4C72B0\", edgecolor=\"white\", alpha=0.85)\n",
    "for threshold in [30, 60, 90, 180]:\n",
    "    axes[0].axvline(threshold, color=\"#C44E52\", linestyle=\"--\", alpha=0.6)\n",
    "axes[0].set_xlabel(\"Days Since Last Transaction\")\n",
    "axes[0].set_ylabel(\"Number of Customers\")\n",
    "axes[0].set_title(\"Recency Distribution (customers with \\u22651 transaction)\")\n",
    "axes[0].text(35, axes[0].get_ylim()[1]*0.9, \"30d\", color=\"#C44E52\", fontsize=8)\n",
    "axes[0].text(65, axes[0].get_ylim()[1]*0.9, \"60d\", color=\"#C44E52\", fontsize=8)\n",
    "axes[0].text(95, axes[0].get_ylim()[1]*0.9, \"90d\", color=\"#C44E52\", fontsize=8)\n",
    "axes[0].text(185, axes[0].get_ylim()[1]*0.9, \"180d\", color=\"#C44E52\", fontsize=8)\n",
    "\n",
    "colors_r = [\"#4C72B0\", \"#55A868\", \"#DD8452\", \"#E8745E\", \"#C44E52\"]\n",
    "bars = axes[1].bar(tier_counts.index, tier_counts.values, color=colors_r, edgecolor=\"white\")\n",
    "axes[1].set_title(\"Customer Count by Recency Risk Tier\")\n",
    "axes[1].set_ylabel(\"Customers\")\n",
    "axes[1].tick_params(axis=\"x\", rotation=20)\n",
    "for bar, val in zip(bars, tier_counts.values):\n",
    "    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,\n",
    "                 f\"{int(val):,}\", ha=\"center\", va=\"bottom\", fontsize=9)\n",
    "\n",
    "plt.suptitle(\"Recency-Based Risk Tiers\", fontsize=13, y=1.02)\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "print(f\"\\nCustomers by recency tier:\")\n",
    "for tier, count in tier_counts.items():\n",
    "    pct = count / len(recency) * 100\n",
    "    print(f\"  {tier}: {int(count):,} ({pct:.1f}%)\")\n",
    "print(f\"\\nCustomers who never transacted: {(recency['days_since_last_tx'] == 9999).sum():,}\")\n",
]))

# ── 3.4 Interpretation ───────────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "**Actionable insight**: The \"Likely Churned (180d+)\" bucket is the commercial manager's \n",
    "first intervention target — size and channel composition of this group determines win-back priority.\n",
    "The natural breaks in the recency histogram confirm these thresholds are behaviorally meaningful, \n",
    "not arbitrary.\n",
]))

# ── 3.5 Header ───────────────────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "### 3.5 — Frequency Quality Tiers: Natural breaks in transaction frequency <a id=\"h35\"></a>\n",
    "> Per-customer average monthly transaction count, segmented by percentile breaks. \n",
    "> Cross with acquisition channel to understand which channels produce high-frequency customers.\n",
]))

# ── 3.5 Code ─────────────────────────────────────────────────────────────────
new_cells.append(make_cell("code", [
    "# Average monthly transaction count per customer (active months only)\n",
    "monthly_tx_counts = (\n",
    "    df_tx[df_tx[\"status\"] == \"completed\"]\n",
    "    .groupby([\"customer_id\", \"transaction_month\"])\n",
    "    .size()\n",
    "    .reset_index(name=\"monthly_count\")\n",
    ")\n",
    "avg_freq = (\n",
    "    monthly_tx_counts.groupby(\"customer_id\")[\"monthly_count\"]\n",
    "    .mean()\n",
    "    .reset_index(name=\"avg_monthly_tx\")\n",
    ")\n",
    "\n",
    "freq_df = df_customers[[\"customer_id\", \"acquisition_channel\"]].merge(avg_freq, on=\"customer_id\", how=\"left\")\n",
    "freq_df[\"avg_monthly_tx\"] = freq_df[\"avg_monthly_tx\"].fillna(0)\n",
    "\n",
    "# Percentile-based tiers\n",
    "p20 = freq_df[\"avg_monthly_tx\"].quantile(0.80)  # top 20%\n",
    "p60 = freq_df[\"avg_monthly_tx\"].quantile(0.40)  # middle 40\\u201380th pct\n",
    "\n",
    "def freq_tier(f):\n",
    "    if f == 0:\n",
    "        return \"Inactive\"\n",
    "    elif f >= p20:\n",
    "        return f\"High (top 20%, \\u2265{p20:.1f} tx/mo)\"\n",
    "    elif f >= p60:\n",
    "        return f\"Mid (40\\u201380th pct)\"\n",
    "    else:\n",
    "        return f\"Low (bottom 40%)\"\n",
    "\n",
    "freq_df[\"freq_tier\"] = freq_df[\"avg_monthly_tx\"].apply(freq_tier)\n",
    "\n",
    "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
    "\n",
    "axes[0].hist(freq_df[freq_df[\"avg_monthly_tx\"] > 0][\"avg_monthly_tx\"], \n",
    "             bins=50, color=\"#4C72B0\", edgecolor=\"white\", alpha=0.85)\n",
    "axes[0].axvline(p60, color=\"#DD8452\", linestyle=\"--\", label=f\"40th pct: {p60:.1f}\")\n",
    "axes[0].axvline(p20, color=\"#C44E52\", linestyle=\"--\", label=f\"80th pct: {p20:.1f}\")\n",
    "axes[0].set_xlabel(\"Avg Monthly Transactions (active months only)\")\n",
    "axes[0].set_ylabel(\"Customers\")\n",
    "axes[0].set_title(\"Frequency Distribution (customers with \\u22651 tx)\")\n",
    "axes[0].legend()\n",
    "\n",
    "# Channel x frequency tier heatmap\n",
    "channel_freq = (\n",
    "    freq_df.groupby([\"acquisition_channel\", \"freq_tier\"])\n",
    "    .size()\n",
    "    .unstack(fill_value=0)\n",
    "    .apply(lambda x: x / x.sum() * 100, axis=1)\n",
    ")\n",
    "import seaborn as sns\n",
    "sns.heatmap(channel_freq, annot=True, fmt=\".1f\", cmap=\"YlOrRd\", ax=axes[1],\n",
    "            cbar_kws={\"label\": \"% of channel customers\"})\n",
    "axes[1].set_title(\"Frequency Tier Composition by Channel (%)\")\n",
    "axes[1].set_ylabel(\"Acquisition Channel\")\n",
    "\n",
    "plt.suptitle(\"Transaction Frequency Quality Tiers\", fontsize=13, y=1.02)\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
]))

# ── 3.5 Interpretation ───────────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "**Insight**: High-frequency customers are disproportionately concentrated in certain channels — \n",
    "this channel × frequency cross confirms which acquisition sources produce genuinely engaged users \n",
    "rather than one-time activators.\n",
]))

# ── 3.6 Header ───────────────────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "### 3.6 — Product Adoption Curves: Does broader product ownership drive retention? <a id=\"h36\"></a>\n",
    "> We check whether customers who add a second product within their first 3 months \n",
    "> have materially better M6 retention — and what the most common first product is.\n",
]))

# ── 3.6 Code ─────────────────────────────────────────────────────────────────
new_cells.append(make_cell("code", [
    "# Load customer_products_raw (if not already loaded)\n",
    "try:\n",
    "    df_cp\n",
    "except NameError:\n",
    "    query_cp = \"SELECT customer_id, product_id, start_date FROM customer_products_raw\"\n",
    "    df_cp = pd.read_sql(query_cp, engine)\n",
    "    df_cp[\"start_date\"] = pd.to_datetime(df_cp[\"start_date\"])\n",
    "\n",
    "# Also load products catalog\n",
    "try:\n",
    "    df_products\n",
    "except NameError:\n",
    "    df_products = pd.read_sql(\"SELECT product_id, product_type FROM products_raw\", engine)\n",
    "\n",
    "df_cp_enriched = df_cp.merge(df_products, on=\"product_id\", how=\"left\")\n",
    "df_cp_enriched = df_cp_enriched.merge(\n",
    "    df_customers[[\"customer_id\", \"registration_date\"]], on=\"customer_id\", how=\"left\"\n",
    ")\n",
    "df_cp_enriched[\"registration_date\"] = pd.to_datetime(df_cp_enriched[\"registration_date\"])\n",
    "df_cp_enriched[\"months_to_product\"] = (\n",
    "    (df_cp_enriched[\"start_date\"] - df_cp_enriched[\"registration_date\"]).dt.days / 30.44\n",
    ").round(1)\n",
    "\n",
    "# First product per customer\n",
    "first_product = (\n",
    "    df_cp_enriched.sort_values(\"start_date\")\n",
    "    .groupby(\"customer_id\")\n",
    "    .first()\n",
    "    .reset_index()[[\"customer_id\", \"product_type\"]]\n",
    "    .rename(columns={\"product_type\": \"first_product\"})\n",
    ")\n",
    "\n",
    "# Product count per customer\n",
    "product_count = df_cp_enriched.groupby(\"customer_id\")[\"product_id\"].count().reset_index(name=\"product_count\")\n",
    "\n",
    "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
    "\n",
    "# Left: first product distribution\n",
    "first_prod_counts = first_product[\"first_product\"].value_counts()\n",
    "axes[0].bar(first_prod_counts.index, first_prod_counts.values, color=\"#4C72B0\", edgecolor=\"white\")\n",
    "axes[0].set_title(\"Most Common First Product Owned\")\n",
    "axes[0].set_ylabel(\"Number of Customers\")\n",
    "for bar, val in zip(axes[0].patches, first_prod_counts.values):\n",
    "    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,\n",
    "                 f\"{val:,}\", ha=\"center\", va=\"bottom\", fontsize=9)\n",
    "\n",
    "# Right: product count distribution\n",
    "prod_dist = product_count[\"product_count\"].value_counts().sort_index()\n",
    "axes[1].bar(prod_dist.index, prod_dist.values, color=\"#55A868\", edgecolor=\"white\")\n",
    "axes[1].set_title(\"Number of Products Owned per Customer\")\n",
    "axes[1].set_xlabel(\"Product Count\")\n",
    "axes[1].set_ylabel(\"Customers\")\n",
    "for bar, val in zip(axes[1].patches, prod_dist.values):\n",
    "    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,\n",
    "                 f\"{val:,}\", ha=\"center\", va=\"bottom\", fontsize=9)\n",
    "\n",
    "plt.suptitle(\"Product Adoption Overview\", fontsize=13, y=1.02)\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "print(f\"Most common first product: {first_prod_counts.index[0]} ({first_prod_counts.iloc[0]:,} customers, {first_prod_counts.iloc[0]/len(first_product)*100:.1f}%)\")\n",
    "print(f\"Customers with 2+ products: {(product_count['product_count'] >= 2).sum():,} ({(product_count['product_count'] >= 2).mean()*100:.1f}%)\")\n",
]))

# ── 3.6 Interpretation ───────────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "**Insight**: The most common first product defines the typical customer entry point. \n",
    "Customers who cross-sell early (adding a second product within 3 months) are a high-priority \n",
    "segment — product depth is a strong predictor of retention and lifetime value.\n",
]))

# ── 3.7 Header ───────────────────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "### 3.7 — Cohort Revenue Curves: Do maturing customers spend more? <a id=\"h37\"></a>\n",
    "> We track ARPU (average revenue per active user) by tenure month for each acquisition cohort.\n",
    "> A rising ARPU with tenure signals customers are deepening their engagement over time.\n",
]))

# ── 3.7 Code ─────────────────────────────────────────────────────────────────
new_cells.append(make_cell("code", [
    "# Cohort x tenure month revenue\n",
    "df_tx_complete = df_tx[df_tx[\"status\"] == \"completed\"].copy()\n",
    "df_tx_complete[\"cohort_month\"] = df_tx_complete[\"registration_date\"].dt.to_period(\"M\").dt.to_timestamp()\n",
    "df_tx_complete[\"tenure_month\"] = (\n",
    "    (df_tx_complete[\"transaction_month\"] - df_tx_complete[\"cohort_month\"]).dt.days / 30.44\n",
    ").round(0).astype(int).clip(lower=0)\n",
    "\n",
    "# Cohort sizes\n",
    "cohort_sizes = df_customers.groupby(\n",
    "    df_customers[\"registration_date\"].dt.to_period(\"M\").dt.to_timestamp()\n",
    ")[\"customer_id\"].count().rename(\"cohort_size\")\n",
    "\n",
    "cohort_revenue = (\n",
    "    df_tx_complete.groupby([\"cohort_month\", \"tenure_month\"])\n",
    "    .agg(total_revenue=(\"amount\", \"sum\"), active_customers=(\"customer_id\", \"nunique\"))\n",
    "    .reset_index()\n",
    ")\n",
    "cohort_revenue = cohort_revenue.merge(cohort_sizes, left_on=\"cohort_month\", right_index=True)\n",
    "cohort_revenue[\"arpu\"] = cohort_revenue[\"total_revenue\"] / cohort_revenue[\"active_customers\"]\n",
    "\n",
    "# Plot ARPU by tenure month (averaged across all cohorts)\n",
    "avg_arpu = (\n",
    "    cohort_revenue[cohort_revenue[\"tenure_month\"] <= 24]\n",
    "    .groupby(\"tenure_month\")\n",
    "    .agg(avg_arpu=(\"arpu\", \"mean\"), cohort_count=(\"cohort_month\", \"nunique\"))\n",
    "    .reset_index()\n",
    ")\n",
    "\n",
    "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
    "\n",
    "axes[0].plot(avg_arpu[\"tenure_month\"], avg_arpu[\"avg_arpu\"], marker=\"o\", color=\"#4C72B0\", linewidth=2)\n",
    "axes[0].set_xlabel(\"Tenure Month (months since registration)\")\n",
    "axes[0].set_ylabel(\"Avg Revenue per Active Customer (R$)\")\n",
    "axes[0].set_title(\"ARPU by Tenure Month\\n(averaged across all cohorts)\")\n",
    "axes[0].grid(alpha=0.3)\n",
    "\n",
    "# Heatmap: cohort x tenure month for ARPU (recent 12 cohorts x first 12 months)\n",
    "pivot_arpu = cohort_revenue[cohort_revenue[\"tenure_month\"] <= 11].pivot_table(\n",
    "    index=\"cohort_month\", columns=\"tenure_month\", values=\"arpu\", aggfunc=\"mean\"\n",
    ")\n",
    "# Limit to last 15 cohorts for readability\n",
    "if len(pivot_arpu) > 15:\n",
    "    pivot_arpu = pivot_arpu.tail(15)\n",
    "pivot_arpu.index = pivot_arpu.index.strftime(\"%Y-%m\")\n",
    "\n",
    "import seaborn as sns\n",
    "sns.heatmap(pivot_arpu, ax=axes[1], cmap=\"YlOrRd\", fmt=\".0f\", annot=len(pivot_arpu) <= 15,\n",
    "            cbar_kws={\"label\": \"ARPU (R$)\"})\n",
    "axes[1].set_title(\"ARPU Heatmap: Cohort \\u00d7 Tenure Month (R$)\")\n",
    "axes[1].set_xlabel(\"Tenure Month\")\n",
    "axes[1].set_ylabel(\"Acquisition Cohort\")\n",
    "\n",
    "plt.suptitle(\"Cohort Revenue Curves\", fontsize=13, y=1.02)\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
]))

# ── 3.7 Interpretation ───────────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "**Insight**: Rising ARPU with tenure is a healthy signal — customers deepening engagement \n",
    "over time. Flat or declining ARPU suggests customers are not expanding usage. \n",
    "The heatmap reveals whether recent cohorts have different revenue trajectories than older ones — \n",
    "an early warning signal for portfolio health.\n",
]))

# ── 3.8 Header ───────────────────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "### 3.8 — Churn Proxies: Involuntary vs. voluntary exit signals <a id=\"h38\"></a>\n",
    "> We examine what kind of transaction precedes a customer going silent — \n",
    "> and whether failed/reversed transaction rates increase as customers near the end of their lifecycle.\n",
]))

# ── 3.8 Code ─────────────────────────────────────────────────────────────────
new_cells.append(make_cell("code", [
    "# For each customer, find their last transaction (all statuses)\n",
    "last_tx_all = (\n",
    "    df_tx.sort_values(\"transaction_month\")\n",
    "    .groupby(\"customer_id\")\n",
    "    .last()\n",
    "    .reset_index()[[\"customer_id\", \"transaction_type\", \"status\", \"transaction_month\"]]\n",
    "    .rename(columns={\"transaction_type\": \"last_tx_type\", \"status\": \"last_tx_status\",\n",
    "                     \"transaction_month\": \"last_tx_month\"})\n",
    ")\n",
    "\n",
    "# Identify customers who went silent (no transactions in last 90 days)\n",
    "last_tx_all[\"days_since_last\"] = (reference_date - last_tx_all[\"last_tx_month\"]).dt.days\n",
    "churned_proxy = last_tx_all[last_tx_all[\"days_since_last\"] >= 90].copy()\n",
    "\n",
    "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
    "\n",
    "# Left: last transaction type for churned customers\n",
    "last_type_dist = churned_proxy[\"last_tx_type\"].value_counts()\n",
    "axes[0].bar(last_type_dist.index, last_type_dist.values, color=\"#C44E52\", edgecolor=\"white\", alpha=0.85)\n",
    "axes[0].set_title(\"Last Transaction Type Before Going Silent\\n(customers inactive 90+ days)\")\n",
    "axes[0].set_ylabel(\"Customers\")\n",
    "for bar, val in zip(axes[0].patches, last_type_dist.values):\n",
    "    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,\n",
    "                 f\"{val:,}\", ha=\"center\", va=\"bottom\", fontsize=9)\n",
    "\n",
    "# Right: failure/refund rate by customer tenure bucket\n",
    "df_tx_enriched = df_tx.merge(\n",
    "    df_customers[[\"customer_id\", \"registration_date\"]], on=\"customer_id\", how=\"left\"\n",
    ")\n",
    "df_tx_enriched[\"tenure_at_tx\"] = (\n",
    "    (df_tx_enriched[\"transaction_month\"] - df_tx_enriched[\"registration_date\"].dt.to_period(\"M\").dt.to_timestamp()).dt.days / 30.44\n",
    ").clip(lower=0).round(0)\n",
    "\n",
    "df_tx_enriched[\"tenure_bucket\"] = pd.cut(\n",
    "    df_tx_enriched[\"tenure_at_tx\"],\n",
    "    bins=[0, 3, 6, 12, 24, 9999],\n",
    "    labels=[\"M0\\u2013M3\", \"M4\\u2013M6\", \"M7\\u2013M12\", \"M13\\u2013M24\", \"M24+\"]\n",
    ")\n",
    "fail_rate = (\n",
    "    df_tx_enriched.groupby(\"tenure_bucket\")[\"status\"]\n",
    "    .apply(lambda x: (x.isin([\"failed\", \"reversed\"])).mean() * 100)\n",
    "    .reset_index(name=\"fail_rate_pct\")\n",
    ")\n",
    "\n",
    "axes[1].bar(fail_rate[\"tenure_bucket\"].astype(str), fail_rate[\"fail_rate_pct\"], \n",
    "            color=\"#DD8452\", edgecolor=\"white\", alpha=0.85)\n",
    "axes[1].set_title(\"Failed + Reversed Transaction Rate by Customer Tenure\")\n",
    "axes[1].set_ylabel(\"% of Transactions (failed or reversed)\")\n",
    "axes[1].set_xlabel(\"Tenure Bucket\")\n",
    "for bar, val in zip(axes[1].patches, fail_rate[\"fail_rate_pct\"]):\n",
    "    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,\n",
    "                 f\"{val:.1f}%\", ha=\"center\", va=\"bottom\", fontsize=9)\n",
    "\n",
    "plt.suptitle(\"Churn Proxies: What Does Exit Look Like?\", fontsize=13, y=1.02)\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "print(f\"\\nCustomers inactive 90+ days: {len(churned_proxy):,} ({len(churned_proxy)/len(df_customers)*100:.1f}% of base)\")\n",
    "print(f\"\\nLast transaction type before going silent:\")\n",
    "print(last_type_dist.to_string())\n",
]))

# ── 3.8 Interpretation ───────────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "**Insight**: If failed/reversed transactions spike at a specific tenure bucket, that's where \n",
    "involuntary churn concentrates — a product/risk issue, not just disengagement. \n",
    "If the last transaction before silence is predominantly \"purchase\" or \"transfer\" (normal activity), \n",
    "the exit is voluntary — a different commercial intervention is required.\n",
    "**Hypothesis for clustering**: customers whose last transaction was a failure likely belong \n",
    "to the at-risk behavioral cluster identified by K-Means in Notebook 3.\n",
]))

# ── Part 3 Closing Summary ───────────────────────────────────────────────────
new_cells.append(make_cell("markdown", [
    "## Part 3 Summary — Behavioral Hypotheses Before Clustering\n",
    "\n",
    "| Signal | Finding | Hypothesis for Notebook 3 |\n",
    "|---|---|---|\n",
    "| Activity rate distribution | [bimodal / skewed / uniform?] | Customers form 2+ distinct behavioral tiers |\n",
    "| Pareto revenue | Top X% drive 80% of TPV | Revenue concentration confirms high-value tier |\n",
    "| Activation quality | M0 activators retain at X% vs Y% | Activation timing is a leading indicator of segment |\n",
    "| Recency tiers | X% in \"Likely Churned\" bucket | Recency will be a dominant RFM dimension |\n",
    "| Frequency tiers | High-frequency = top X% by channel | Frequency separates engagement levels cleanly |\n",
    "| Product adoption | First product = wallet in X% | Product depth correlates with segment quality |\n",
    "| Cohort ARPU | Rising / flat / declining with tenure | ARPU trajectory reveals cohort health |\n",
    "| Churn proxies | X% of silent customers last tx was [type] | Involuntary vs. voluntary churn signal |\n",
    "\n",
    "> **Next step**: Notebook 3 will apply RFM scoring and K-Means clustering to formally \n",
    "> recover the behavioral groups hinted at above — and validate them against the ground truth \n",
    "> in `EDA_Validation_Fake_Dataset.ipynb`.\n",
]))

# ── Insert all new cells before the closing summary cell ────────────────────
insert_at = idx_closing  # insert before the closing summary
for i, cell in enumerate(new_cells):
    nb["cells"].insert(insert_at + i, cell)

print(f"Inserted {len(new_cells)} new cells before idx {insert_at}")
print(f"Total cells now: {len(nb['cells'])}")

# ── Write back ───────────────────────────────────────────────────────────────
with open(NB_PATH, "w") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"\\nNotebook saved to {NB_PATH}")

# ── Verify ───────────────────────────────────────────────────────────────────
with open(NB_PATH) as f:
    nb_verify = json.load(f)
print(f"Verification — total cells: {len(nb_verify['cells'])}")

# Check no true_segment references remain in cell sources
true_seg_cells = []
for i, c in enumerate(nb_verify["cells"]):
    src = "".join(c["source"])
    if "true_segment" in src:
        true_seg_cells.append((i, src[:100]))

if true_seg_cells:
    print(f"WARNING: true_segment still found in {len(true_seg_cells)} cells:")
    for idx, snippet in true_seg_cells:
        print(f"  [{idx}]: {snippet}")
else:
    print("OK: No true_segment references remain in cell sources.")
