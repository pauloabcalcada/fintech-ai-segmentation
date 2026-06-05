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
  it("renders the logo text SYNAPTIQPAY  as a link to /", () => {
    renderNavbar();
    const logo = screen.getByRole("link", { name: /synaptiqpay \/ ai-seg/i });
    expect(logo).toHaveAttribute("href", "/");
  });

  it("renders anchor link for #methodology", () => {
    renderNavbar();
    expect(screen.getByRole("link", { name: /methodology/i })).toHaveAttribute("href", "#methodology");
  });

  it("renders anchor link for #deliverables", () => {
    renderNavbar();
    expect(screen.getByRole("link", { name: /deliverables/i })).toHaveAttribute("href", "#deliverables");
  });

  it("renders anchor link for #stack", () => {
    renderNavbar();
    expect(screen.getByRole("link", { name: /stack/i })).toHaveAttribute("href", "#stack");
  });

  it("renders anchor link for #roadmap", () => {
    renderNavbar();
    expect(screen.getByRole("link", { name: /roadmap/i })).toHaveAttribute("href", "#roadmap");
  });

  it("does not render any nav anchor to the old sections", () => {
    renderNavbar();
    const oldAnchors = ["#how-it-works", "#dashboard", "#ai-agent"];
    const links = screen.getAllByRole("link");
    const hrefs = links.map((l) => l.getAttribute("href"));
    for (const old of oldAnchors) {
      expect(hrefs).not.toContain(old);
    }
  });

  it("renders translated nav labels in pt-BR", () => {
    renderNavbar("pt-BR");
    expect(screen.getByRole("link", { name: /metodologia/i })).toHaveAttribute("href", "#methodology");
  });

  it("renders CTA link to /dashboard", () => {
    renderNavbar();
    const links = screen.getAllByRole("link", { name: /dashboard/i });
    const cta = links.find((l) => l.getAttribute("href") === "/dashboard");
    expect(cta).toBeTruthy();
  });

  it("renders CTA link to /customers", () => {
    renderNavbar();
    const links = screen.getAllByRole("link", { name: /ai agent/i });
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
