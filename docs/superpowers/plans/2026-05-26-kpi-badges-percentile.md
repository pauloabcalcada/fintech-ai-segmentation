# KPI Badges — Percentile Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Drop 2 low-signal KPI badges, add 3 new metric badges, and surface population percentiles on 5 badges in the customer detail inline view.

**Architecture:** Backend adds `avg_ticket`, `avg_days_between_tx`, and 5 `PERCENT_RANK()` window fields to the customer profile SQL (via CTE so windows run over the full population before filtering). Frontend adds a `subvalue` prop to `KpiBadge`, rewires the badge row, and formats percentiles as `p{N} vs pop.`. Activity trend displays as `(ratio-1)/(ratio+1)` mapped to `[-1, 1]`.

**Tech Stack:** Python/Pydantic (backend schema), SQLAlchemy `text()` + PostgreSQL CTE/`PERCENT_RANK()` (SQL), React + TypeScript + react-i18next (frontend), Vitest + Testing Library (tests).

---

## File Map

| File | What changes |
|---|---|
| `src/fintech_ai_segmentation/app/schemas/customer.py` | Add 7 new optional fields to `CustomerProfile` |
| `src/fintech_ai_segmentation/app/repositories/customer.py` | Rewrite `_PROFILE_SQL` as CTE; add `avg_ticket`, `avg_days_between_tx`, 5 `PERCENT_RANK()` windows; map new fields in row constructor |
| `frontend/src/lib/api.ts` | Add 8 new optional fields to `CustomerProfile` TypeScript interface |
| `frontend/src/i18n/en.json` | Remove 4 dropped keys; add 9 new keys |
| `frontend/src/i18n/pt-BR.json` | Same removals and additions in Portuguese |
| `frontend/src/components/CustomerDetailInline.tsx` | Add `subvalue` prop to `KpiBadge`; drop 2 badges; add 3 new badges; wire percentile subvalues; transform activity trend |
| `frontend/src/components/CustomerDetailInline.test.tsx` | Update fixture; update/add assertions for all badge changes |

---

## Task 1: Backend schema — add 7 new fields

**Files:**
- Modify: `src/fintech_ai_segmentation/app/schemas/customer.py:77-78`

- [ ] **Step 1: Add fields to `CustomerProfile`**

Open `src/fintech_ai_segmentation/app/schemas/customer.py`. Replace the last two lines of `CustomerProfile`:

```python
    activity_trend_ratio: float | None = None
    early_window_freq_ratio: float | None = None
```

with:

```python
    activity_trend_ratio: float | None = None
    early_window_freq_ratio: float | None = None
    avg_ticket: float | None = None
    avg_days_between_tx: float | None = None
    activity_trend_percentile: float | None = None
    acquisition_cost_percentile: float | None = None
    recency_percentile: float | None = None
    avg_ticket_percentile: float | None = None
    avg_days_between_tx_percentile: float | None = None
```

- [ ] **Step 2: Verify Pydantic parses correctly**

```bash
cd /Users/paulocalcada/Documents/GitHub/Fintech_AI_Segmentation
source .venv/bin/activate
python -c "
from src.fintech_ai_segmentation.app.schemas.customer import CustomerProfile
import uuid
p = CustomerProfile(
    customer_id=uuid.uuid4(), name='X', email='x@x.com', age=30, state='SP',
    acquisition_channel='organic', acquisition_cost=100.0,
    registration_date='2023-01-01', tenure_months=12,
    cluster_name=None, lifecycle_stage=None, rfm_score=None,
    recency_score=None, frequency_score=None, monetary_score=None,
    recency_days=None, products_owned_count=0,
    has_wallet=False, has_credit_card=False, has_investment=False,
    has_insurance=False, has_loan=False,
    cluster_position=None, cluster_averages=None,
    population_averages=None, cluster_product_profile=None,
)
print('avg_ticket:', p.avg_ticket)
print('activity_trend_percentile:', p.activity_trend_percentile)
print('OK')
"
```

Expected output:
```
avg_ticket: None
activity_trend_percentile: None
OK
```

- [ ] **Step 3: Commit**

```bash
git add src/fintech_ai_segmentation/app/schemas/customer.py
git commit -m "feat: add avg_ticket, avg_days_between_tx, and 5 percentile fields to CustomerProfile schema"
```

---

## Task 2: Backend repository — CTE SQL + new field mapping

