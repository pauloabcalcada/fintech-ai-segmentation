import { render, screen } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { I18nextProvider } from "react-i18next";
import { createTestI18n } from "@/i18n/test-utils";
import { CustomerDetailInline } from "@/components/CustomerDetailInline";
import { fetchCustomerProfile } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  fetchCustomerProfile: vi.fn(),
  NotFoundError: class NotFoundError extends Error {},
}));

vi.mock("@/components/AiRecommendationPanel", () => ({
  AiRecommendationPanel: ({ customerId }: { customerId: string }) => (
    <div data-testid="ai-recommendation-panel" data-customer-id={customerId} />
  ),
}));

vi.mock("recharts", () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const mockFetchCustomerProfile = vi.mocked(fetchCustomerProfile);

const FIXTURE = {
  data: {
    customer_id: "abc-123",
    name: "Ana Lima",
    email: "ana@example.com",
    age: 32,
    state: "SP",
    acquisition_channel: "organic",
    acquisition_cost: 50,
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
  },
  activity_timeline: [
    { year_month: "2023-01", tx_count: 5, total_amount: 300 },
    { year_month: "2023-02", tx_count: 3, total_amount: 150 },
  ],
};

function renderInline(lng = "en") {
  const i18n = createTestI18n(lng);
  return render(
    <I18nextProvider i18n={i18n}>
      <CustomerDetailInline customerId="abc-123" />
    </I18nextProvider>
  );
}

describe("CustomerDetailInline", () => {
  beforeEach(() => {
    mockFetchCustomerProfile.mockResolvedValue(FIXTURE);
  });

  it("shows a loading container while fetching", () => {
    mockFetchCustomerProfile.mockImplementation(() => new Promise(() => {}));
    renderInline();
    expect(screen.getByTestId("customer-detail-inline-loading")).toBeInTheDocument();
  });

  it("renders AiRecommendationPanel at the top after load", async () => {
    renderInline();
    await screen.findByText("Ana Lima");
    const panel = screen.getByTestId("ai-recommendation-panel");
    expect(panel).toBeInTheDocument();
    expect(panel).toHaveAttribute("data-customer-id", "abc-123");
  });

  it("renders the customer name after load", async () => {
    renderInline();
    await screen.findByText("Ana Lima");
    expect(screen.getByText("Ana Lima")).toBeInTheDocument();
  });

  it("renders KPI badges for rfm_score, cluster_rank, and tenure", async () => {
    renderInline();
    await screen.findByText("Ana Lima");
    expect(screen.getByText("4.50")).toBeInTheDocument();
    expect(screen.getByText("Top 20%")).toBeInTheDocument();
    expect(screen.getByText("28 months")).toBeInTheDocument();
  });

  it("does not render a lifecycle KPI badge", async () => {
    renderInline();
    await screen.findByText("Ana Lima");
    expect(screen.queryByText(/ciclo de vida/i)).toBeNull();
    expect(screen.queryByText(/lifecycle/i)).toBeNull();
  });

  it("renders products section header in English", async () => {
    renderInline();
    await screen.findByText("Ana Lima");
    expect(screen.getByText("Products owned by the customer")).toBeInTheDocument();
  });

  it("renders product ownership chips in English", async () => {
    renderInline();
    await screen.findByText("Ana Lima");
    expect(screen.getByText("Wallet")).toBeInTheDocument();
    expect(screen.getByText("Credit Card")).toBeInTheDocument();
    expect(screen.getByText("Investment")).toBeInTheDocument();
    expect(screen.getByText("Insurance")).toBeInTheDocument();
    expect(screen.getByText("Loan")).toBeInTheDocument();
  });

  it("renders Portuguese product chip labels when language is pt-BR", async () => {
    renderInline("pt-BR");
    await screen.findByText("Ana Lima");
    expect(screen.getByText("Carteira Digital")).toBeInTheDocument();
    expect(screen.getByText("Cartão de Crédito")).toBeInTheDocument();
    expect(screen.getByText("Investimento")).toBeInTheDocument();
    expect(screen.getByText("Seguro")).toBeInTheDocument();
    expect(screen.getByText("Empréstimo")).toBeInTheDocument();
  });

  it("renders Portuguese KPI badge labels when language is pt-BR", async () => {
    renderInline("pt-BR");
    await screen.findByText("Ana Lima");
    expect(screen.getByText("Posição no Segmento")).toBeInTheDocument();
    expect(screen.getByText("Tempo de Conta")).toBeInTheDocument();
  });

  it("renders Portuguese products section header when language is pt-BR", async () => {
    renderInline("pt-BR");
    await screen.findByText("Ana Lima");
    expect(screen.getByText("Produtos do cliente")).toBeInTheDocument();
  });
});
