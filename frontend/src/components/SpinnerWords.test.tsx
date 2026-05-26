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
    vi.spyOn(Math, "random").mockReturnValue(0);
    renderSpinner("en");

    const before = screen.getByTestId("customer-detail-inline-loading").textContent ?? "";

    act(() => {
      vi.advanceTimersByTime(700);
    });

    const after = screen.getByTestId("customer-detail-inline-loading").textContent ?? "";
    expect(after).not.toBe(before);

    vi.spyOn(Math, "random").mockRestore();
  });
});