**Files:**
- Modify: `src/fintech_ai_segmentation/app/repositories/customer.py:26-67` (SQL) and `~:240-267` (mapping)

The current `_PROFILE_SQL` applies `WHERE customer_id = :customer_id` before window functions, which means `PERCENT_RANK()` operates over 1 row and always returns 0. The fix is a CTE: compute all windows over the full population, then filter in the outer SELECT.

- [ ] **Step 1: Replace `_PROFILE_SQL` with a CTE version**

In `src/fintech_ai_segmentation/app/repositories/customer.py`, replace the entire `_PROFILE_SQL = text("""...""")` block (lines 26–67) with:

```python
_PROFILE_SQL = text("""
    WITH full_pop AS (
        SELECT
            cr.customer_id,
            cr.name,
            cr.email,
            cr.age,
            cr.state,
            cr.acquisition_channel,
            cr.acquisition_cost,
            cr.registration_date,
            ca.tenure_months,
            ca.cluster_name,
            ca.lifecycle_stage,
            ca.rfm_score,
            ca.recency_score,
            ca.frequency_score,
            ca.monetary_score,
            ca.recency_days,
            ca.has_wallet,
            ca.has_credit_card,
            ca.has_investment,
            ca.has_insurance,
            ca.has_loan,
            ca.activity_trend_ratio,
            ca.early_window_freq_ratio,
            ca.avg_ticket,
            ca.avg_days_between_tx,
            (
                ca.has_wallet::int + ca.has_credit_card::int + ca.has_investment::int
                + ca.has_insurance::int + ca.has_loan::int
            ) AS products_owned_count,
            CASE
                WHEN PERCENT_RANK() OVER (
                    PARTITION BY ca.cluster_name ORDER BY ca.rfm_score
                ) <= 0.20 THEN 'bottom_20'
                WHEN PERCENT_RANK() OVER (
                    PARTITION BY ca.cluster_name ORDER BY ca.rfm_score
                ) >= 0.80 THEN 'top_20'
                ELSE 'mid_60'
            END AS cluster_position,
            PERCENT_RANK() OVER (
                ORDER BY ca.activity_trend_ratio ASC NULLS FIRST
            ) AS activity_trend_percentile,
            1.0 - PERCENT_RANK() OVER (
                ORDER BY ca.acquisition_cost ASC NULLS LAST
            ) AS acquisition_cost_percentile,
            1.0 - PERCENT_RANK() OVER (
                ORDER BY ca.recency_days ASC NULLS LAST
            ) AS recency_percentile,
            PERCENT_RANK() OVER (
                ORDER BY ca.avg_ticket ASC NULLS FIRST
            ) AS avg_ticket_percentile,
            1.0 - PERCENT_RANK() OVER (
                ORDER BY ca.avg_days_between_tx ASC NULLS LAST
            ) AS avg_days_between_tx_percentile
        FROM customer_analysis ca
        JOIN customers_raw cr ON cr.customer_id = ca.customer_id::uuid
    )
    SELECT * FROM full_pop WHERE customer_id = :customer_id
""")
```

- [ ] **Step 2: Map the 7 new fields in the row-to-model constructor**

In the same file, find the `CustomerProfile(...)` constructor call (around line 240). Add 7 new keyword arguments after `early_window_freq_ratio=...`:

```python
            activity_trend_ratio=float(row["activity_trend_ratio"]) if row["activity_trend_ratio"] is not None else None,
            early_window_freq_ratio=float(row["early_window_freq_ratio"]) if row["early_window_freq_ratio"] is not None else None,
            avg_ticket=float(row["avg_ticket"]) if row["avg_ticket"] is not None else None,
            avg_days_between_tx=float(row["avg_days_between_tx"]) if row["avg_days_between_tx"] is not None else None,
            activity_trend_percentile=float(row["activity_trend_percentile"]) if row["activity_trend_percentile"] is not None else None,
            acquisition_cost_percentile=float(row["acquisition_cost_percentile"]) if row["acquisition_cost_percentile"] is not None else None,
            recency_percentile=float(row["recency_percentile"]) if row["recency_percentile"] is not None else None,
            avg_ticket_percentile=float(row["avg_ticket_percentile"]) if row["avg_ticket_percentile"] is not None else None,
            avg_days_between_tx_percentile=float(row["avg_days_between_tx_percentile"]) if row["avg_days_between_tx_percentile"] is not None else None,
```

- [ ] **Step 3: Smoke-test against the running backend**

