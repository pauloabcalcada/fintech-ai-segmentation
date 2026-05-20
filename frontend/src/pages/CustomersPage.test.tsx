import { render, screen, within } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { I18nextProvider } from "react-i18next";
import { createTestI18n } from "@/i18n/test-utils";
import { CustomersPage } from "./CustomersPage";
import { fetchCustomers } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  fetchCustomers: vi.fn(),
}));

const mockFetchCustomers = vi.mocked(fetchCustomers);

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
  ],
  total: 1,
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
    mockFetchCustomers.mockResolvedValue(FIXTURE);
  });

  it("does not render an Email column header", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    expect(
      screen.queryByRole("columnheader", { name: "Email" })
    ).toBeNull();
  });

  it("does not render an RFM Score column header", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    expect(
      screen.queryByRole("columnheader", { name: /rfm score/i })
    ).toBeNull();
  });

  it("skeleton rows render 5 cells per row", () => {
    mockFetchCustomers.mockImplementation(() => new Promise(() => {}));
    renderCustomers();
    const rows = screen.getAllByRole("row");
    const skeletonRows = rows.slice(1);
    expect(skeletonRows.length).toBeGreaterThan(0);
    for (const row of skeletonRows) {
      const cells = within(row).getAllByRole("cell");
      expect(cells).toHaveLength(5);
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

  it("renders English table headers by default", async () => {
    renderCustomers();
    await screen.findByText("Ana Lima");
    expect(screen.getByRole("columnheader", { name: "Name" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Age" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: /recency/i })).toBeInTheDocument();
  });

  it("renders Portuguese table headers when language is pt-BR", async () => {
    renderCustomers("pt-BR");
    await screen.findByText("Ana Lima");
    expect(screen.getByRole("columnheader", { name: "Nome" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Idade" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: /recência/i })).toBeInTheDocument();
  });
});
