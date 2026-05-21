import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { I18nextProvider } from "react-i18next";
import { createTestI18n } from "@/i18n/test-utils";
import { DashboardPage } from "./DashboardPage";
import type { DashboardSummaryResponse } from "@/lib/api";

const STUB_SUMMARY: DashboardSummaryResponse = {
  kpi_cards: {
    total_customers: 8000,
    no_transaction_count: 1194,
    at_risk_count: 1613,
    by_cluster: [
      { cluster_name: "high_value_active", customer_count: 2564, pct_of_total: 32.05, avg_rfm_score: 4.29, avg_acquisition_cost: 85.16 },
      { cluster_name: "low_value_dormant", customer_count: 2629, pct_of_total: 32.86, avg_rfm_score: 1.81, avg_acquisition_cost: 121.95 },
      { cluster_name: "at_risk_churner", customer_count: 1613, pct_of_total: 20.16, avg_rfm_score: 2.91, avg_acquisition_cost: 95.77 },
    ],
  },
  acquisition_cost_by_channel: [],
  population_by_products_owned: [],
  product_ownership_vs_tenure: [],
  most_common_products: [],
};

const { fetchDashboardSummary: mockSummary, fetchDashboardAggregates: mockAggregates } = vi.hoisted(() => ({
  fetchDashboardSummary: vi.fn(() => new Promise(() => {})),
  fetchDashboardAggregates: vi.fn(() => new Promise(() => {})),
}));

vi.mock("@/lib/api", () => ({
  fetchDashboardSummary: mockSummary,
  fetchDashboardAggregates: mockAggregates,
}));

beforeEach(() => {
  mockSummary.mockReset();
  mockAggregates.mockReset();
  // Default: never-resolving (loading state)
  mockSummary.mockReturnValue(new Promise(() => {}));
  mockAggregates.mockReturnValue(new Promise(() => {}));
});

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

// ---------------------------------------------------------------------------
// Cycle 1 — KPI skeleton is 3-wide (loading state)
// ---------------------------------------------------------------------------

describe("DashboardPage loading skeleton", () => {
  it("renders exactly 3 skeleton KPI cards while loading", () => {
    renderDashboard();
    const skeletonCards = document.querySelectorAll("[data-testid='kpi-skeleton-card']");
    expect(skeletonCards).toHaveLength(3);
  });
});

// ---------------------------------------------------------------------------
// Cycle 3 — ClusterStrip shows all 3 clusters with required values
// ---------------------------------------------------------------------------

describe("DashboardPage ClusterStrip", () => {
  it("renders a column for each cluster with count, %, avg RFM, avg acquisition cost", async () => {
    mockSummary.mockResolvedValue(STUB_SUMMARY);
    renderDashboard();

    expect(await screen.findByTestId("cluster-strip")).toBeInTheDocument();

    for (const cluster of ["high_value_active", "low_value_dormant", "at_risk_churner"]) {
      const col = screen.getByTestId(`cluster-col-${cluster}`);
      expect(col).toBeInTheDocument();
      expect(col.querySelector("[data-testid='cluster-count']")).toBeInTheDocument();
      expect(col.querySelector("[data-testid='cluster-pct']")).toBeInTheDocument();
      expect(col.querySelector("[data-testid='cluster-avg-rfm']")).toBeInTheDocument();
      expect(col.querySelector("[data-testid='cluster-avg-acq-cost']")).toBeInTheDocument();
    }
  });
});

// ---------------------------------------------------------------------------
// Cycle 4 — InfoTooltip shows text on hover
// ---------------------------------------------------------------------------