Start the backend:
```bash
PYTHONPATH=src .venv/bin/uvicorn fintech_ai_segmentation.app.main:app --reload
```

In a separate terminal, pick any customer UUID from the DB and call the endpoint:
```bash
curl -s "http://localhost:8000/customers/<any-uuid>" | python3 -m json.tool | grep -E "avg_ticket|avg_days|percentile"
```

Expected: 7 new fields appear with numeric values (not null, unless the mart row has nulls).

- [ ] **Step 4: Commit**

```bash
git add src/fintech_ai_segmentation/app/repositories/customer.py
git commit -m "feat: rewrite profile SQL as CTE; add avg_ticket, avg_days_between_tx, and 5 PERCENT_RANK population percentiles"
```

---

## Task 3: Frontend types + i18n

**Files:**
- Modify: `frontend/src/lib/api.ts:64-94`
- Modify: `frontend/src/i18n/en.json`
- Modify: `frontend/src/i18n/pt-BR.json`

- [ ] **Step 1: Add 8 new fields to `CustomerProfile` TypeScript interface**

In `frontend/src/lib/api.ts`, add after `early_window_freq_ratio: number | null;` (line 93):

```typescript
  avg_ticket: number | null;
  avg_days_between_tx: number | null;
  activity_trend_percentile: number | null;
  acquisition_cost_percentile: number | null;
  recency_percentile: number | null;
  avg_ticket_percentile: number | null;
  avg_days_between_tx_percentile: number | null;
```

- [ ] **Step 2: Update `en.json` KPI section**

In `frontend/src/i18n/en.json`, replace the entire `"kpi"` block inside `"customerDetail"`:

```json
    "kpi": {
      "rfmScore": "RFM Score",
      "rfmScoreTooltip": "Composite behavioral score (1–5) combining recency, frequency, and monetary signals. ≥ 4.0 = strong · 2.5–3.9 = moderate · < 2.5 = at risk.",
      "tenure": "Tenure",
      "tenureTooltip": "Months since registration. Longer tenure means deeper relationship history. No universal threshold.",
      "tenureValue": "{{months}} months",
      "lifecycle": "Lifecycle",
      "recencyDays": "Recency",
      "recencyDaysTooltip": "Days since last transaction. Lower is better — a customer active yesterday scores lower than one inactive for 90 days. Percentile is inverted: p95 means more recent than 95% of the population.",
      "avgTicket": "Avg Ticket",
      "avgTicketTooltip": "Average transaction value in BRL. Higher tickets indicate greater spending power. p95 means higher than 95% of the population.",
      "avgDaysBetweenTx": "Tx Frequency",
      "avgDaysBetweenTxTooltip": "Average days between transactions. Lower means more frequent engagement. Percentile is inverted: p95 means more frequent than 95% of the population.",
      "acquisitionCost": "Acq. Cost",
      "acquisitionCostTooltip": "R$ invested to acquire this customer. Lower is better for unit economics. High cost + low RFM = poor ROI. Percentile is inverted: p95 means lower cost than 95% of the population.",
      "activityTrend": "Activity Trend",
      "activityTrendTooltip": "Direction of engagement over the analysis window, scaled to [−1, +1]. +1 = strongly growing, 0 = stable, −1 = strongly declining. Percentile ranks this customer's trend vs the full population.",
      "percentileVsPop": "p{{n}} vs pop."
    },
```

- [ ] **Step 3: Update `pt-BR.json` KPI section**

In `frontend/src/i18n/pt-BR.json`, replace the entire `"kpi"` block inside `"customerDetail"`:

