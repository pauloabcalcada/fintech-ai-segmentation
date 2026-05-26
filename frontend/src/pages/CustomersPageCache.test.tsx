/**
 * Integration test for issue #38 — verifies fetchCustomerProfile is called
 * exactly once per customer regardless of expand/collapse cycles.
 * Uses the real CustomerDetailInline (not the stub from CustomersPage.test.tsx).
 */
import { render, screen, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { I18nextProvider } from "react-i18next";
import { createTestI18n } from "@/i18n/test-utils";
import { CustomersPage } from "./CustomersPage";
import { fetchCustomerSample, fetchCustomerProfile } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  fetchCustomerSample: vi.fn(),
  fetchCustomerProfile: vi.fn(),
  NotFoundError: class NotFoundError extends Error {},
}));

vi.mock("@/components/AiRecommendationPanel", () => ({
  AiRecommendationPanel: () => <div data-testid="ai-recommendation-panel" />,
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

const SAMPLE_FIXTURE = {
  data: [
    {
      customer_id: "abc-123",
      name: "Ana Lima",
      email: "ana@example.com",
      age: 32,
      state: "SP",
      cluster_name: "high_value_active",
      lifecycle_stage: "active_clustered",
      rfm_score: 4.5,
      recency_days: 7,
    },
  ],
  total: 1,
  page: 1,
  page_size: 50,
};

const PROFILE_FIXTURE = {
  data: {
    customer_id: "abc-123",
    name: "Ana Lima",
    email: "ana@example.com",
    age: 32,
    state: "SP",
    acquisition_channel: "organic",
    acquisition_cost: 240,
    activity_trend_ratio: 1.0,
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
    has_credit_card: false,
    has_investment: false,
    has_insurance: false,
    has_loan: false,
    cluster_position: "top_20" as const,
    cluster_averages: null,
    population_averages: null,
    cluster_product_profile: null,
    cached_recommendation: null,
  },
  activity_timeline: [],
};

const mockFetchCustomerSample = vi.mocked(fetchCustomerSample);
const mockFetchCustomerProfile = vi.mocked(fetchCustomerProfile);

function renderPage() {
  const i18n = createTestI18n("en");
  return render(
    <I18nextProvider i18n={i18n}>
      <MemoryRouter>
        <CustomersPage />
      </MemoryRouter>
    </I18nextProvider>
  );
}

describe("CustomersPage cache integration", () => {
  beforeEach(() => {
    mockFetchCustomerSample.mockResolvedValue(SAMPLE_FIXTURE);
    mockFetchCustomerProfile.mockResolvedValue(PROFILE_FIXTURE);
  });

  it("fetchCustomerProfile is called exactly once across expand → collapse → expand", async () => {
    renderPage();
    await screen.findByText("Ana Lima");

    // First expand — triggers fetch
    fireEvent.click(screen.getByText("Ana Lima"));
    await screen.findByText("Ana Lima", { selector: "span" });
    expect(mockFetchCustomerProfile).toHaveBeenCalledOnce();

    // Collapse
    fireEvent.click(screen.getAllByText("Ana Lima")[0]);

    // Second expand — served from cache, no new fetch
    fireEvent.click(screen.getByText("Ana Lima"));
    await screen.findByText("Ana Lima", { selector: "span" });
    expect(mockFetchCustomerProfile).toHaveBeenCalledOnce();
  });
});
