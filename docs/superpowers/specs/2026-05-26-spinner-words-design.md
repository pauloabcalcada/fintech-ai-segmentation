# SpinnerWords Loading Animation — Design Spec

**Date:** 2026-05-26
**Status:** Approved

---

## Problem

When a user clicks a customer row in the Customers page, `CustomerDetailInline` fetches the profile and currently displays plain `<Skeleton>` blocks. There is no contextual feedback about what is happening, and the experience is flat.

## Goal

Replace the skeleton loading state with a cycling text spinner (braille dots + rotating domain-themed phrases), matching the style Claude Code uses. Supports English and PT-BR automatically via the existing `react-i18next` setup.

---

## Component: `SpinnerWords`

**File:** `frontend/src/components/SpinnerWords.tsx`

### Behaviour

- Reads the current language from `useTranslation`.
- Picks phrase list from `t("customers.loadingPhrases", { returnObjects: true })` — a JSON array.
- Starts at a random phrase index so simultaneous expanded rows are not in sync.
- Two independent `useEffect` intervals:
  - **Dot frame:** advances every 80ms through `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏` (10 braille frames).
  - **Phrase:** advances every 700ms through the phrase array (wraps around).
- Both intervals cleared on unmount.
- Renders a single centered line: `⠹ Calculating RFM score…`

### Props

None. The component is self-contained and language-aware.

### Visual output

```
⠹ Calculating RFM score…
```

Styled: `text-sm text-muted-foreground font-mono`, centered, inside a `p-6` wrapper with `data-testid="customer-detail-inline-loading"` preserved so existing tests pass.

---

## i18n additions

### `customers.loadingPhrases` — English (`en.json`)

```json
"loadingPhrases": [
  "Reading transactions…",
  "Calculating RFM score…",
  "Checking churn signals…",
  "Scoring recency…",
  "Fetching product ownership…",
  "Ranking vs. population…",
  "Mapping activity trend…",
  "Measuring frequency…",
  "Loading customer profile…",
  "Analysing monetary value…"
]
```

### `customers.loadingPhrases` — PT-BR (`pt-BR.json`)

```json
"loadingPhrases": [
  "Lendo transações…",
  "Calculando pontuação RFM…",
  "Verificando sinais de churn…",
  "Pontuando recência…",
  "Buscando produtos do cliente…",
  "Classificando vs. população…",
  "Mapeando tendência de atividade…",
  "Medindo frequência…",
  "Carregando perfil do cliente…",
  "Analisando valor monetário…"
]
```

---

## Integration

**File:** `frontend/src/components/CustomerDetailInline.tsx`

Replace the `if (loading)` branch (currently lines 160–174, returning skeleton blocks) with:

```tsx
if (loading) {
  return <SpinnerWords />;
}
```

The `data-testid="customer-detail-inline-loading"` attribute moves inside `SpinnerWords` so existing tests that check for the loading state continue to pass.

---

## Scope — what does NOT change

| Area | Reason |
|---|---|
| AI panel `"Analyzing…"` text | Separate loading state, separate concern |
| Page-level `SkeletonRows` in `CustomersPage` | Table initial load, not row expansion |
| Any test checking `data-testid="customer-detail-inline-loading"` | Attribute preserved inside `SpinnerWords` |

---

## Files changed

| File | Change |
|---|---|
| `frontend/src/components/SpinnerWords.tsx` | New file |
| `frontend/src/components/CustomerDetailInline.tsx` | Replace skeleton loading branch |
| `frontend/src/i18n/en.json` | Add `customers.loadingPhrases` array |
| `frontend/src/i18n/pt-BR.json` | Add `customers.loadingPhrases` array |
