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

  it("tech stack section renders TechStackGrid with 12 tool cards", () => {
    renderLanding();
    const section = screen.getByTestId("tech-stack");
    const cards = section.querySelectorAll("[data-testid='stack-card']");
    expect(cards).toHaveLength(12);
    for (const tech of ["Faker", "Pandas", "Scikit-learn", "LangGraph", "FastAPI"]) {
      expect(section).toHaveTextContent(tech);
    }
  });

  it("renders pt-BR text when language is pt-BR", () => {
    renderLanding("pt-BR");
    expect(screen.getByRole("link", { name: /abrir painel/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /ver no github/i })).toBeInTheDocument();
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

  // Issue #45 — Pipeline section
  it("pipeline section renders all 6 steps in order", () => {
    renderLanding();
    const section = screen.getByTestId("pipeline-section");
    const steps = section.querySelectorAll("[data-testid='pipeline-step']");
    expect(steps).toHaveLength(6);
  });

  it("pipeline step nodes show tool tag chips", () => {
    renderLanding();
    const section = screen.getByTestId("pipeline-section");
    expect(section).toHaveTextContent("Faker");
    expect(section).toHaveTextContent("FastAPI");
    expect(section).toHaveTextContent("LangGraph");
    expect(section).toHaveTextContent("React");
  });

  it("pipeline renders in PT-BR without missing-key fallbacks", () => {
    renderLanding("pt-BR");
    const section = screen.getByTestId("pipeline-section");
    expect(section).not.toHaveTextContent("landing.pipeline");
  });

  // Issue #46 — Dashboard preview section
  it("dashboard section has id='dashboard'", () => {
    renderLanding();
    expect(document.getElementById("dashboard")).toBeInTheDocument();
  });

  it("dashboard section renders an img element for the preview screenshot", () => {
    renderLanding();
    const section = document.getElementById("dashboard")!;
    expect(section.querySelector("img")).toBeInTheDocument();
  });

  it("dashboard section has a browser-chrome frame wrapper with a mock URL bar", () => {
    renderLanding();
    const section = document.getElementById("dashboard")!;
    expect(section.querySelector("[data-testid='browser-chrome']")).toBeInTheDocument();
  });

  it("dashboard renders in PT-BR without missing-key fallbacks", () => {
    renderLanding("pt-BR");
    const section = document.getElementById("dashboard")!;
    expect(section).not.toHaveTextContent("landing.dashboard");
  });

  // Issue #47 — AI Agent section
  it("ai-agent section has id='ai-agent'", () => {
    renderLanding();
    expect(document.getElementById("ai-agent")).toBeInTheDocument();
  });

  it("ai-agent terminal panels render input and output JSON field names", () => {
    renderLanding();
    const section = document.getElementById("ai-agent")!;
    // input fields
    expect(section).toHaveTextContent("segment");
    expect(section).toHaveTextContent("rfm_score");
    expect(section).toHaveTextContent("recency_days");
    // output fields
    expect(section).toHaveTextContent("risk_level");
    expect(section).toHaveTextContent("recommended_action");
    expect(section).toHaveTextContent("reasoning");
  });

  it("ai-agent node-flow shows all 5 node labels in correct order", () => {
    renderLanding();
    const flow = screen.getByTestId("agent-node-flow");
    const nodes = flow.querySelectorAll("[data-testid='agent-node']");
    expect(nodes).toHaveLength(5);
    expect(nodes[0]).toHaveTextContent(/fetch_customer_profile/i);
    expect(nodes[4]).toHaveTextContent(/validate_output/i);
  });

  it("ai-agent renders in PT-BR without missing-key fallbacks", () => {
    renderLanding("pt-BR");
    const section = document.getElementById("ai-agent")!;
    expect(section).not.toHaveTextContent("landing.agent");
  });

  // Issue #49 — Roadmap section
  it("roadmap section has id='roadmap'", () => {
    renderLanding();
    expect(document.getElementById("roadmap")).toBeInTheDocument();
  });

  it("roadmap renders all 4 phase cards with correct status badges", () => {
    renderLanding();
    const section = document.getElementById("roadmap")!;
    const cards = section.querySelectorAll("[data-testid='roadmap-card']");
    expect(cards).toHaveLength(4);
    expect(section).toHaveTextContent("SHIPPED");
    expect(section).toHaveTextContent("ACTIVE");
    // PLANNED appears twice
    const plannedMatches = section.textContent?.match(/PLANNED/g);
    expect(plannedMatches?.length).toBeGreaterThanOrEqual(2);
  });

  // Issue #49 — Footer
  it("footer renders GitHub, email, and LinkedIn links", () => {
    renderLanding();
    const footer = screen.getByRole("contentinfo");
    expect(footer).toHaveTextContent(/github/i);
    expect(footer).toHaveTextContent(/pauloabcalcada@gmail.com/i);
    expect(footer).toHaveTextContent(/linkedin/i);
  });

  it("footer has copyright line", () => {
    renderLanding();
    const footer = screen.getByRole("contentinfo");
    expect(footer).toHaveTextContent(/paulo calçada/i);
    expect(footer).toHaveTextContent(/mit/i);
  });

  // Issue #49 — outOfScope removed
  it("Out of Scope section is removed from LandingPage", () => {
    renderLanding();
    expect(screen.queryByTestId("out-of-scope")).toBeNull();
  });
});
