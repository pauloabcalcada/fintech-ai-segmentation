import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { AppShell } from "./AppShell";

describe("AppShell topnav", () => {
  it("renders SynaptiqPay brand as a link", () => {
    render(
      <MemoryRouter>
        <AppShell />
      </MemoryRouter>
    );
    expect(screen.getByRole("link", { name: /synaptiqpay/i })).toBeInTheDocument();
  });

  it("renders Dashboard nav link pointing to /dashboard", () => {
    render(
      <MemoryRouter>
        <AppShell />
      </MemoryRouter>
    );
    const link = screen.getByRole("link", { name: "Dashboard" });
    expect(link).toHaveAttribute("href", "/dashboard");
  });

  it("renders Customers nav link pointing to /customers", () => {
    render(
      <MemoryRouter>
        <AppShell />
      </MemoryRouter>
    );
    const link = screen.getByRole("link", { name: "Customers" });
    expect(link).toHaveAttribute("href", "/customers");
  });

  it("has a right-side slot reserved for language toggle", () => {
    render(
      <MemoryRouter>
        <AppShell />
      </MemoryRouter>
    );
    expect(screen.getByTestId("topnav-right-slot")).toBeInTheDocument();
  });

  it("does not render a sidebar", () => {
    render(
      <MemoryRouter>
        <AppShell />
      </MemoryRouter>
    );
    expect(screen.queryByRole("complementary")).toBeNull();
  });
});