```json
    "kpi": {
      "rfmScore": "RFM Score",
      "rfmScoreTooltip": "Pontuação comportamental composta (1–5) combinando recência, frequência e valor monetário. ≥ 4,0 = forte · 2,5–3,9 = moderado · < 2,5 = em risco.",
      "tenure": "Tempo de Conta",
      "tenureTooltip": "Meses desde o cadastro. Maior tempo indica histórico de relacionamento mais profundo. Sem limite universal.",
      "tenureValue": "{{months}} meses",
      "lifecycle": "Ciclo de Vida",
      "recencyDays": "Recência",
      "recencyDaysTooltip": "Dias desde a última transação. Menor é melhor — cliente ativo ontem tem recência mais baixa que um inativo há 90 dias. Percentil invertido: p95 significa mais recente que 95% da população.",
      "avgTicket": "Ticket Médio",
      "avgTicketTooltip": "Valor médio por transação em BRL. Tickets maiores indicam maior poder de compra. p95 significa maior que 95% da população.",
      "avgDaysBetweenTx": "Freq. Transações",
      "avgDaysBetweenTxTooltip": "Média de dias entre transações. Menor significa engajamento mais frequente. Percentil invertido: p95 significa mais frequente que 95% da população.",
      "acquisitionCost": "Custo de Aquisição",
      "acquisitionCostTooltip": "R$ investido para adquirir este cliente. Menor é melhor para economia unitária. Custo alto + RFM baixo = ROI ruim. Percentil invertido: p95 significa custo menor que 95% da população.",
      "activityTrend": "Tendência de Atividade",
      "activityTrendTooltip": "Direção do engajamento na janela de análise, escalonada para [−1, +1]. +1 = crescendo fortemente, 0 = estável, −1 = declinando fortemente. O percentil compara a tendência deste cliente com toda a população.",
      "percentileVsPop": "p{{n}} vs pop."
    },
```

- [ ] **Step 4: Run the existing test suite to confirm i18n changes don't break anything**

```bash
cd /Users/paulocalcada/Documents/GitHub/Fintech_AI_Segmentation/frontend
npm run test 2>&1 | tail -6
```

Expected: most tests pass. Three tests will now fail because their label assertions reference dropped i18n keys — these are fixed in Task 5: `"renders Portuguese KPI badge labels when language is pt-BR"` (references `Posição no Segmento` and `Freq. Janela Inicial`), `"renders a tooltip trigger on the RFM Score badge"` label lookup, and the `"all 6 KPI badges render a tooltip trigger"` label list. This is expected — they are addressed in the TDD cycles.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/i18n/en.json frontend/src/i18n/pt-BR.json
git commit -m "feat: add percentile + new metric fields to frontend CustomerProfile type and i18n keys"
```

---

## Task 4 (TDD): KpiBadge — add `subvalue` prop

**Files:**
- Modify: `frontend/src/components/CustomerDetailInline.tsx:22-31`
- Modify: `frontend/src/components/CustomerDetailInline.test.tsx`

### Cycle 4-A: RED — subvalue renders below the main value

- [ ] **Step 1: Write the failing test**

In `frontend/src/components/CustomerDetailInline.test.tsx`, add a new `describe` block at the bottom of the outer `describe("CustomerDetailInline", ...)` block (before the final `});`):

```typescript
  // ---------------------------------------------------------------------------
  // Task 4 — KpiBadge subvalue prop
  // ---------------------------------------------------------------------------

  describe("KpiBadge subvalue", () => {
    it("renders subvalue text below the badge value when percentile data is present", async () => {
      mockFetchCustomerProfile.mockResolvedValueOnce({
        ...FIXTURE,
        data: {
          ...FIXTURE.data,
          recency_percentile: 0.83,
          avg_ticket: 150.5,
          avg_ticket_percentile: 0.65,
          avg_days_between_tx: 14.2,
          avg_days_between_tx_percentile: 0.78,
          activity_trend_percentile: 0.72,
          acquisition_cost_percentile: 0.45,
        },
      });
      renderInline();
      await screen.findByText("Ana Lima");
      // recency_percentile 0.83 → "p83 vs pop."
      expect(screen.getByText("p83 vs pop.")).toBeInTheDocument();
    });
  });
```

- [ ] **Step 2: Update FIXTURE to include new required fields**

The `FIXTURE` constant is missing the 7 new fields. Update it so `mockFetchCustomerProfile.mockResolvedValue(FIXTURE)` continues to satisfy the `CustomerProfile` type. Find the `const FIXTURE = { data: { ... } }` block and add inside `data`:

```typescript
    avg_ticket: 150.5,
    avg_days_between_tx: 14.2,
    activity_trend_percentile: 0.83,
    acquisition_cost_percentile: 0.72,
    recency_percentile: 0.91,
    avg_ticket_percentile: 0.65,
    avg_days_between_tx_percentile: 0.78,
