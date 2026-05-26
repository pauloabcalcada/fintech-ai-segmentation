import { render, screen, within } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { I18nextProvider } from "react-i18next";
import { createTestI18n } from "@/i18n/test-utils";
import { LandingPage } from "./LandingPage";

function renderLanding(lng = "en") {
  const i18n = createTestI18n(lng);
  return render(
    <I18nextProvider i18n={i18n}>
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    </I18nextProvider>
  );
}

describe("LandingPage", () => {
  it("renders the hero heading and Open Dashboard CTA", () => {
    renderLanding();
    expect(screen.getByRole("heading", { name: /SynaptiqPay AI Segmentation/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /open dashboard/i })).toBeInTheDocument();
  });

  it("CTA links to /dashboard", () => {
    renderLanding();
    expect(screen.getByRole("link", { name: /open dashboard/i })).toHaveAttribute("href", "/dashboard");
  });

  it("GitHub link points to the correct repository URL", () => {
    renderLanding();
    const githubLink = screen.getByRole("link", { name: /view on github/i });
    expect(githubLink).toHaveAttribute("href", "https://github.com/pauloabcalcada/fintech-ai-segmentation");
  });

  it("tech stack section lists all 9 technologies", () => {
    renderLanding();
    const section = screen.getByTestId("tech-stack");
    for (const tech of ["Faker", "Pandas", "Scikit-learn", "LangGraph", "FastAPI", "React", "Supabase", "Vercel", "Fly.io"]) {
      expect(section).toHaveTextContent(tech);
    }
  });

  it("out-of-scope section includes all 4 deferred items", () => {
    renderLanding();
    const section = screen.getByTestId("out-of-scope");
    expect(section).toHaveTextContent(/cac payback/i);
    expect(section).toHaveTextContent(/churn prediction/i);
    expect(section).toHaveTextContent(/ltv\/cac heatmap/i);
    expect(section).toHaveTextContent(/text-to-sql/i);
  });

  it("renders pt-BR text when language is pt-BR", () => {
    renderLanding("pt-BR");
    expect(screen.getByRole("link", { name: /abrir painel/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /ver no github/i })).toBeInTheDocument();
    expect(screen.getByTestId("out-of-scope")).toHaveTextContent(/payback de cac/i);
  });

  it("LandingPage wrapper element carries the dark CSS class", () => {
    const { container } = renderLanding();
    expect(container.firstChild).toHaveClass("dark");
  });

  // Issue #43 — Hero section
  it("hero metrics panel displays all 6 hardcoded values", () => {
    renderLanding();
    const panel = screen.getByTestId("hero-metrics");
    expect(panel).toHaveTextContent("8,000");
    expect(panel).toHaveTextContent("4");
    expect(panel).toHaveTextContent("3");
    expect(panel).toHaveTextContent("50");
    expect(panel).toHaveTextContent("1.4s");
    expect(panel).toHaveTextContent("4");
  });

  it("hero secondary CTA links to /customers", () => {
    renderLanding();
    const links = screen.getAllByRole("link");
    const customersLink = links.find((l) => l.getAttribute("href") === "/customers");
    expect(customersLink).toBeTruthy();
  });

  it("hero heading renders correctly in PT-BR", () => {
    renderLanding("pt-BR");
    expect(screen.getByRole("heading", { name: /synaptiqpay ai segmentation/i })).toBeInTheDocument();
  });

  // Issue #44 — How It Works section
  it("how-it-works section has id='how-it-works'", () => {
    renderLanding();
    expect(document.getElementById("how-it-works")).toBeInTheDocument();
  });

  it("how-it-works section renders 4 cards with badges 01–04", () => {
    renderLanding();
    const section = document.getElementById("how-it-works")!;
    expect(section).toHaveTextContent("01");
    expect(section).toHaveTextContent("02");
    expect(section).toHaveTextContent("03");
    expect(section).toHaveTextContent("04");
  });

  it("how-it-works section renders category labels DATA, FEATURES, AGENT, SURFACE", () => {
    renderLanding();
    const section = document.getElementById("how-it-works")!;
    expect(section).toHaveTextContent("DATA");
    expect(section).toHaveTextContent("FEATURES");
    expect(section).toHaveTextContent("AGENT");
    expect(section).toHaveTextContent("SURFACE");
  });

  it("how-it-works renders in PT-BR without missing-key fallbacks", () => {
    renderLanding("pt-BR");
    const section = document.getElementById("how-it-works")!;
    expect(section).not.toHaveTextContent("landing.howItWorks");
  });
});
