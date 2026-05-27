import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { I18nextProvider } from "react-i18next";
import { createTestI18n } from "@/i18n/test-utils";
import { ThemeProvider } from "@/context/ThemeContext";
import { LandingNavbar } from "./LandingNavbar";

function renderNavbar(lng = "en") {
  const i18n = createTestI18n(lng);
  return render(
    <ThemeProvider>
      <I18nextProvider i18n={i18n}>
        <MemoryRouter>
          <LandingNavbar />
        </MemoryRouter>
      </I18nextProvider>
    </ThemeProvider>
  );
}

describe("LandingNavbar", () => {
  it("renders the logo text SYNAPTIQPAY / AI-SEG as a link to /", () => {
    renderNavbar();
    const logo = screen.getByRole("link", { name: /synaptiqpay \/ ai-seg/i });
    expect(logo).toHaveAttribute("href", "/");
  });

  it("renders anchor link for #how-it-works", () => {
    renderNavbar();
    expect(screen.getByRole("link", { name: /how it works/i })).toHaveAttribute("href", "#how-it-works");
  });

  it("renders anchor link for #dashboard", () => {
    renderNavbar();
    const links = screen.getAllByRole("link", { name: /dashboard/i });
    const anchor = links.find((l) => l.getAttribute("href") === "#dashboard");
    expect(anchor).toBeTruthy();
  });

  it("renders anchor link for #ai-agent", () => {
    renderNavbar();
    expect(screen.getByRole("link", { name: /ai agent/i })).toHaveAttribute("href", "#ai-agent");
  });

  it("renders anchor link for #roadmap", () => {
    renderNavbar();
    expect(screen.getByRole("link", { name: /roadmap/i })).toHaveAttribute("href", "#roadmap");
  });

  it("renders CTA link to /dashboard", () => {
    renderNavbar();
    const links = screen.getAllByRole("link", { name: /dashboard/i });
    const cta = links.find((l) => l.getAttribute("href") === "/dashboard");
    expect(cta).toBeTruthy();
  });

  it("renders CTA link to /customers", () => {
    renderNavbar();
    const links = screen.getAllByRole("link", { name: /customers/i });
    const cta = links.find((l) => l.getAttribute("href") === "/customers");
    expect(cta).toBeTruthy();
  });

  it("renders the language toggle", () => {
    renderNavbar();
    expect(screen.getByTestId("lang-en")).toBeInTheDocument();
    expect(screen.getByTestId("lang-pt-BR")).toBeInTheDocument();
  });

  it("renders the theme toggle", () => {
    renderNavbar();
    expect(screen.getByTestId("theme-toggle")).toBeInTheDocument();
  });
});