```

- [ ] **Step 3: Run the test to confirm RED**

```bash
npm run test -- --reporter=verbose CustomerDetailInline 2>&1 | grep -E "FAIL|✗|renders subvalue"
```

Expected: `FAIL … renders subvalue text below the badge value when percentile data is present`

### Cycle 4-A: GREEN

- [ ] **Step 4: Add `subvalue` prop to `KpiBadge`**

In `frontend/src/components/CustomerDetailInline.tsx`, replace the `KpiBadge` function (lines 22–31):

```tsx
function KpiBadge({ label, value, tooltip, subvalue }: {
  label: string;
  value: string;
  tooltip?: string;
  subvalue?: string;
}) {
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-border bg-card px-4 py-3 min-w-[120px]">
      <span className="text-xs text-muted-foreground uppercase tracking-wide">
        {label}{tooltip && <InfoTooltip text={tooltip} />}
      </span>
      <span className="text-xl font-semibold text-foreground">{value}</span>
      {subvalue && (
        <span className="text-xs text-muted-foreground">{subvalue}</span>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Wire `subvalue` on the Recency badge (minimal to pass this test)**

Find the `<KpiBadge label={t("customerDetail.kpi.acquisitionCost")} .../>` badge in `CustomerDetailInline.tsx` and add a `subvalue` prop to any **one** badge that uses `recency_percentile`. This will come in the next task — for now the test uses a `recencyDays` badge that doesn't exist yet.

Wait — re-read the test: it checks for `"p83 vs pop."` which corresponds to `recency_percentile: 0.83`. The Recency Days badge does not exist yet, so the test will still fail even with the `subvalue` prop added. Revise the test to instead check a badge that already exists and has a percentile. Update the test to check `activity_trend_percentile: 0.72` on the Activity Trend badge (which already exists):

Replace the failing test with:

```typescript
    it("renders subvalue text below the badge value when percentile data is present", async () => {
      mockFetchCustomerProfile.mockResolvedValueOnce({
        ...FIXTURE,
        data: {
          ...FIXTURE.data,
          activity_trend_percentile: 0.72,
        },
      });
      renderInline();
      await screen.findByText("Ana Lima");
      // activity_trend_percentile 0.72 → "p72 vs pop."
      expect(screen.getByText("p72 vs pop.")).toBeInTheDocument();
    });
```

- [ ] **Step 6: Wire `subvalue` on the Activity Trend badge**

In `CustomerDetailInline.tsx`, find the Activity Trend `<KpiBadge>` and add:

```tsx
        <KpiBadge
          label={t("customerDetail.kpi.activityTrend")}
          value={
            profile.activity_trend_ratio != null
              ? ((profile.activity_trend_ratio - 1) / (profile.activity_trend_ratio + 1)).toFixed(2)
              : "—"
          }
          tooltip={t("customerDetail.kpi.activityTrendTooltip")}
          subvalue={
            profile.activity_trend_percentile != null
              ? t("customerDetail.kpi.percentileVsPop", { n: Math.round(profile.activity_trend_percentile * 100) })
              : undefined
          }
        />
```

- [ ] **Step 7: Run tests to confirm GREEN**

```bash
npm run test -- --reporter=verbose CustomerDetailInline 2>&1 | grep -E "✓|✗|Tests" | tail -6
```

Expected: 1 new test passes, all previous tests still pass.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/CustomerDetailInline.tsx frontend/src/components/CustomerDetailInline.test.tsx
git commit -m "feat: add subvalue prop to KpiBadge; wire activity_trend_percentile subvalue"
```

---

## Task 5 (TDD): CustomerDetailInline — drop badges, add new badges, wire all percentiles

**Files:**
- Modify: `frontend/src/components/CustomerDetailInline.tsx`
- Modify: `frontend/src/components/CustomerDetailInline.test.tsx`

### Cycle 5-A: Activity Trend shows transformed value (not raw ratio)

- [ ] **Step 1: Write the failing test**

Add inside the existing describe block:

```typescript
  describe("activity trend transformation", () => {
    it("displays activity_trend_ratio transformed to [-1,1] scale, not the raw ratio", async () => {
      mockFetchCustomerProfile.mockResolvedValueOnce({
        ...FIXTURE,
        data: { ...FIXTURE.data, activity_trend_ratio: 3.0 },
      });
      renderInline();
      await screen.findByText("Ana Lima");
      // (3 - 1) / (3 + 1) = 0.50
      expect(screen.getByText("0.50")).toBeInTheDocument();
      // raw value "3.00" must NOT appear in the badge area
      expect(screen.queryByText("3.00")).not.toBeInTheDocument();
    });
  });
```

- [ ] **Step 2: Run to confirm RED**

```bash
npm run test -- --reporter=verbose CustomerDetailInline 2>&1 | grep -E "FAIL|activity trend transformation"
```

Expected: FAIL — currently renders "3.00" (raw ratio).

- [ ] **Step 3: The transformation is already wired from Task 4 Step 6 — run to confirm GREEN**

```bash
npm run test -- --reporter=verbose CustomerDetailInline 2>&1 | grep -E "✓|activity trend transformation"
```

If the Activity Trend badge was updated in Task 4, this should already pass. If not, apply the value formula from Task 4 Step 6.

---

### Cycle 5-B: Drop `cluster_rank` and `early_window_freq_ratio` badges

- [ ] **Step 1: Write the failing test**

```typescript
  describe("dropped badges", () => {
    it("does not render a Cluster Rank badge", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      expect(screen.queryByText("Cluster Rank")).not.toBeInTheDocument();
    });

    it("does not render an Early Freq. Ratio badge", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      expect(screen.queryByText("Early Freq. Ratio")).not.toBeInTheDocument();
    });
  });
```

- [ ] **Step 2: Run to confirm RED**

```bash
npm run test -- --reporter=verbose CustomerDetailInline 2>&1 | grep -E "FAIL|dropped badges"
```

Expected: FAIL — both badges currently exist.

- [ ] **Step 3: Remove the two badges and the `clusterPositionLabel` helper from `CustomerDetailInline.tsx`**

Delete the two `<KpiBadge>` blocks:

```tsx
// DELETE this entire KpiBadge block:
        <KpiBadge
          label={t("customerDetail.kpi.clusterRank")}
          value={clusterPositionLabel(profile.cluster_position)}
          tooltip={t("customerDetail.kpi.clusterRankTooltip")}
        />

// DELETE this entire KpiBadge block:
        <KpiBadge
          label={t("customerDetail.kpi.earlyWindowFreq")}
          value={profile.early_window_freq_ratio?.toFixed(2) ?? "—"}
          tooltip={t("customerDetail.kpi.earlyWindowFreqTooltip")}
        />
```

Also delete the `clusterPositionLabel` function (around line 107) — it is only used by the removed badge:

```tsx
// DELETE this entire function:
function clusterPositionLabel(pos: CustomerProfile["cluster_position"]) {
  ...
}
```

- [ ] **Step 4: Run tests to confirm GREEN**

```bash
npm run test -- --reporter=verbose CustomerDetailInline 2>&1 | grep -E "✓|✗|Tests" | tail -6
```

Expected: 2 new tests pass, existing tests still pass (the existing "Top 20%" assertion will now FAIL — fix it in the next step by removing it).

- [ ] **Step 5: Remove stale assertions**

In `CustomerDetailInline.test.tsx`, find and delete the assertion:
```typescript
    expect(screen.getByText("Top 20%")).toBeInTheDocument();
```
(part of the `"renders KPI badges for rfm_score, cluster_rank, and tenure"` test). Update that test description to `"renders KPI badges for rfm_score and tenure"` and remove the `"Top 20%"` line.

Also update the `"renders exactly 6 tooltip triggers"` test: change `toHaveLength(6)` to `toHaveLength(4)` (dropped 2 from 6; 3 new badges not yet added — will become 7 after Task 5-C).

Also delete or update the `"does not render a lifecycle KPI badge"` test if needed — check whether it still makes sense.

- [ ] **Step 6: Run tests to confirm all pass**

```bash
npm run test -- --reporter=verbose CustomerDetailInline 2>&1 | tail -6
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/CustomerDetailInline.tsx frontend/src/components/CustomerDetailInline.test.tsx
git commit -m "feat: drop cluster_rank and early_window_freq_ratio KPI badges"
```

---

### Cycle 5-C: Add `recency_days`, `avg_ticket`, `avg_days_between_tx` badges with percentiles

- [ ] **Step 1: Write the failing tests**

```typescript
  describe("new metric badges", () => {
    it("renders Recency badge with value and percentile subvalue", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      // FIXTURE has recency_days: 7
      expect(screen.getByText("7 days")).toBeInTheDocument();
      // FIXTURE has recency_percentile: 0.91 → p91
      expect(screen.getByText("p91 vs pop.")).toBeInTheDocument();
    });

    it("renders Avg Ticket badge with value and percentile subvalue", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      // FIXTURE has avg_ticket: 150.5
      expect(screen.getByText("R$ 151")).toBeInTheDocument();
      // FIXTURE has avg_ticket_percentile: 0.65 → p65
      expect(screen.getByText("p65 vs pop.")).toBeInTheDocument();
    });

    it("renders Tx Frequency badge with value and percentile subvalue", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      // FIXTURE has avg_days_between_tx: 14.2
      expect(screen.getByText("14.2 days")).toBeInTheDocument();
      // FIXTURE has avg_days_between_tx_percentile: 0.78 → p78
      expect(screen.getByText("p78 vs pop.")).toBeInTheDocument();
    });
  });
