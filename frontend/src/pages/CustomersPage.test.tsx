import { render, screen, within, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { I18nextProvider } from "react-i18next";
import { createTestI18n } from "@/i18n/test-utils";
import { CustomersPage } from "./CustomersPage";
import { fetchCustomerSample } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  fetchCustomerSample: vi.fn(),
}));

vi.mock("@/components/CustomerDetailInline", () => ({
  CustomerDetailInline: ({
    customerId,
    cachedData,
    onLoaded,
  }: {
    customerId: string;
    cachedData?: object;
    onLoaded?: (id: string, data: object) => void;
  }) => {
    if (!cachedData && onLoaded) {
      Promise.resolve().then(() => onLoaded(customerId, { _stub: true }));
    }
    return (
      <div
        data-testid="customer-detail-inline"
        data-customer-id={customerId}
        data-cached={cachedData ? "true" : "false"}
      />
    );
  },
}));

const mockFetchCustomerSample = vi.mocked(fetchCustomerSample);

const FIXTURE = {
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
    {
      customer_id: "def-456",
      name: "Carlos Melo",
      email: "carlos@example.com",
      age: 28,
      state: "RJ",
      cluster_name: "at_risk_churner",
      lifecycle_stage: "active_clustered",
      rfm_score: 1.5,
      recency_days: 95,
    },
  ],
  total: 2,
  page: 1,
  page_size: 50,
};

function renderCustomers(lng = "en") {
  const i18n = createTestI18n(lng);
  return render(
    <I18nextProvider i18n={i18n}>
      <MemoryRouter>
        <CustomersPage />
      </MemoryRouter>
    </I18nextProvider>
  );
}

