import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Skeleton } from "@/components/ui/skeleton";
import { AiRecommendationPanel } from "@/components/AiRecommendationPanel";
import {
  fetchCustomerProfile,
  NotFoundError,
  type CustomerProfile,
  type ActivityTimelineEntry,
} from "@/lib/api";

function KpiBadge({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-border bg-card px-4 py-3 min-w-[120px]">
      <span className="text-xs text-muted-foreground uppercase tracking-wide">
        {label}
      </span>
      <span className="text-xl font-semibold text-foreground">{value}</span>
    </div>
  );
}

function ActivityTimeline({ timeline }: { timeline: ActivityTimelineEntry[] }) {
  const { t } = useTranslation();
  const [mode, setMode] = useState<"tx_count" | "total_amount">("tx_count");

  if (timeline.length === 0) return null;

  const txLabel = t("customerDetail.chart.toggle.transactions");
  const gtvLabel = t("customerDetail.chart.toggle.gtv");

  return (
    <div>
      <div className="flex gap-1 mb-2">
        <button
          aria-pressed={mode === "tx_count"}
          onClick={() => setMode("tx_count")}
          className={`px-2 py-0.5 rounded text-xs font-medium border transition-colors ${
            mode === "tx_count"
              ? "bg-primary text-primary-foreground border-primary"
              : "bg-transparent text-muted-foreground border-border hover:border-primary"
          }`}
        >
          {txLabel}
        </button>
        <button
          aria-pressed={mode === "total_amount"}
          onClick={() => setMode("total_amount")}
          className={`px-2 py-0.5 rounded text-xs font-medium border transition-colors ${
            mode === "total_amount"
              ? "bg-primary text-primary-foreground border-primary"
              : "bg-transparent text-muted-foreground border-border hover:border-primary"
          }`}
        >
          {gtvLabel}
        </button>
      </div>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={timeline}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            dataKey="year_month"
            tick={{ fontSize: 10 }}
            interval="preserveStartEnd"
          />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: 8,
            }}
            formatter={
              mode === "total_amount"
                ? (value: number) => [
                    `R$ ${value.toLocaleString("pt-BR", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`,
                    gtvLabel,
                  ]
                : undefined
            }
          />
          <Line
            type="monotone"
            dataKey={mode}
            stroke="#6366f1"
            strokeWidth={2}
            dot={false}
            name={mode === "tx_count" ? txLabel : gtvLabel}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function clusterPositionLabel(pos: CustomerProfile["cluster_position"]) {
  if (pos === "top_20") return "Top 20%";
  if (pos === "bottom_20") return "Bottom 20%";
  if (pos === "mid_60") return "Mid 60%";
  return "—";
}

const PRODUCTS: { hasKey: keyof CustomerProfile; i18nKey: string }[] = [
  { hasKey: "has_wallet", i18nKey: "customerDetail.products.wallet" },
  { hasKey: "has_credit_card", i18nKey: "customerDetail.products.creditCard" },
  { hasKey: "has_investment", i18nKey: "customerDetail.products.investment" },
  { hasKey: "has_insurance", i18nKey: "customerDetail.products.insurance" },
  { hasKey: "has_loan", i18nKey: "customerDetail.products.loan" },
];

export function CustomerDetailInline({ customerId }: { customerId: string }) {
  const { t } = useTranslation();
  const [profile, setProfile] = useState<CustomerProfile | null>(null);
  const [timeline, setTimeline] = useState<ActivityTimelineEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(false);
    fetchCustomerProfile(customerId)
      .then((resp) => {
        setProfile(resp.data);
        setTimeline(resp.activity_timeline);
      })
      .catch((err: unknown) => {
        if (!(err instanceof NotFoundError)) setError(true);
      })
      .finally(() => setLoading(false));
  }, [customerId]);

  if (loading) {
    return (
      <div
        className="p-6 flex flex-col gap-4"
        data-testid="customer-detail-inline-loading"
      >
        <Skeleton className="h-24 rounded-lg" />
        <div className="flex gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-32 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !profile) return null;

  return (
    <div className="w-full overflow-x-hidden p-6 flex flex-col gap-4 border-t border-border bg-muted/10">
      {/* AI panel at top */}
      <AiRecommendationPanel
        customerId={customerId}
        initialRecommendation={profile.cached_recommendation}
      />

      {/* Customer name */}
      <span className="font-semibold text-lg">{profile.name}</span>

      {/* KPI badges */}
      <div className="flex flex-wrap gap-3">
        <KpiBadge
          label={t("customerDetail.kpi.rfmScore")}
          value={profile.rfm_score?.toFixed(2) ?? "—"}
        />
        <KpiBadge
          label={t("customerDetail.kpi.clusterRank")}
          value={clusterPositionLabel(profile.cluster_position)}
        />
        <KpiBadge
          label={t("customerDetail.kpi.tenure")}
          value={t("customerDetail.kpi.tenureValue", { months: profile.tenure_months })}
        />
        <KpiBadge
          label={t("customerDetail.kpi.acquisitionCost")}
          value={profile.acquisition_cost != null ? `R$ ${Math.round(profile.acquisition_cost)}` : "—"}
        />
        <KpiBadge
          label={t("customerDetail.kpi.activityTrend")}
          value={profile.activity_trend_ratio?.toFixed(2) ?? "—"}
        />
        <KpiBadge
          label={t("customerDetail.kpi.earlyWindowFreq")}
          value={profile.early_window_freq_ratio?.toFixed(2) ?? "—"}
        />
      </div>

      {/* Product ownership chips */}
      <p className="text-xs text-muted-foreground">{t("customerDetail.products.header")}</p>
      <div className="flex flex-wrap gap-1.5">
        {PRODUCTS.map((p) => (
          <span
            key={p.i18nKey}
            className={`text-xs px-2 py-0.5 rounded-full border ${
              profile[p.hasKey]
                ? "border-indigo-500 text-indigo-400 bg-indigo-500/10"
                : "border-border text-muted-foreground"
            }`}
          >
            {t(p.i18nKey)}
          </span>
        ))}
      </div>

      {/* Activity timeline */}
      <ActivityTimeline timeline={timeline} />
    </div>
  );
}
