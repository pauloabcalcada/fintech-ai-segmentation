# SpinnerWords Loading Animation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the skeleton loading state in `CustomerDetailInline` with a braille-dot spinner that cycles through domain-themed phrases in both English and PT-BR.

**Architecture:** A new `SpinnerWords` component reads the phrase list from i18n (`customers.loadingPhrases`), advances a phrase index every 700ms and a dot-frame index every 80ms via two independent `useEffect` intervals, and renders a single centered line. `CustomerDetailInline`'s `if (loading)` branch is swapped to render `<SpinnerWords />` instead of the skeleton blocks.

**Tech Stack:** React 18, react-i18next (already installed), Vitest + Testing Library (already installed)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `frontend/src/i18n/en.json` | Modify | Add `customers.loadingPhrases` array (EN) |
| `frontend/src/i18n/pt-BR.json` | Modify | Add `customers.loadingPhrases` array (PT-BR) |
| `frontend/src/components/SpinnerWords.tsx` | Create | Self-contained spinner component |
| `frontend/src/components/SpinnerWords.test.tsx` | Create | Unit tests for `SpinnerWords` |
| `frontend/src/components/CustomerDetailInline.tsx` | Modify | Swap skeleton loading branch for `<SpinnerWords />` |

---

## Task 1: Add `loadingPhrases` to both translation files

**Files:**
- Modify: `frontend/src/i18n/en.json`
- Modify: `frontend/src/i18n/pt-BR.json`

- [ ] **Step 1: Add the EN phrase array**

In `frontend/src/i18n/en.json`, inside the `"customers"` object, add after `"loading": "Loading…",`:

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
],
```

- [ ] **Step 2: Add the PT-BR phrase array**

In `frontend/src/i18n/pt-BR.json`, inside the `"customers"` object, add after `"loading": "Carregando…",`:

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
],
```

- [ ] **Step 3: Verify JSON is valid**

```bash
node -e "require('./frontend/src/i18n/en.json'); require('./frontend/src/i18n/pt-BR.json'); console.log('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/i18n/en.json frontend/src/i18n/pt-BR.json
git commit -m "feat: add loadingPhrases i18n arrays for SpinnerWords (EN + PT-BR)"
```

---

## Task 2: Create `SpinnerWords` with failing tests first

**Files:**
- Create: `frontend/src/components/SpinnerWords.test.tsx`
- Create: `frontend/src/components/SpinnerWords.tsx`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/components/SpinnerWords.test.tsx`:

```tsx
import { render, screen, act } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { I18nextProvider } from "react-i18next";
import { createTestI18n } from "@/i18n/test-utils";
import { SpinnerWords } from "@/components/SpinnerWords";

function renderSpinner(lng = "en") {
  const i18n = createTestI18n(lng);
  return render(
    <I18nextProvider i18n={i18n}>
      <SpinnerWords />
    </I18nextProvider>
  );
}

