import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  analyzeCustomer,
  formatProvenance,
  MODEL_OPTIONS,
  RateLimitError,
  ProviderRateLimitError,
  ServerBusyError,
  type AnalyzeResponse,
  type CachedRecommendation,
  type RecommendationResult,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Risk level badge
// ---------------------------------------------------------------------------

const RISK_COLORS: Record<RecommendationResult["risk_level"], string> = {
  low: "bg-green-500/15 text-green-400 border-green-500/30",
  medium: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
  high: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  critical: "bg-red-500/15 text-red-400 border-red-500/30",
};

function RiskBadge({ level }: { level: RecommendationResult["risk_level"] }) {
  return (
    <span
      className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border uppercase tracking-wide ${RISK_COLORS[level]}`}
    >
      {level}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Notification text card with copy button
// ---------------------------------------------------------------------------

function NotificationCard({ text }: { text: string }) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);

  const fallback = !text;

  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }

  return (
    <div className="rounded-md border border-border bg-muted/30 px-4 py-3">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-muted-foreground">{t("aiPanel.notificationText")}</p>
        {!fallback && (
          <button
            onClick={handleCopy}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors px-2 py-0.5 rounded border border-border"
          >
            {copied ? t("aiPanel.copied") : t("aiPanel.copy")}
          </button>
        )}
      </div>
      {fallback ? (
        <p className="text-sm text-muted-foreground italic">
          {t("aiPanel.reAnalyzeToGenerate")}
        </p>
      ) : (
        <p className="text-sm leading-relaxed">{text}</p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Recommendation card
// ---------------------------------------------------------------------------

function RecommendationCard({
  result,
  provenance,
}: {
  result: RecommendationResult;
  provenance: string;
}) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <RiskBadge level={result.risk_level} />
        <span className="text-xs text-muted-foreground">{provenance}</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="rounded-md border border-border bg-muted/30 px-4 py-3">
          <p className="text-xs text-muted-foreground mb-1">Recommended Action</p>
          <p className="text-sm font-medium">{result.recommended_action}</p>
        </div>
        <div className="rounded-md border border-border bg-muted/30 px-4 py-3">
          <p className="text-xs text-muted-foreground mb-1">Suggested Product</p>
          <p className="text-sm font-medium">{result.suggested_product}</p>
        </div>
        <div className="rounded-md border border-border bg-muted/30 px-4 py-3">
          <p className="text-xs text-muted-foreground mb-1">Message Tone</p>
          <p className="text-sm font-medium">{result.message_tone}</p>
        </div>
      </div>

      <div className="rounded-md border border-border bg-muted/20 px-4 py-3">
        <p className="text-xs text-muted-foreground mb-2">Reasoning</p>
        <p className="text-sm leading-relaxed text-foreground">{result.reasoning}</p>
      </div>

      <NotificationCard text={result.notification_text} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main panel
// ---------------------------------------------------------------------------

type Status = "idle" | "loading" | "success" | "rate_limited" | "provider_rate_limited" | "server_busy" | "error";

export function AiRecommendationPanel({
  customerId,
  initialRecommendation,
}: {
  customerId: string;
  initialRecommendation: CachedRecommendation | null;
}) {
  const { t, i18n } = useTranslation();
  const [model, setModel] = useState<string>("");
  const [status, setStatus] = useState<Status>(initialRecommendation ? "success" : "idle");
  const [result, setResult] = useState<AnalyzeResponse | null>(
    initialRecommendation
      ? {
          cached: true,
          generated_at: initialRecommendation.generated_at,
          model_used: initialRecommendation.model_used,
          recommendation: initialRecommendation.recommendation,
        }
      : null
  );
  const [retryAfter, setRetryAfter] = useState<string | null>(null);

  async function fireRequest() {
    setStatus("loading");
    try {
      const response = await analyzeCustomer(customerId, model, i18n.language);
      setResult(response);
      setStatus("success");
    } catch (err) {
      if (err instanceof RateLimitError) {
        setRetryAfter(err.retry_after);
        setStatus("rate_limited");
      } else if (err instanceof ServerBusyError) {
        setStatus("server_busy");
      } else if (err instanceof ProviderRateLimitError) {
        setStatus("provider_rate_limited");
      } else {
        setStatus("error");
      }
    }
  }

  return (
    <div className="rounded-lg border border-border bg-card p-6 flex flex-col gap-5">
      {/* Top controls — always visible */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h3 className="text-sm font-semibold">{t("aiPanel.title")}</h3>

        <div className="flex items-center gap-2">
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="rounded-md border border-border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="" disabled>
              {t("aiPanel.selectModel")}
            </option>
            {MODEL_OPTIONS.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
          <button
            disabled={!model || status === "loading"}
            onClick={fireRequest}
            className="px-4 py-1.5 rounded-md bg-primary text-primary-foreground text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
          >
            {status === "loading" ? t("aiPanel.analyzing") : t("aiPanel.analyze")}
          </button>
        </div>
      </div>

      {/* Loading state */}
      {status === "loading" && (
        <div className="flex items-center gap-3 py-6 text-muted-foreground text-sm">
          <div className="h-4 w-4 rounded-full border-2 border-primary border-t-transparent animate-spin" />
          {t("aiPanel.analyzing")}
        </div>
      )}

      {/* Success state */}
      {status === "success" && result && (
        <RecommendationCard
          result={result.recommendation}
          provenance={formatProvenance(result.generated_at, result.model_used)}
        />
      )}

      {/* Rate limit error */}
      {status === "rate_limited" && retryAfter && (
        <div className="rounded-md border border-orange-500/30 bg-orange-500/10 px-4 py-3 text-sm text-orange-400">
          Daily limit reached. Available again at{" "}
          <span className="font-medium">
            {new Date(retryAfter).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
          .
        </div>
      )}

      {/* Server busy */}
      {status === "server_busy" && (
        <div className="rounded-md border border-blue-500/30 bg-blue-500/10 px-4 py-3 text-sm text-blue-400">
          We're handling several analysis requests at the moment. Please wait a few seconds and try again.
        </div>
      )}

      {/* Provider rate limit error */}
      {status === "provider_rate_limited" && (
        <div className="rounded-md border border-yellow-500/30 bg-yellow-500/10 px-4 py-3 text-sm text-yellow-400">
          This model is temporarily unavailable on the free tier. Try{" "}
          <span className="font-medium">Smart Auto</span> or another model.
        </div>
      )}

      {/* Generic error */}
      {status === "error" && (
        <div className="rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          Something went wrong. Please try again.
        </div>
      )}

      {/* Idle hint */}
      {status === "idle" && (
        <p className="text-sm text-muted-foreground">{t("aiPanel.idleHint")}</p>
      )}
    </div>
  );
}
