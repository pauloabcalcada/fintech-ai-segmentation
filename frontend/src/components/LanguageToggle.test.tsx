import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { I18nextProvider } from "react-i18next";
import { createTestI18n } from "@/i18n/test-utils";
import { LanguageToggle } from "./LanguageToggle";

describe("LanguageToggle", () => {
  let i18n: ReturnType<typeof createTestI18n>;

  beforeEach(() => {
    localStorage.clear();
    i18n = createTestI18n("en");
  });

  afterEach(() => {
    localStorage.clear();
  });

  function renderToggle(lng?: string) {
    if (lng) i18n = createTestI18n(lng);
    return render(
      <I18nextProvider i18n={i18n}>
        <LanguageToggle />
      </I18nextProvider>
    );
  }

  it("renders the English flag button", () => {
    renderToggle();
    expect(screen.getByTestId("lang-en")).toBeInTheDocument();
  });

  it("renders the Brazilian Portuguese flag button", () => {
    renderToggle();
    expect(screen.getByTestId("lang-pt-BR")).toBeInTheDocument();
  });

  it("clicking the pt-BR button stores 'pt-BR' in localStorage", () => {
    renderToggle();
    fireEvent.click(screen.getByTestId("lang-pt-BR"));
    expect(localStorage.getItem("language")).toBe("pt-BR");
  });

  it("clicking the en button stores 'en' in localStorage", () => {
    renderToggle("pt-BR");
    fireEvent.click(screen.getByTestId("lang-en"));
    expect(localStorage.getItem("language")).toBe("en");
  });

  it("clicking pt-BR changes i18n language to pt-BR", () => {
    renderToggle();
    fireEvent.click(screen.getByTestId("lang-pt-BR"));
    expect(i18n.language).toBe("pt-BR");
  });

  it("clicking en changes i18n language to en", () => {
    renderToggle("pt-BR");
    fireEvent.click(screen.getByTestId("lang-en"));
    expect(i18n.language).toBe("en");
  });
});
