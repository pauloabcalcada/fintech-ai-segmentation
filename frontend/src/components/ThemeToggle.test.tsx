import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { ThemeProvider } from "@/context/ThemeContext";
import { ThemeToggle } from "./ThemeToggle";

function renderToggle() {
  return render(
    <ThemeProvider>
      <ThemeToggle />
    </ThemeProvider>
  );
}

describe("ThemeToggle", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = "";
  });

  afterEach(() => {
    localStorage.clear();
    document.documentElement.className = "";
  });

  it("renders a button with data-testid='theme-toggle'", () => {
    renderToggle();
    expect(screen.getByTestId("theme-toggle")).toBeInTheDocument();
  });

  it("shows 'Switch to light mode' aria-label in dark mode", () => {
    renderToggle();
    expect(screen.getByRole("button", { name: "Switch to light mode" })).toBeInTheDocument();
  });

  it("shows 'Switch to dark mode' aria-label in light mode", () => {
    localStorage.setItem("theme", "light");
    renderToggle();
    expect(screen.getByRole("button", { name: "Switch to dark mode" })).toBeInTheDocument();
  });

  it("clicking the button toggles the theme", () => {
    renderToggle();
    fireEvent.click(screen.getByTestId("theme-toggle"));
    expect(screen.getByRole("button", { name: "Switch to dark mode" })).toBeInTheDocument();
  });
});