```

- [ ] **Step 2: Run to confirm RED**

```bash
npm run test -- --reporter=verbose CustomerDetailInline 2>&1 | grep -E "FAIL|new metric badges"
```

Expected: 3 FAILs.

- [ ] **Step 3: Add 3 new `<KpiBadge>` blocks to `CustomerDetailInline.tsx`**

Insert after the Tenure badge and before the Activity Trend badge:

```tsx
        <KpiBadge
          label={t("customerDetail.kpi.recencyDays")}
          value={profile.recency_days != null ? `${profile.recency_days} days` : "—"}
          tooltip={t("customerDetail.kpi.recencyDaysTooltip")}
          subvalue={
            profile.recency_percentile != null
              ? t("customerDetail.kpi.percentileVsPop", { n: Math.round(profile.recency_percentile * 100) })
              : undefined
          }
        />
        <KpiBadge
          label={t("customerDetail.kpi.avgTicket")}
          value={profile.avg_ticket != null ? `R$ ${Math.round(profile.avg_ticket)}` : "—"}
          tooltip={t("customerDetail.kpi.avgTicketTooltip")}
          subvalue={
            profile.avg_ticket_percentile != null
              ? t("customerDetail.kpi.percentileVsPop", { n: Math.round(profile.avg_ticket_percentile * 100) })
              : undefined
          }
        />
        <KpiBadge
          label={t("customerDetail.kpi.avgDaysBetweenTx")}
          value={profile.avg_days_between_tx != null ? `${profile.avg_days_between_tx.toFixed(1)} days` : "—"}
          tooltip={t("customerDetail.kpi.avgDaysBetweenTxTooltip")}
          subvalue={
            profile.avg_days_between_tx_percentile != null
              ? t("customerDetail.kpi.percentileVsPop", { n: Math.round(profile.avg_days_between_tx_percentile * 100) })
              : undefined
          }
        />
