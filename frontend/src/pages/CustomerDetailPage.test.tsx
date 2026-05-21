import { render, screen } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
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

function renderDetailPage() {
  return render(
    <MemoryRouter initialEntries={["/customers/abc-123"]}>
      <Routes>
        <Route path="/customers/:id" element={<CustomerDetailPage />} />
      </Routes>
    </MemoryRouter>
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
});
