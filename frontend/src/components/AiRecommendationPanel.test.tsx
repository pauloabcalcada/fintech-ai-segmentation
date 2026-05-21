import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { I18nextProvider } from "react-i18next";
import { createTestI18n } from "@/i18n/test-utils";
import { AiRecommendationPanel } from "./AiRecommendationPanel";
import * as api from "@/lib/api";

function renderPanel(
  opts: { lng?: string; initialRecommendation?: api.CachedRecommendation | null } = {}
) {
  const i18n = createTestI18n(opts.lng ?? "en");
  return render(
    <I18nextProvider i18n={i18n}>
      <AiRecommendationPanel
        customerId="test-id"
        initialRecommendation={opts.initialRecommendation ?? null}
      />
    </I18nextProvider>
  );
}

const _STUB_REC: api.RecommendationResult = {
  risk_level: "high",
  recommended_action: "Send re-engagement offer",
  suggested_product: "cashback credit card",
  message_tone: "urgent, empathetic",
  reasoning: "Customer has been inactive for 92 days.",
  strategy_used: "retention",
  notification_text: "We miss you! Activate your cashback card today.",
};

const _STUB_RESPONSE: api.AnalyzeResponse = {
  cached: false,
  generated_at: "2026-05-20T10:00:00Z",
  model_used: "smart-auto",
  recommendation: _STUB_REC,
};

// ---------------------------------------------------------------------------
// Cycle 1 — Analyze button visible and enabled; no model selector
// ---------------------------------------------------------------------------

describe("AiRecommendationPanel — top controls", () => {
  it("shows no model selector in idle state", () => {
    renderPanel();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });

  it("Analyze button is enabled without selecting a model", () => {
    renderPanel();
    expect(screen.getByRole("button", { name: /analyze/i })).toBeEnabled();
  });

  it("Analyze button contains a Sparkles icon in idle state", () => {
    renderPanel();
    const button = screen.getByRole("button", { name: /analyze/i });
    expect(button.querySelector("[data-testid='sparkles-icon']")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Cycle 5 — Sparkles icon present during loading state
// ---------------------------------------------------------------------------

describe("AiRecommendationPanel — Sparkles icon during loading", () => {
  it("Analyze button contains a Sparkles icon while loading", async () => {
    vi.spyOn(api, "analyzeCustomer").mockImplementation(() => new Promise(() => {}));
    renderPanel();
    fireEvent.click(screen.getByRole("button", { name: /analyze/i }));
    const button = await screen.findByRole("button", { name: /analyzing/i });
    expect(button.querySelector("[data-testid='sparkles-icon']")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Cycle 2 — analyzeCustomer called with i18n language
// ---------------------------------------------------------------------------

describe("AiRecommendationPanel — language forwarding", () => {
  beforeEach(() => {
    vi.spyOn(api, "analyzeCustomer").mockResolvedValue(_STUB_RESPONSE);
  });

  it("passes 'en' language to analyzeCustomer when language is English", async () => {
    renderPanel({ lng: "en" });
    fireEvent.click(screen.getByRole("button", { name: /analyze/i }));
    await waitFor(() => expect(api.analyzeCustomer).toHaveBeenCalledWith("test-id", "en"));
  });

  it("passes 'pt-BR' language to analyzeCustomer when language is pt-BR", async () => {
    renderPanel({ lng: "pt-BR" });
    fireEvent.click(screen.getByRole("button", { name: /anali/i }));
    await waitFor(() => expect(api.analyzeCustomer).toHaveBeenCalledWith("test-id", "pt-BR"));
  });
});

// ---------------------------------------------------------------------------
// Cycle 3 — notification_text card shown after successful analyze
// ---------------------------------------------------------------------------

describe("AiRecommendationPanel — notification_text card", () => {
  beforeEach(() => {
    vi.spyOn(api, "analyzeCustomer").mockResolvedValue(_STUB_RESPONSE);
  });

  it("shows notification_text after a successful analyze", async () => {
    renderPanel();
    fireEvent.click(screen.getByRole("button", { name: /analyze/i }));
    await waitFor(() =>
      expect(screen.getByText("We miss you! Activate your cashback card today.")).toBeInTheDocument()
    );
  });

  it("copy button exists alongside notification_text", async () => {
    renderPanel();
    fireEvent.click(screen.getByRole("button", { name: /analyze/i }));
    await waitFor(() => screen.getByText("We miss you! Activate your cashback card today."));
    expect(screen.getByRole("button", { name: /copy/i })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Cycle 4 — graceful fallback for cached recs without notification_text
// ---------------------------------------------------------------------------

describe("AiRecommendationPanel — notification_text fallback", () => {
  it("shows fallback text when cached recommendation has no notification_text", () => {
    const cachedWithoutNotification: api.CachedRecommendation = {
      generated_at: "2026-05-20T09:00:00Z",
      model_used: "llama-70b-free",
      recommendation: {
        risk_level: "critical",
        recommended_action: "Retention offer",
        suggested_product: "cashback card",
        message_tone: "urgent",
        reasoning: "Old cached result.",
        strategy_used: "retention",
        notification_text: "",
      },
    };
    renderPanel({ initialRecommendation: cachedWithoutNotification });
    expect(screen.getByText(/re-analyze to generate notification/i)).toBeInTheDocument();
  });
});