describe("CustomersPage", () => {
  beforeEach(() => {
    mockFetchCustomerSample.mockResolvedValue(FIXTURE);
  });

  it("calls fetchCustomerSample on load", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    expect(mockFetchCustomerSample).toHaveBeenCalledWith(3);
  });

  it("does not render an Email column header", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    expect(screen.queryByRole("columnheader", { name: "Email" })).toBeNull();
  });

  it("does not render an RFM Score column header", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    expect(screen.queryByRole("columnheader", { name: /rfm score/i })).toBeNull();
  });

  it("skeleton rows render 4 cells per row", () => {
    mockFetchCustomerSample.mockImplementation(() => new Promise(() => {}));
    renderCustomers();
    const rows = screen.getAllByRole("row");
    const skeletonRows = rows.slice(1);
    expect(skeletonRows.length).toBeGreaterThan(0);
    for (const row of skeletonRows) {
      const cells = within(row).getAllByRole("cell");
      expect(cells).toHaveLength(4);
    }
  });

  it("renders English heading by default", async () => {
    renderCustomers();
    expect(screen.getByRole("heading", { name: "Customers" })).toBeInTheDocument();
  });

  it("renders Portuguese heading when language is pt-BR", async () => {
    renderCustomers("pt-BR");
    expect(screen.getByRole("heading", { name: "Clientes" })).toBeInTheDocument();
  });

  it("renders an instruction hint below the heading in English", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    expect(screen.getByText(/click on a customer to expand their profile and generate/i)).toBeInTheDocument();
  });

  it("renders an instruction hint below the heading in pt-BR", async () => {
    renderCustomers("pt-BR");
    await screen.findByText("Ana Lima");
    expect(screen.getByText(/clique em um cliente para expandir o perfil e gerar/i)).toBeInTheDocument();
  });

  it("renders English table headers by default", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    expect(screen.getByRole("columnheader", { name: "Name" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Age" })).toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: /recency/i })).toBeNull();
  });

  it("renders Portuguese table headers when language is pt-BR", async () => {
    renderCustomers("pt-BR");
    await screen.findByText("Ana Lima");
    expect(screen.getByRole("columnheader", { name: "Nome" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Idade" })).toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: /recência/i })).toBeNull();
  });

  it("does not render a Recency Days column header", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    expect(screen.queryByRole("columnheader", { name: /recency/i })).toBeNull();
  });

  it("does not render pagination controls", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    expect(screen.queryByRole("button", { name: /previous/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /next/i })).toBeNull();
  });

  it("does not render a search bar", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    expect(screen.queryByPlaceholderText(/search/i)).toBeNull();
  });

  it("does not render a channel filter", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    expect(screen.queryByText(/all channels/i)).toBeNull();
  });

  it("does not render a cluster filter select", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    expect(screen.queryByText(/all clusters/i)).toBeNull();
  });

  it("renders a refresh button", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    expect(screen.getByRole("button", { name: /refresh/i })).toBeInTheDocument();
  });

  it("clicking refresh re-fetches the customer sample", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    mockFetchCustomerSample.mockClear();
    fireEvent.click(screen.getByRole("button", { name: /refresh/i }));
    expect(mockFetchCustomerSample).toHaveBeenCalledWith(3);
  });

  it("clicking a row expands CustomerDetailInline for that customer", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    fireEvent.click(screen.getByText("Ana Lima"));
    const inline = screen.getByTestId("customer-detail-inline");
    expect(inline).toBeInTheDocument();
    expect(inline).toHaveAttribute("data-customer-id", "abc-123");
  });

  it("clicking the same row again collapses the expanded section", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    fireEvent.click(screen.getByText("Ana Lima"));
    expect(screen.getByTestId("customer-detail-inline")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Ana Lima"));
    expect(screen.queryByTestId("customer-detail-inline")).toBeNull();
  });

  it("renders a synthetic data disclosure banner in English", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    expect(screen.getByText(/synthetic/i)).toBeInTheDocument();
  });

  it("renders a synthetic data disclosure banner in pt-BR", async () => {
    renderCustomers("pt-BR");
    await screen.findByText("Ana Lima");
    expect(screen.getByText(/sintéticos/i)).toBeInTheDocument();
  });

  it("renders an InfoTooltip trigger in the Cluster column header", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    const clusterHeader = screen.getByRole("columnheader", { name: /cluster/i });
    expect(within(clusterHeader).getByTestId("info-tooltip-trigger")).toBeInTheDocument();
  });

  describe("profile cache", () => {
    it("CustomerDetailInline receives cachedData on second expand of the same row", async () => {
      renderCustomers();
      await screen.findByText("Ana Lima");

      // First expand — no cache yet
      fireEvent.click(screen.getByText("Ana Lima"));
      expect(screen.getByTestId("customer-detail-inline")).toHaveAttribute("data-cached", "false");

      // Allow mock onLoaded to fire
      await waitFor(() =>
        expect(screen.getByTestId("customer-detail-inline")).toBeInTheDocument()
      );

      // Collapse
      fireEvent.click(screen.getByText("Ana Lima"));
      expect(screen.queryByTestId("customer-detail-inline")).toBeNull();

      // Second expand — cache should be populated
      fireEvent.click(screen.getByText("Ana Lima"));
      expect(screen.getByTestId("customer-detail-inline")).toHaveAttribute("data-cached", "true");
    });

    it("after clicking refresh, re-expanding a row shows no cached data", async () => {
      renderCustomers();
      await screen.findByText("Ana Lima");

      // Expand and wait for cache to populate
      fireEvent.click(screen.getByText("Ana Lima"));
      await waitFor(() =>
        expect(screen.getByTestId("customer-detail-inline")).toHaveAttribute("data-cached", "false")
      );
      // Allow onLoaded to fire
      await waitFor(() => {});

      // Refresh — clears cache
      fireEvent.click(screen.getByRole("button", { name: /refresh/i }));
      await screen.findByText("Ana Lima");

      // Expand again — should have no cache
      fireEvent.click(screen.getByText("Ana Lima"));
      expect(screen.getByTestId("customer-detail-inline")).toHaveAttribute("data-cached", "false");
    });
  });

  it("clicking a different row collapses previous and expands new", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    fireEvent.click(screen.getByText("Ana Lima"));
    expect(screen.getByTestId("customer-detail-inline")).toHaveAttribute(
      "data-customer-id",
      "abc-123"
    );
    fireEvent.click(screen.getByText("Carlos Melo"));
    const inline = screen.getByTestId("customer-detail-inline");
    expect(inline).toHaveAttribute("data-customer-id", "def-456");
    expect(screen.queryAllByTestId("customer-detail-inline")).toHaveLength(1);
  });
});
