import { render, screen, within } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { I18nextProvider } from "react-i18next";
import { createTestI18n } from "@/i18n/test-utils";
import { ThemeProvider } from "@/context/ThemeContext";
import { LandingPage } from "./LandingPage";

function renderLanding(lng = "en") {
  const i18n = createTestI18n(lng);
  return render(
    <ThemeProvider>
      <I18nextProvider i18n={i18n}>
        <MemoryRouter>
          <LandingPage />
        </MemoryRouter>
      </I18nextProvider>
    </ThemeProvider>
  );
}

describe("LandingPage", () => {
  it("renders the hero heading and View Dashboard CTA", () => {
    renderLanding();
    expect(
      screen.getByRole("heading", {
        name: /8,000 customers\. One spreadsheet\. No direction\./i,
      })
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /view dashboard/i })).toBeInTheDocument();
  });

  it("primary CTA links to /dashboard", () => {
    renderLanding();
    expect(screen.getByRole("link", { name: /view dashboard/i })).toHaveAttribute("href", "/dashboard");
  });

  it("hero secondary CTA Explore Customers links to /customers", () => {
    renderLanding();
    expect(screen.getByRole("link", { name: /explore customers/i })).toHaveAttribute("href", "/customers");
  });

  it("hero browser chrome frame is present with the preview image", () => {
    renderLanding();
    const frame = screen.getByTestId("hero-browser-chrome");
    expect(frame).toBeInTheDocument();
    expect(frame.querySelector("img")).toBeInTheDocument();
  });

  it("hero metrics panel is removed", () => {
    renderLanding();
    expect(screen.queryByTestId("hero-metrics")).toBeNull();
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

  // Issue #56 — Stack and Architecture section
  it("stack section has id='stack'", () => {
    renderLanding();
    expect(document.getElementById("stack")).toBeInTheDocument();
  });

  it("stack section renders the 'Stack and Architecture' heading", () => {
    renderLanding();
    const section = screen.getByTestId("stack-section");
    expect(section).toHaveTextContent("Stack and Architecture");
  });

  it("architecture workflow renders 6 nodes in order", () => {
    renderLanding();
    const workflow = screen.getByTestId("arch-workflow");
    const nodes = within(workflow).getAllByTestId("arch-node");
    expect(nodes).toHaveLength(6);
    const names = ["Faker", "Pandas", "Supabase", "FastAPI", "LangGraph", "React"];
    names.forEach((name, idx) => {
      expect(nodes[idx]).toHaveTextContent(name);
    });
  });

  it("architecture workflow renders 5 arrows between 6 nodes", () => {
    renderLanding();
    const workflow = screen.getByTestId("arch-workflow");
    const arrows = within(workflow).getAllByTestId("arch-arrow");
    expect(arrows).toHaveLength(5);
  });

  it("renders pt-BR text when language is pt-BR", () => {
    renderLanding("pt-BR");
    expect(screen.getByRole("link", { name: /ver painel/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /ver no github/i })).toBeInTheDocument();
  });

  it("LandingPage renders the theme toggle in the navbar", () => {
    renderLanding();
    expect(screen.getByTestId("theme-toggle")).toBeInTheDocument();
  });

  // Issue #52 — Hero section
  it("hero heading renders correctly in PT-BR", () => {
    renderLanding("pt-BR");
    expect(
      screen.getByRole("heading", {
        name: /8\.000 clientes\. Uma planilha\. Nenhuma direção\./i,
      })
    ).toBeInTheDocument();
  });

  it("language toggle changes the hero H1", () => {
    renderLanding("pt-BR");
    expect(
      screen.getByRole("heading", {
        name: /8\.000 clientes\. Uma planilha\. Nenhuma direção\./i,
      })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", {
        name: /8,000 customers\. One spreadsheet\. No direction\./i,
      })
    ).toBeNull();
  });

  // Issue #53 — Summary Block section
  it("summary block renders 4 cards", () => {
    renderLanding();
    const section = screen.getByTestId("summary-block");
    const cards = within(section).getAllByTestId("summary-card");
    expect(cards).toHaveLength(4);
  });

  it("summary block renders the 4 EN labels", () => {
    renderLanding();
    const section = screen.getByTestId("summary-block");
    expect(section).toHaveTextContent("The Problem");
    expect(section).toHaveTextContent("The Brief");
    expect(section).toHaveTextContent("The Approach");
    expect(section).toHaveTextContent("What Was Delivered");
  });

  it("each summary card has a non-empty label and body", () => {
    renderLanding();
    const section = screen.getByTestId("summary-block");
    const cards = within(section).getAllByTestId("summary-card");
    for (const card of cards) {
      expect(card.textContent?.trim().length ?? 0).toBeGreaterThan(20);
    }
  });

  it("summary block switches copy to PT-BR", () => {
    renderLanding("pt-BR");
    const section = screen.getByTestId("summary-block");
    expect(section).toHaveTextContent("O Problema");
    expect(section).not.toHaveTextContent("The Problem");
  });

  it("summary block renders without missing-key fallbacks", () => {
    renderLanding();
    const section = screen.getByTestId("summary-block");
    expect(section).not.toHaveTextContent("landing.summary");
  });

  // Issue #54 — Methodology section
  it("methodology section has id='methodology'", () => {
    renderLanding();
    expect(document.getElementById("methodology")).toBeInTheDocument();
  });

  it("methodology section renders 3 phases", () => {
    renderLanding();
    const section = document.getElementById("methodology")!;
    const phases = section.querySelectorAll("[data-testid='phase']");
    expect(phases).toHaveLength(3);
  });

  it("methodology phases render numbers 01/02/03 and titles", () => {
    renderLanding();
    const section = document.getElementById("methodology")!;
    expect(section).toHaveTextContent("01");
    expect(section).toHaveTextContent("02");
    expect(section).toHaveTextContent("03");
    expect(section).toHaveTextContent("Data Foundation");
    expect(section).toHaveTextContent("Behavioral Analysis");
    expect(section).toHaveTextContent("Segmentation and Intelligence");
  });

  it("methodology callout box renders and mentions K-Means", () => {
    renderLanding();
    const callout = screen.getByTestId("methodology-callout");
    expect(callout).toBeInTheDocument();
    expect(callout).toHaveTextContent("K-Means");
  });

  it("methodology renders in PT-BR without missing-key fallbacks", () => {
    renderLanding("pt-BR");
    const section = document.getElementById("methodology")!;
    expect(section).not.toHaveTextContent("landing.methodology");
  });

  // Issue #55 — Deliverables section
  it("deliverables section has id='deliverables'", () => {
    renderLanding();
    expect(document.getElementById("deliverables")).toBeInTheDocument();
  });

  it("deliverables section renders the 'What Was Built' shared label", () => {
    renderLanding();
    const section = screen.getByTestId("deliverables-section");
    expect(section).toHaveTextContent("What Was Built");
  });

  it("deliverables section renders both product badges", () => {
    renderLanding();
    const section = screen.getByTestId("deliverables-section");
    expect(section).toHaveTextContent("Product 01");
    expect(section).toHaveTextContent("Product 02");
  });

  it("deliverables section renders the dashboard screenshot in a browser chrome frame", () => {
    renderLanding();
    const frame = screen.getByTestId("deliverable-browser-chrome");
    expect(frame).toBeInTheDocument();
    expect(frame.querySelector("img")).toBeInTheDocument();
  });

  it("deliverables section renders the Sparkles icon beside the agent title", () => {
    renderLanding();
    expect(screen.getByTestId("deliverable-sparkles")).toBeInTheDocument();
  });

  it("deliverables code block renders input and output field names", () => {
    renderLanding();
    const code = screen.getByTestId("deliverable-code");
    expect(code).toHaveTextContent("segment");
    expect(code).toHaveTextContent("risk_level");
  });

  it("deliverables section renders 6 tool logo placeholders", () => {
    renderLanding();
    expect(screen.getAllByTestId("logo-placeholder")).toHaveLength(6);
  });

  it("deliverables renders in PT-BR without missing-key fallbacks", () => {
    renderLanding("pt-BR");
    const section = screen.getByTestId("deliverables-section");
    expect(section).not.toHaveTextContent("landing.deliverables");
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

  // Issue #57 — Footer disclaimer
  it("footer renders the disclaimer line in EN", () => {
    renderLanding();
    const disclaimer = screen.getByTestId("footer-disclaimer");
    expect(disclaimer).toBeInTheDocument();
    expect(disclaimer).toHaveTextContent(
      "SynaptiqPay is a fictional company. All data is synthetic and generated for portfolio purposes."
    );
  });

  it("footer disclaimer switches to PT-BR", () => {
    renderLanding("pt-BR");
    const disclaimer = screen.getByTestId("footer-disclaimer");
    expect(disclaimer).toHaveTextContent(
      "SynaptiqPay é uma empresa fictícia. Todos os dados são sintéticos e gerados para fins de portfólio."
    );
  });

  // Issue #57 — standalone About section removed
  it("standalone About section is removed from LandingPage", () => {
    renderLanding();
    expect(screen.queryByText(/what this is/i)).toBeNull();
    expect(screen.queryByText(/landing.about/i)).toBeNull();
  });

  // Issue #57 — footer section links point to real ids
  it("footer section links point to current section ids", () => {
    renderLanding();
    const footer = screen.getByRole("contentinfo");
    const hrefs = within(footer)
      .getAllByRole("link")
      .map((l) => l.getAttribute("href"));
    expect(hrefs).toContain("#methodology");
    expect(hrefs).toContain("#deliverables");
    expect(hrefs).toContain("#stack");
    expect(hrefs).not.toContain("#how-it-works");
    expect(hrefs).not.toContain("#ai-agent");
  });
});
