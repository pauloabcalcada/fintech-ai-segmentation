import { render, screen } from "@testing-library/react";
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
});