describe("SpinnerWords", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders with data-testid customer-detail-inline-loading", () => {
    renderSpinner();
    expect(
      screen.getByTestId("customer-detail-inline-loading")
    ).toBeInTheDocument();
  });

  it("renders a braille dot character on mount", () => {
    renderSpinner();
    const container = screen.getByTestId("customer-detail-inline-loading");
    const BRAILLE = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏";
    const text = container.textContent ?? "";
    const hasDot = [...BRAILLE].some((dot) => text.includes(dot));
    expect(hasDot).toBe(true);
  });

  it("renders a phrase from the EN list on mount", () => {
    renderSpinner("en");
    const container = screen.getByTestId("customer-detail-inline-loading");
    const EN_PHRASES = [
      "Reading transactions…",
      "Calculating RFM score…",
      "Checking churn signals…",
      "Scoring recency…",
      "Fetching product ownership…",
      "Ranking vs. population…",
      "Mapping activity trend…",
      "Measuring frequency…",
      "Loading customer profile…",
      "Analysing monetary value…",
    ];
    const text = container.textContent ?? "";
    const hasPhrase = EN_PHRASES.some((p) => text.includes(p));
    expect(hasPhrase).toBe(true);
  });

  it("renders a phrase from the PT-BR list when language is pt-BR", () => {
    renderSpinner("pt-BR");
    const container = screen.getByTestId("customer-detail-inline-loading");
    const PT_PHRASES = [
      "Lendo transações…",
      "Calculando pontuação RFM…",
      "Verificando sinais de churn…",
      "Pontuando recência…",
      "Buscando produtos do cliente…",
      "Classificando vs. população…",
      "Mapeando tendência de atividade…",
      "Medindo frequência…",
      "Carregando perfil do cliente…",
      "Analisando valor monetário…",
    ];
    const text = container.textContent ?? "";
    const hasPhrase = PT_PHRASES.some((p) => text.includes(p));
    expect(hasPhrase).toBe(true);
  });

  it("advances to the next phrase after 700ms", () => {
    // Pin Math.random to fix starting index at 0
    vi.spyOn(Math, "random").mockReturnValue(0);
    renderSpinner("en");

    const before = screen.getByTestId("customer-detail-inline-loading").textContent ?? "";

    act(() => {
      vi.advanceTimersByTime(700);
    });

    const after = screen.getByTestId("customer-detail-inline-loading").textContent ?? "";
    // Phrase should have changed (index 0 → 1)
    expect(after).not.toBe(before);

    vi.spyOn(Math, "random").mockRestore();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
npm --prefix frontend run test -- --run SpinnerWords
```

Expected: FAIL — `SpinnerWords` not found / not exported.

- [ ] **Step 3: Create `SpinnerWords.tsx`**

Create `frontend/src/components/SpinnerWords.tsx`:

```tsx
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

const DOTS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

export function SpinnerWords() {
  const { t } = useTranslation();
  const phrases = t("customers.loadingPhrases", { returnObjects: true }) as string[];

  const [phraseIdx, setPhraseIdx] = useState(
    () => Math.floor(Math.random() * phrases.length)
  );
  const [dotIdx, setDotIdx] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setPhraseIdx((i) => (i + 1) % phrases.length);
    }, 700);
    return () => clearInterval(id);
  }, [phrases.length]);

  useEffect(() => {
    const id = setInterval(() => {
      setDotIdx((i) => (i + 1) % DOTS.length);
    }, 80);
    return () => clearInterval(id);
  }, []);

  return (
    <div
      className="p-6 flex items-center justify-center min-h-[120px]"
      data-testid="customer-detail-inline-loading"
    >
      <span className="text-sm text-muted-foreground font-mono">
        {DOTS[dotIdx]} {phrases[phraseIdx]}
      </span>
    </div>
  );
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
npm --prefix frontend run test -- --run SpinnerWords
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/SpinnerWords.tsx frontend/src/components/SpinnerWords.test.tsx
git commit -m "feat: add SpinnerWords cycling-phrase loading component"
```

---

## Task 3: Wire `SpinnerWords` into `CustomerDetailInline`

**Files:**
- Modify: `frontend/src/components/CustomerDetailInline.tsx`

- [ ] **Step 1: Verify the existing loading test still references `data-testid`**

The test at `CustomerDetailInline.test.tsx:139` asserts:

```ts
expect(screen.getByTestId("customer-detail-inline-loading")).toBeInTheDocument();
```

`SpinnerWords` already carries that `data-testid`, so the test will continue to pass after the swap.

- [ ] **Step 2: Add the import and replace the loading branch**

At the top of `frontend/src/components/CustomerDetailInline.tsx`, add the import after existing imports:

```tsx
import { SpinnerWords } from "@/components/SpinnerWords";
```

Then find the `if (loading)` block (currently around line 160–174):

```tsx
  if (loading) {
    return (
      <div
        className="p-6 flex flex-col gap-4"
        data-testid="customer-detail-inline-loading"
      >
        <Skeleton className="h-24 rounded-lg" />
        <div className="flex gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-32 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }
```

Replace it with:

```tsx
  if (loading) {
    return <SpinnerWords />;
  }
```

- [ ] **Step 3: Remove the now-unused `Skeleton` import if it is no longer referenced**

Check the file for any remaining `<Skeleton` usage. If none remain, remove the import line:

```tsx
import { Skeleton } from "@/components/ui/skeleton";
```

- [ ] **Step 4: Run the full `CustomerDetailInline` test suite**

```bash
npm --prefix frontend run test -- --run CustomerDetailInline
```

Expected: all existing tests PASS (the `data-testid` check at line 139 passes because `SpinnerWords` carries the same attribute).

- [ ] **Step 5: Run the full frontend test suite**

```bash
npm --prefix frontend run test -- --run
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/CustomerDetailInline.tsx
git commit -m "feat: replace skeleton loading in CustomerDetailInline with SpinnerWords"
```

---

## Task 4: Manual smoke test

- [ ] **Step 1: Start the backend**

```bash
PYTHONPATH=src .venv/bin/uvicorn fintech_ai_segmentation.app.main:app --reload
```

- [ ] **Step 2: Start the frontend**

```bash
npm --prefix frontend run dev
```

- [ ] **Step 3: Open the Customers page and click a row**

Navigate to `http://localhost:5173/customers`. Click any customer row. Confirm:

- The expanded panel shows a braille dot + rotating phrase (not a skeleton).
- The phrase changes roughly every 700ms.
- Toggle the language switcher to PT-BR and click another row — phrases are in Portuguese.
- After the data loads, the spinner disappears and the full profile renders.

- [ ] **Step 4: Close dev servers** (Ctrl-C both terminals)
