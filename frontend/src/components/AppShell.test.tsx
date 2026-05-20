import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { I18nextProvider } from "react-i18next";
import { createTestI18n } from "@/i18n/test-utils";
import { ThemeProvider } from "@/context/ThemeContext";
import { AppShell } from "./AppShell";

function renderShell(lng = "en") {
  const i18n = createTestI18n(lng);
  return render(
    <ThemeProvider>
      <I18nextProvider i18n={i18n}>
        <MemoryRouter>
          <AppShell />
        </MemoryRouter>
      </I18nextProvider>
    </ThemeProvider>
  );
}

beforeEach(() => {
  localStorage.clear();
  document.documentElement.className = "";
});

afterEach(() => {
  localStorage.clear();
  document.documentElement.className = "";
})

describe("AppShell topnav", () => {
  it("renders SynaptiqPay brand as a link", () => {
    renderShell();
    expect(screen.getByRole("link", { name: /synaptiqpay/i })).toBeInTheDocument();
  });

  it("renders Dashboard nav link pointing to /dashboard", () => {
    renderShell();
    const link = screen.getByRole("link", { name: "Dashboard" });
    expect(link).toHaveAttribute("href", "/dashboard");
  });

  it("renders Customers nav link pointing to /customers", () => {
    renderShell();
    const link = screen.getByRole("link", { name: "Customers" });
    expect(link).toHaveAttribute("href", "/customers");
  });

  it("has a right-side slot reserved for language toggle", () => {
    renderShell();
    expect(screen.getByTestId("topnav-right-slot")).toBeInTheDocument();
  });

  it("does not render a sidebar", () => {
    renderShell();
    expect(screen.queryByRole("complementary")).toBeNull();
  });

  it("renders nav labels in Portuguese when language is pt-BR", () => {
    renderShell("pt-BR");
    expect(screen.getByRole("link", { name: "Painel" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Clientes" })).toBeInTheDocument();
  });

  it("renders the LanguageToggle in the right slot", () => {
    renderShell();
    expect(screen.getByTestId("lang-en")).toBeInTheDocument();
    expect(screen.getByTestId("lang-pt-BR")).toBeInTheDocument();
  });

  it("renders the ThemeToggle in the right slot", () => {
    renderShell();
    expect(screen.getByTestId("theme-toggle")).toBeInTheDocument();
  });
});