describe("DashboardPage InfoTooltip", () => {
  it("shows tooltip text when hovering the ⓘ button on a KPI card", async () => {
    mockSummary.mockResolvedValue(STUB_SUMMARY);
    renderDashboard();

    await screen.findByTestId("kpi-lapsed");
    const lapsedCard = screen.getByTestId("kpi-lapsed");
    const trigger = lapsedCard.querySelector("[data-testid='info-tooltip-trigger']")!;

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
    fireEvent.mouseEnter(trigger);
    expect(screen.getByRole("tooltip")).toBeInTheDocument();
    fireEvent.mouseLeave(trigger);
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Cycle 5 — Cluster colours match spec
// ---------------------------------------------------------------------------

describe("DashboardPage cluster colours", () => {
  it("applies correct colour to each cluster badge", async () => {
    mockSummary.mockResolvedValue(STUB_SUMMARY);
    renderDashboard();

    await screen.findByTestId("cluster-strip");

    const expected: Record<string, string> = {
      high_value_active: "#dcb8ff",
      at_risk_churner: "#f87171",
      low_value_dormant: "#6b7280",
    };

    for (const [cluster, colour] of Object.entries(expected)) {
      const col = screen.getByTestId(`cluster-col-${cluster}`);
      const badge = col.querySelector("span[data-brand-color]") as HTMLElement;
      expect(badge.dataset.brandColor).toBe(colour);
    }
  });
});

// ---------------------------------------------------------------------------
// Cycle 6 — Cluster section title + bordered frame + per-cluster tooltips
// ---------------------------------------------------------------------------

describe("DashboardPage ClusterStrip — section title and tooltips", () => {
  it("renders 'AI Segmentation Groups' heading above the cluster strip", async () => {
    mockSummary.mockResolvedValue(STUB_SUMMARY);
    renderDashboard();
    await screen.findByTestId("cluster-strip");
    expect(screen.getByTestId("cluster-section-title")).toHaveTextContent("AI Segmentation Groups");
  });

  it("renders the section title in PT-BR when language is pt-BR", async () => {
    mockSummary.mockResolvedValue(STUB_SUMMARY);
    renderDashboard("pt-BR");
    await screen.findByTestId("cluster-strip");
    expect(screen.getByTestId("cluster-section-title")).toHaveTextContent("Grupos de Segmentação por IA");
  });

  it("shows cluster description tooltip on hover of the cluster name ⓘ", async () => {
    mockSummary.mockResolvedValue(STUB_SUMMARY);
    renderDashboard();
    await screen.findByTestId("cluster-strip");

    const header = screen.getByTestId("cluster-name-header-high_value_active");
    const tooltipTrigger = header.querySelector("[data-testid='info-tooltip-trigger']")!;

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
    fireEvent.mouseEnter(tooltipTrigger);
    const tooltip = screen.getByRole("tooltip");
    expect(tooltip.textContent).toMatch(/Top-tier engagers/);
    fireEvent.mouseLeave(tooltipTrigger);
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("shows PT-BR cluster description tooltip for high_value_active", async () => {
    mockSummary.mockResolvedValue(STUB_SUMMARY);
    renderDashboard("pt-BR");
    await screen.findByTestId("cluster-strip");

    const header = screen.getByTestId("cluster-name-header-high_value_active");
    const tooltipTrigger = header.querySelector("[data-testid='info-tooltip-trigger']")!;

    fireEvent.mouseEnter(tooltipTrigger);
    const tooltip = screen.getByRole("tooltip");
    expect(tooltip.textContent).not.toMatch(/Top-tier engagers/);
  });
});

// ---------------------------------------------------------------------------
// Cycle 2 — KpiRow: 3 correct cards, old cards absent
// ---------------------------------------------------------------------------

describe("DashboardPage KpiRow", () => {
  it("shows Total Customers, At-Risk, and No Activity Yet — not Avg RFM or Largest Segment", async () => {
    mockSummary.mockResolvedValue(STUB_SUMMARY);
    renderDashboard();

    expect(await screen.findByTestId("kpi-total-customers")).toBeInTheDocument();
    expect(await screen.findByTestId("kpi-lapsed")).toBeInTheDocument();
    expect(await screen.findByTestId("kpi-no-activity")).toBeInTheDocument();

    expect(screen.queryByTestId("kpi-avg-rfm")).not.toBeInTheDocument();
    expect(screen.queryByTestId("kpi-largest-segment")).not.toBeInTheDocument();
  });
});
