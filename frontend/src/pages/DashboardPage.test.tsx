import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { I18nextProvider } from "react-i18next";
import { createTestI18n } from "@/i18n/test-utils";
import { DashboardPage } from "./DashboardPage";

vi.mock("@/lib/api", () => ({
  fetchDashboardSummary: vi.fn(() => new Promise(() => {})),
  fetchDashboardAggregates: vi.fn(() => new Promise(() => {})),
}));

function renderDashboard(lng = "en") {
  const i18n = createTestI18n(lng);
  return render(
    <I18nextProvider i18n={i18n}>
      <DashboardPage />
    </I18nextProvider>
  );
}

describe("DashboardPage i18n", () => {
  it("renders English heading by default", () => {
    renderDashboard();
    expect(screen.getByRole("heading", { name: "Population Overview" })).toBeInTheDocument();
  });

  it("renders Portuguese heading when language is pt-BR", () => {
    renderDashboard("pt-BR");
    expect(
      screen.getByRole("heading", { name: "Visão Geral da População" })
    ).toBeInTheDocument();
  });
});
