import { render, screen } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { I18nextProvider } from "react-i18next";
import { createTestI18n } from "@/i18n/test-utils";
import { fetchCustomerProfile } from "@/lib/api";
import { CustomerDetailPage } from "./CustomerDetailPage";

vi.mock("@/lib/api", () => ({
  fetchCustomerProfile: vi.fn(),
  NotFoundError: class NotFoundError extends Error {},
  MODEL_OPTIONS: [],
}));

vi.mock("@/components/AiRecommendationPanel", () => ({
  AiRecommendationPanel: () => null,
}));

vi.mock("recharts", () => ({
  BarChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
  LineChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Line: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  ReferenceLine: () => null,
}));

const mockFetchCustomerProfile = vi.mocked(fetchCustomerProfile);

const FIXTURE_PROFILE = {
  customer_id: "abc-123",
  name: "Ana Lima",
  email: "ana@example.com",
  age: 32,
  state: "SP",
  acquisition_channel: "organic",
  acquisition_cost: 0,
  registration_date: "2023-01-15",
  tenure_months: 28,
  cluster_name: "high_value_active",
  lifecycle_stage: "active_clustered",
  rfm_score: 4.5,
  recency_score: 4,
  frequency_score: 5,
  monetary_score: 4,
  recency_days: 7,
  products_owned_count: 3,
  has_wallet: true,
  has_credit_card: true,
  has_investment: true,
  has_insurance: false,
  has_loan: false,
  cluster_position: "top_20" as const,
  cluster_averages: null,
  population_averages: null,
  cluster_product_profile: null,
  cached_recommendation: null,
};

function renderDetailPage(lng = "en") {
  const i18n = createTestI18n(lng);
  return render(
    <I18nextProvider i18n={i18n}>
      <MemoryRouter initialEntries={["/customers/abc-123"]}>
        <Routes>
          <Route path="/customers/:id" element={<CustomerDetailPage />} />
        </Routes>
      </MemoryRouter>
    </I18nextProvider>
  );
}

describe("CustomerDetailPage", () => {
  beforeEach(() => {
    mockFetchCustomerProfile.mockResolvedValue({
      data: FIXTURE_PROFILE,
      activity_timeline: [],
    });
  });

  it("does not render the customer email in the header", async () => {
    renderDetailPage();
    await screen.findByText("Ana Lima");
    expect(screen.queryByText("ana@example.com")).toBeNull();
  });

  describe("pt-BR language", () => {
    it("renders 'Informações do Cliente' as the customer info section header", async () => {
      renderDetailPage("pt-BR");
      await screen.findByText("Ana Lima");
      expect(screen.getByText("Informações do Cliente")).toBeTruthy();
    });

    it("renders 'Comparação de Pontuação RFM' as the RFM chart section header", async () => {
      mockFetchCustomerProfile.mockResolvedValueOnce({
        data: {
          ...FIXTURE_PROFILE,
          cluster_averages: { recency_score: 3, frequency_score: 3, monetary_score: 3 },
          population_averages: { recency_score: 3, frequency_score: 3, monetary_score: 3 },
        },
        activity_timeline: [],
      });
      renderDetailPage("pt-BR");
      await screen.findByText("Ana Lima");
      expect(screen.getByText("Comparação de Pontuação RFM")).toBeTruthy();
    });

    it("renders translated KPI badge labels", async () => {
      renderDetailPage("pt-BR");
      await screen.findByText("Ana Lima");
      expect(screen.getByText("Posição no Segmento")).toBeTruthy();
      expect(screen.getByText("Tempo de Conta")).toBeTruthy();
    });

    it("does not render a lifecycle KPI badge", async () => {
      renderDetailPage("pt-BR");
      await screen.findByText("Ana Lima");
      expect(screen.queryByText("Ciclo de Vida")).toBeNull();
    });

    it("renders translated InfoRow labels", async () => {
      renderDetailPage("pt-BR");
      await screen.findByText("Ana Lima");
      expect(screen.getByText("Idade")).toBeTruthy();
      expect(screen.getByText("Estado")).toBeTruthy();
      expect(screen.getByText("Canal")).toBeTruthy();
      expect(screen.getByText("Custo de Aquisição")).toBeTruthy();
      expect(screen.getByText("Cadastro")).toBeTruthy();
      expect(screen.getByText("Recência")).toBeTruthy();
    });
  });
});