```

- [ ] **Step 4: Run tests to confirm GREEN**

```bash
npm run test -- --reporter=verbose CustomerDetailInline 2>&1 | tail -6
```

Expected: all tests pass.

- [ ] **Step 5: Update tooltip trigger count test**

Find `expect(screen.getAllByTestId("info-tooltip-trigger")).toHaveLength(5)` (set in cycle 5-B) and change to `toHaveLength(7)` (5 − 0 + 3 new = 7; RFM + Tenure + Recency + AvgTicket + TxFreq + ActivityTrend + AcqCost = 7).

Also update the `"all 6 KPI badges render a tooltip trigger"` test: change its label list to:
```typescript
      const labels = [
        "RFM Score",
        "Tenure",
        "Recency",
        "Avg Ticket",
        "Tx Frequency",
        "Activity Trend",
        "Acq. Cost",
      ];
```
and update its description to `"all 7 KPI badges render a tooltip trigger"`.

- [ ] **Step 6: Run full test suite**

```bash
npm run test 2>&1 | tail -6
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/CustomerDetailInline.tsx frontend/src/components/CustomerDetailInline.test.tsx
git commit -m "feat: add recency_days, avg_ticket, avg_days_between_tx KPI badges with population percentiles"
```

---

### Cycle 5-D: Wire `acquisition_cost_percentile` subvalue

- [ ] **Step 1: Write the failing test**

```typescript
  describe("acquisition cost percentile", () => {
    it("renders acquisition cost with percentile subvalue", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      // FIXTURE has acquisition_cost: 240, acquisition_cost_percentile: 0.72 → p72
      expect(screen.getByText("R$ 240")).toBeInTheDocument();
      expect(screen.getByText("p72 vs pop.")).toBeInTheDocument();
    });
  });
