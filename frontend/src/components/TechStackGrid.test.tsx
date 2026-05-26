import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { I18nextProvider } from "react-i18next";
import { createTestI18n } from "@/i18n/test-utils";
import { TechStackGrid } from "./TechStackGrid";

function renderGrid(lng = "en") {
  const i18n = createTestI18n(lng);
  return render(
    <I18nextProvider i18n={i18n}>
      <MemoryRouter>
        <TechStackGrid />
      </MemoryRouter>
    </I18nextProvider>
  );
}

describe("TechStackGrid", () => {
  it("renders all 12 tool cards when ALL tab is active", () => {
    renderGrid();
    const cards = screen.getAllByTestId("stack-card");
    expect(cards).toHaveLength(12);
  });

  it("clicking a category tab hides cards from other categories", () => {
    renderGrid();
    fireEvent.click(screen.getByRole("button", { name: /^DATA$/i }));
    const cards = screen.getAllByTestId("stack-card");
    // Only DATA cards: Faker, Pandas, Supabase/Postgres, SQLAlchemy = 4
    expect(cards).toHaveLength(4);
  });

  it("clicking ALL after a filter restores all 12 cards", () => {
    renderGrid();
    fireEvent.click(screen.getByRole("button", { name: /^DATA$/i }));
    fireEvent.click(screen.getByRole("button", { name: /^ALL$/i }));
    const cards = screen.getAllByTestId("stack-card");
    expect(cards).toHaveLength(12);
  });

  it("each card shows a tool name, category badge, and a why statement", () => {
    renderGrid();
    const cards = screen.getAllByTestId("stack-card");
    for (const card of cards) {
      expect(card.querySelector("[data-testid='card-name']")).toBeInTheDocument();
      expect(card.querySelector("[data-testid='card-category']")).toBeInTheDocument();
      expect(card.querySelector("[data-testid='card-why']")).toBeInTheDocument();
    }
  });

  it("renders in PT-BR without missing-key fallbacks", () => {
    renderGrid("pt-BR");
    expect(screen.getByRole("button", { name: /^TODOS$/i })).toBeInTheDocument();
  });
});
