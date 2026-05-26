# KPI Badges — Percentile Redesign

**Date:** 2026-05-26
**Status:** Approved

## Summary

Redesign the customer detail inline badge row: drop two low-signal badges (`cluster_rank`, `early_window_freq_ratio`), add three new metric badges (`recency_days`, `avg_ticket`, `avg_days_between_tx`), and surface population percentiles on five badges so business users can immediately interpret where a customer stands relative to the full 8,000-customer population.

---

## Section 1 — Badge Row

Final 7 badges in order:

| Badge | Source field | Change | Percentile |
|---|---|---|---|
| RFM Score | `rfm_score` | unchanged | — |
| Tenure | `tenure_months` | unchanged | — |
| Recency Days | `recency_days` | **new** | `recency_percentile` (inverted: lower days = better) |
| Avg Ticket | `avg_ticket` | **new** | `avg_ticket_percentile` (raw: higher = better) |
| Avg Days Between Tx | `avg_days_between_tx` | **new** | `avg_days_between_tx_percentile` (inverted: lower = better) |
| Activity Trend | `activity_trend_ratio` | keep, transform + add percentile | `activity_trend_percentile` (raw: higher = better) |
| Acquisition Cost | `acquisition_cost` | keep, add percentile | `acquisition_cost_percentile` (inverted: lower cost = better) |

**Dropped:** `cluster_position` (Cluster Rank), `early_window_freq_ratio` (Early Freq. Ratio).

### Activity Trend transformation

The raw `activity_trend_ratio` is right-skewed and unbounded (e.g., 694). Display uses the transformation `(ratio - 1) / (ratio + 1)`, which maps `[0, ∞]` to `[-1, 1]` continuously:

- `ratio = 0` → `-1.00` (fully declining)
- `ratio = 1` → `0.00` (stable)
- `ratio = 694` → `≈ +1.00` (strongly growing)

Computed in the frontend from the stored raw ratio. No new backend field.

---

## Section 2 — Percentile Computation

All percentiles computed via `PERCENT_RANK()` window functions added to the existing detail SQL query in `src/fintech_ai_segmentation/app/repositories/customer.py`, alongside the existing `cluster_position` window.

"Inverted" metrics use `1 - PERCENT_RANK()` so every percentile field means **"better than N% of the population"** regardless of metric direction:

| Schema field | SQL expression |
|---|---|
| `activity_trend_percentile` | `PERCENT_RANK() OVER (ORDER BY activity_trend_ratio ASC)` |
| `acquisition_cost_percentile` | `1 - PERCENT_RANK() OVER (ORDER BY acquisition_cost ASC)` |
| `recency_percentile` | `1 - PERCENT_RANK() OVER (ORDER BY recency_days ASC)` |
| `avg_ticket_percentile` | `PERCENT_RANK() OVER (ORDER BY avg_ticket ASC)` |
| `avg_days_between_tx_percentile` | `1 - PERCENT_RANK() OVER (ORDER BY avg_days_between_tx ASC)` |

All return `float` in `[0, 1]`. Formatted frontend-side as `p{N}` where `N = Math.round(percentile * 100)`.

---

## Section 3 — KpiBadge Component

Add optional `subvalue?: string` prop to `KpiBadge`. Rendered as a small muted line below the main value:

```
ACTIVITY TREND ⓘ
0.72
p83 vs pop.
```

`subvalue` is built at the call site:
```tsx
subvalue={percentile != null ? t("customerDetail.kpi.percentileVsPop", { n: Math.round(percentile * 100) }) : undefined}
```

No changes to `InfoTooltip` or its trigger position.

---

## Section 4 — Schema & API

### Backend additions (`schemas/customer.py`)

Seven new optional fields on `CustomerProfile`:
```python
avg_ticket: float | None = None
avg_days_between_tx: float | None = None
activity_trend_percentile: float | None = None
acquisition_cost_percentile: float | None = None
recency_percentile: float | None = None
avg_ticket_percentile: float | None = None
avg_days_between_tx_percentile: float | None = None
```

Note: `recency_days` is already in the schema and fetched. `avg_ticket` and `avg_days_between_tx` are in the mart but not yet in the schema or SQL select.

### Repository (`repositories/customer.py`)

- Add 5 `PERCENT_RANK()` expressions to the detail SQL
- Map all 8 new fields in the row-to-model conversion

### Frontend (`lib/api.ts`)

Same 8 fields added to the `CustomerProfile` TypeScript type.

No new endpoints. All data flows through the existing `GET /customers/{id}` response.

---

## Section 5 — i18n & Tests

### i18n (`en.json` / `pt-BR.json`)

**Remove:**
- `customerDetail.kpi.clusterRank` + `clusterRankTooltip`
- `customerDetail.kpi.earlyWindowFreq` + `earlyWindowFreqTooltip`

**Add:**
- `customerDetail.kpi.recencyDays` — label
- `customerDetail.kpi.recencyDaysTooltip` — explain days since last transaction; lower = more recent; percentile = better than N% of population
- `customerDetail.kpi.avgTicket` — label
- `customerDetail.kpi.avgTicketTooltip` — explain average transaction value; higher = better
- `customerDetail.kpi.avgDaysBetweenTx` — label
- `customerDetail.kpi.avgDaysBetweenTxTooltip` — explain average gap between transactions; lower = more frequent; percentile inverted
- `customerDetail.kpi.activityTrendTooltip` — updated to explain [-1, 1] scale (stable at 0, growing toward +1, declining toward -1) + percentile meaning
- `customerDetail.kpi.percentileVsPop` — `"p{{n}} vs pop."` (same in both languages)

### Tests (`CustomerDetailInline.test.tsx`)

**Fixture updates:**
- Add fields: `recency_days`, `avg_ticket`, `avg_days_between_tx`, plus 5 percentile fields

**Removed assertions:**
- `cluster_position` badge
- `early_window_freq_ratio` badge

**New assertions:**
- 3 new badge values render (`recency_days`, `avg_ticket`, `avg_days_between_tx`)
- Activity trend displays transformed value (not raw ratio)
- Percentile subvalues render in `p{N} vs pop.` format for each of the 5 percentile badges
- Tooltip trigger count updated: 7 (was 6, dropped 2, added 3)
- pt-BR test updated for new/removed label keys