```

- [ ] **Step 2: Run to confirm RED**

```bash
npm run test -- --reporter=verbose CustomerDetailInline 2>&1 | grep -E "FAIL|acquisition cost percentile"
```

- [ ] **Step 3: Add `subvalue` to the Acquisition Cost badge in `CustomerDetailInline.tsx`**

```tsx
        <KpiBadge
          label={t("customerDetail.kpi.acquisitionCost")}
          value={profile.acquisition_cost != null ? `R$ ${Math.round(profile.acquisition_cost)}` : "—"}
          tooltip={t("customerDetail.kpi.acquisitionCostTooltip")}
          subvalue={
            profile.acquisition_cost_percentile != null
              ? t("customerDetail.kpi.percentileVsPop", { n: Math.round(profile.acquisition_cost_percentile * 100) })
              : undefined
          }
        />
```

- [ ] **Step 4: Run to confirm GREEN**

```bash
npm run test -- --reporter=verbose CustomerDetailInline 2>&1 | tail -6
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/CustomerDetailInline.tsx frontend/src/components/CustomerDetailInline.test.tsx
git commit -m "feat: add acquisition_cost_percentile subvalue to Acq. Cost KPI badge"
```

---

### Cycle 5-E: pt-BR labels for new badges

- [ ] **Step 1: Write the failing test**

```typescript
  describe("pt-BR new badge labels", () => {
    it("renders Portuguese labels for the three new badges", async () => {
      renderInline("pt-BR");
      await screen.findByText("Ana Lima");
      expect(screen.getByText("Recência")).toBeInTheDocument();
      expect(screen.getByText("Ticket Médio")).toBeInTheDocument();
      expect(screen.getByText("Freq. Transações")).toBeInTheDocument();
    });
  });
```

- [ ] **Step 2: Run to confirm RED**

```bash
npm run test -- --reporter=verbose CustomerDetailInline 2>&1 | grep -E "FAIL|pt-BR new badge"
```

- [ ] **Step 3: Confirm GREEN (i18n keys already added in Task 3)**

The Portuguese keys were added in Task 3. This test should pass without any code change.

```bash
npm run test -- --reporter=verbose CustomerDetailInline 2>&1 | grep -E "✓|pt-BR new badge"
```

If it fails, verify `frontend/src/i18n/pt-BR.json` contains `"recencyDays": "Recência"`, `"avgTicket": "Ticket Médio"`, `"avgDaysBetweenTx": "Freq. Transações"`.

- [ ] **Step 4: Update existing pt-BR test**

Find the test `"renders Portuguese KPI badge labels when language is pt-BR"` and remove assertions for `Posição no Segmento` and `Freq. Janela Inicial` (dropped badges). Add assertions for the 3 new labels and update the description:

```typescript
  it("renders Portuguese KPI badge labels when language is pt-BR", async () => {
    renderInline("pt-BR");
    await screen.findByText("Ana Lima");
    expect(screen.getByText("Tempo de Conta")).toBeInTheDocument();
    expect(screen.getByText("Custo de Aquisição")).toBeInTheDocument();
    expect(screen.getByText("Tendência de Atividade")).toBeInTheDocument();
    expect(screen.getByText("Recência")).toBeInTheDocument();
    expect(screen.getByText("Ticket Médio")).toBeInTheDocument();
    expect(screen.getByText("Freq. Transações")).toBeInTheDocument();
  });
```

- [ ] **Step 5: Run full test suite**

```bash
npm run test 2>&1 | tail -6
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/CustomerDetailInline.test.tsx
git commit -m "test: update pt-BR badge label assertions for redesigned KPI row"
```

---

## Task 6: Final smoke test and cleanup

- [ ] **Step 1: Run the full test suite one last time**

```bash
cd /Users/paulocalcada/Documents/GitHub/Fintech_AI_Segmentation/frontend
npm run test 2>&1 | tail -8
```

Expected: all test files pass, 0 failures.

- [ ] **Step 2: Start the full stack and visually verify the badge row**

```bash
# Terminal 1 — backend
PYTHONPATH=src .venv/bin/uvicorn fintech_ai_segmentation.app.main:app --reload

# Terminal 2 — frontend
npm --prefix frontend run dev
```

Open `http://localhost:5173/customers`, expand any customer row, and verify:
- 7 badges appear in order: RFM Score · Tenure · Recency · Avg Ticket · Tx Frequency · Activity Trend · Acq. Cost
- Activity Trend shows a value between −1 and +1
- 5 badges show a `p{N} vs pop.` subvalue
- No "Cluster Rank" or "Early Freq. Ratio" badge is present
- Each badge has an ⓘ tooltip trigger

- [ ] **Step 3: Final commit (if any cleanup edits were made)**

```bash
git add -p  # stage only intentional changes
git commit -m "chore: final cleanup after KPI badge percentile redesign"
```
