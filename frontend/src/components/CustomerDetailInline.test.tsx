import { render, screen, fireEvent } from "@testing-library/react";
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
    acquisition_cost: 240,
    activity_trend_ratio: 1.23,
    early_window_freq_ratio: 0.87,
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
    avg_ticket: 150.5,
    avg_days_between_tx: 14.2,
    activity_trend_percentile: 0.83,
    acquisition_cost_percentile: 0.72,
    recency_percentile: 0.91,
    avg_ticket_percentile: 0.65,
    avg_days_between_tx_percentile: 0.78,
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

  describe("cachedData prop", () => {
    it("does not call fetchCustomerProfile when cachedData is provided", () => {
      const i18n = createTestI18n("en");
      render(
        <I18nextProvider i18n={i18n}>
          <CustomerDetailInline customerId="abc-123" cachedData={FIXTURE} />
        </I18nextProvider>
      );
      expect(mockFetchCustomerProfile).not.toHaveBeenCalled();
    });

    it("renders immediately without a loading skeleton when cachedData is provided", () => {
      const i18n = createTestI18n("en");
      render(
        <I18nextProvider i18n={i18n}>
          <CustomerDetailInline customerId="abc-123" cachedData={FIXTURE} />
        </I18nextProvider>
      );
      expect(screen.queryByTestId("customer-detail-inline-loading")).toBeNull();
      expect(screen.getByText("Ana Lima")).toBeInTheDocument();
    });

    it("calls onLoaded with customerId and response after a successful fetch", async () => {
      const onLoaded = vi.fn();
      const i18n = createTestI18n("en");
      render(
        <I18nextProvider i18n={i18n}>
          <CustomerDetailInline customerId="abc-123" onLoaded={onLoaded} />
        </I18nextProvider>
      );
      await screen.findByText("Ana Lima");
      expect(onLoaded).toHaveBeenCalledOnce();
      expect(onLoaded).toHaveBeenCalledWith("abc-123", FIXTURE);
    });

    it("does not call onLoaded when cachedData is provided", () => {
      const onLoaded = vi.fn();
      const i18n = createTestI18n("en");
      render(
        <I18nextProvider i18n={i18n}>
          <CustomerDetailInline customerId="abc-123" cachedData={FIXTURE} onLoaded={onLoaded} />
        </I18nextProvider>
      );
      expect(onLoaded).not.toHaveBeenCalled();
    });
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

  it("renders KPI badges for rfm_score and tenure", async () => {
    renderInline();
    await screen.findByText("Ana Lima");
    expect(screen.getByText("4.50")).toBeInTheDocument();
    expect(screen.getByText("28 months")).toBeInTheDocument();
  });

  it("renders Acquisition Cost badge as 'R$ 240'", async () => {
    renderInline();
    await screen.findByText("Ana Lima");
    expect(screen.getByText("R$ 240")).toBeInTheDocument();
  });

  it("renders Activity Trend badge with transformed [-1,1] value", async () => {
    // FIXTURE has activity_trend_ratio: 1.23 → (1.23-1)/(1.23+1) ≈ 0.10
    renderInline();
    await screen.findByText("Ana Lima");
    expect(screen.getByText("0.10")).toBeInTheDocument();
  });

  it("renders em-dash for null activity_trend_ratio", async () => {
    mockFetchCustomerProfile.mockResolvedValueOnce({
      ...FIXTURE,
      data: { ...FIXTURE.data, activity_trend_ratio: null },
    });
    renderInline();
    await screen.findByText("Ana Lima");
    const dashes = screen.getAllByText("—");
    expect(dashes.length).toBeGreaterThanOrEqual(1);
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
    expect(screen.getByText("Tempo de Conta")).toBeInTheDocument();
    expect(screen.getByText("Custo de Aquisição")).toBeInTheDocument();
    expect(screen.getByText("Tendência de Atividade")).toBeInTheDocument();
    expect(screen.getByText("Recência")).toBeInTheDocument();
    expect(screen.getByText("Ticket Médio")).toBeInTheDocument();
    expect(screen.getByText("Freq. Transações")).toBeInTheDocument();
  });

  it("renders Portuguese products section header when language is pt-BR", async () => {
    renderInline("pt-BR");
    await screen.findByText("Ana Lima");
    expect(screen.getByText("Produtos do cliente")).toBeInTheDocument();
  });

  describe("activity chart GTV toggle", () => {
    it("renders both Transactions and GTV toggle buttons", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      expect(screen.getByRole("button", { name: "Transactions" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "GTV" })).toBeInTheDocument();
    });

    it("Transactions toggle is active and GTV is inactive by default", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      expect(screen.getByRole("button", { name: "Transactions" })).toHaveAttribute("aria-pressed", "true");
      expect(screen.getByRole("button", { name: "GTV" })).toHaveAttribute("aria-pressed", "false");
    });

    it("clicking GTV makes GTV active and Transactions inactive", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      fireEvent.click(screen.getByRole("button", { name: "GTV" }));
      expect(screen.getByRole("button", { name: "GTV" })).toHaveAttribute("aria-pressed", "true");
      expect(screen.getByRole("button", { name: "Transactions" })).toHaveAttribute("aria-pressed", "false");
    });

    it("clicking Transactions after GTV restores Transactions as active", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      fireEvent.click(screen.getByRole("button", { name: "GTV" }));
      fireEvent.click(screen.getByRole("button", { name: "Transactions" }));
      expect(screen.getByRole("button", { name: "Transactions" })).toHaveAttribute("aria-pressed", "true");
      expect(screen.getByRole("button", { name: "GTV" })).toHaveAttribute("aria-pressed", "false");
    });

    it("renders Portuguese toggle labels when language is pt-BR", async () => {
      renderInline("pt-BR");
      await screen.findByText("Ana Lima");
      expect(screen.getByRole("button", { name: "Transações" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "VBT" })).toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // Cycle 5-A — Activity trend transformation
  // ---------------------------------------------------------------------------

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
      expect(screen.queryByText("3.00")).not.toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // Cycle 5-B — Dropped badges
  // ---------------------------------------------------------------------------

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

  // ---------------------------------------------------------------------------
  // Cycle 5-C — New metric badges
  // ---------------------------------------------------------------------------

  describe("new metric badges", () => {
    it("renders Recency badge with value and percentile subvalue", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      expect(screen.getByText("7 days")).toBeInTheDocument();
      expect(screen.getByText("p91 vs pop.")).toBeInTheDocument();
    });

    it("renders Avg Ticket badge with value and percentile subvalue", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      expect(screen.getByText("R$ 151")).toBeInTheDocument();
      expect(screen.getByText("p65 vs pop.")).toBeInTheDocument();
    });

    it("renders Tx Frequency badge with value and percentile subvalue", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      expect(screen.getByText("14.2 days")).toBeInTheDocument();
      expect(screen.getByText("p78 vs pop.")).toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // Cycle 5-D — Acquisition cost percentile
  // ---------------------------------------------------------------------------

  describe("acquisition cost percentile", () => {
    it("renders acquisition cost with percentile subvalue", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      expect(screen.getByText("R$ 240")).toBeInTheDocument();
      // FIXTURE has acquisition_cost_percentile: 0.72 → p72
      expect(screen.getByText("p72 vs pop.")).toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // Cycle 5-E — pt-BR labels for new badges
  // ---------------------------------------------------------------------------

  describe("pt-BR new badge labels", () => {
    it("renders Portuguese labels for the three new badges", async () => {
      renderInline("pt-BR");
      await screen.findByText("Ana Lima");
      expect(screen.getByText("Recência")).toBeInTheDocument();
      expect(screen.getByText("Ticket Médio")).toBeInTheDocument();
      expect(screen.getByText("Freq. Transações")).toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // Task 4 — KpiBadge subvalue prop
  // ---------------------------------------------------------------------------

  describe("KpiBadge subvalue", () => {
    it("renders subvalue text below the badge value when percentile data is present", async () => {
      mockFetchCustomerProfile.mockResolvedValueOnce({
        ...FIXTURE,
        data: {
          ...FIXTURE.data,
          activity_trend_percentile: 0.57,
        },
      });
      renderInline();
      await screen.findByText("Ana Lima");
      // activity_trend_percentile 0.57 → "p57 vs pop." (unique value)
      expect(screen.getByText("p57 vs pop.")).toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // Cycle 1 — KpiBadge tooltip trigger rendered when tooltip prop provided
  // ---------------------------------------------------------------------------

  describe("KPI badge InfoTooltip", () => {
    it("renders a tooltip trigger on the RFM Score badge", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      const rfmBadge = screen.getByText("RFM Score").closest("div")!;
      expect(rfmBadge.querySelector("[data-testid='info-tooltip-trigger']")).toBeInTheDocument();
    });

    it("renders exactly 7 tooltip triggers — one per KPI badge", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      expect(screen.getAllByTestId("info-tooltip-trigger")).toHaveLength(7);
    });

    it("hovering the RFM Score tooltip trigger shows tooltip text", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      const rfmBadge = screen.getByText("RFM Score").closest("div")!;
      const trigger = rfmBadge.querySelector("[data-testid='info-tooltip-trigger']")!;
      expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
      fireEvent.mouseEnter(trigger);
      expect(screen.getByRole("tooltip")).toBeInTheDocument();
      fireEvent.mouseLeave(trigger);
      expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
    });

    it("renders Portuguese tooltip text on hover when language is pt-BR", async () => {
      renderInline("pt-BR");
      await screen.findByText("Ana Lima");
      const rfmBadge = screen.getByText("RFM Score").closest("div")!;
      const trigger = rfmBadge.querySelector("[data-testid='info-tooltip-trigger']")!;
      fireEvent.mouseEnter(trigger);
      const tooltip = screen.getByRole("tooltip");
      expect(tooltip.textContent).toMatch(/pontuação comportamental/i);
      fireEvent.mouseLeave(trigger);
    });

    it("all 7 KPI badges render a tooltip trigger", async () => {
      renderInline();
      await screen.findByText("Ana Lima");
      const labels = [
        "RFM Score",
        "Tenure",
        "Recency",
        "Avg Ticket",
        "Tx Frequency",
        "Acq. Cost",
        "Activity Trend",
      ];
      for (const label of labels) {
        const badge = screen.getByText(label).closest("div")!;
        expect(badge.querySelector("[data-testid='info-tooltip-trigger']"), `${label} missing tooltip trigger`).toBeInTheDocument();
      }
    });
  });
});
