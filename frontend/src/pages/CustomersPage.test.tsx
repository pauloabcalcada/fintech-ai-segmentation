import { render, screen, within } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
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

describe("CustomersPage", () => {
  beforeEach(() => {
    mockFetchCustomers.mockResolvedValue(FIXTURE);
  });

  it("does not render an Email column header", async () => {
    render(
      <MemoryRouter>
        <CustomersPage />
      </MemoryRouter>
    );
    await screen.findByText("Ana Lima");
    expect(
      screen.queryByRole("columnheader", { name: "Email" })
    ).toBeNull();
  });

  it("does not render an RFM Score column header", async () => {
    render(
      <MemoryRouter>
        <CustomersPage />
      </MemoryRouter>
    );
    await screen.findByText("Ana Lima");
    expect(
      screen.queryByRole("columnheader", { name: /rfm score/i })
    ).toBeNull();
  });

  it("skeleton rows render 5 cells per row", () => {
    mockFetchCustomers.mockImplementation(() => new Promise(() => {}));
    render(
      <MemoryRouter>
        <CustomersPage />
      </MemoryRouter>
    );
    const rows = screen.getAllByRole("row");
    // First row is the header row; rest are skeleton rows
    const skeletonRows = rows.slice(1);
    expect(skeletonRows.length).toBeGreaterThan(0);
    for (const row of skeletonRows) {
      const cells = within(row).getAllByRole("cell");
      expect(cells).toHaveLength(5);
    }
  });
});
