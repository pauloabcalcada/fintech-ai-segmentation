import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams, useNavigate } from "react-router-dom";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { Skeleton } from "@/components/ui/skeleton";
import { ClusterBadge } from "@/components/ClusterBadge";
import { AiRecommendationPanel } from "@/components/AiRecommendationPanel";
import {
  fetchCustomerProfile,
  NotFoundError,
  type CustomerProfile,
  type ClusterProductProfile,
  type ActivityTimelineEntry,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// KPI badge
// ---------------------------------------------------------------------------

function KpiBadge({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-border bg-card px-5 py-4 min-w-[140px]">
      <span className="text-xs text-muted-foreground uppercase tracking-wide">
        {label}
      </span>
      <span className="text-2xl font-semibold text-foreground">{value}</span>
      {sub && <span className="text-xs text-muted-foreground">{sub}</span>}
    </div>
  );
}

function clusterPositionLabel(pos: CustomerProfile["cluster_position"]) {
  if (pos === "top_20") return "Top 20%";
  if (pos === "bottom_20") return "Bottom 20%";
  if (pos === "mid_60") return "Mid 60%";
  return "—";
}

// ---------------------------------------------------------------------------
// Info row helper
// ---------------------------------------------------------------------------

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between py-1.5 border-b border-border last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// RFM Comparison bar chart
// ---------------------------------------------------------------------------

function RfmComparisonChart({ profile }: { profile: CustomerProfile }) {
  const { t } = useTranslation();
  if (!profile.cluster_averages || !profile.population_averages) return null;

  const data = [
    {
      metric: "Recency",
      Customer: profile.recency_score ?? 0,
      "Cluster avg": profile.cluster_averages.recency_score,
      "Population avg": profile.population_averages.recency_score,
    },
    {
      metric: "Frequency",
      Customer: profile.frequency_score ?? 0,
      "Cluster avg": profile.cluster_averages.frequency_score,
      "Population avg": profile.population_averages.frequency_score,
    },
    {
      metric: "Monetary",
      Customer: profile.monetary_score ?? 0,
      "Cluster avg": profile.cluster_averages.monetary_score,
      "Population avg": profile.population_averages.monetary_score,
    },
  ];

  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <h3 className="text-sm font-medium mb-4">{t("customerDetail.sections.rfmComparison")}</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} barGap={4}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="metric" tick={{ fontSize: 12 }} />
          <YAxis domain={[0, 5]} tick={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: 8,
            }}
          />
          <Legend />
          <Bar dataKey="Customer" fill="#6366f1" radius={[3, 3, 0, 0]} />
          <Bar dataKey="Cluster avg" fill="#818cf8" radius={[3, 3, 0, 0]} />
          <Bar
            dataKey="Population avg"
            fill="#c7d2fe"
            radius={[3, 3, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Activity timeline line chart
// ---------------------------------------------------------------------------

function ActivityTimelineChart({
  timeline,
}: {
  timeline: ActivityTimelineEntry[];
}) {
  const { t } = useTranslation();
  if (timeline.length === 0)
    return (
      <div className="rounded-lg border border-border bg-card p-5 flex items-center justify-center text-muted-foreground text-sm h-[180px]">
        No transaction history
      </div>
    );

  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <h3 className="text-sm font-medium mb-4">{t("customerDetail.sections.monthlyVolume")}</h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={timeline}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            dataKey="year_month"
            tick={{ fontSize: 10 }}
            interval="preserveStartEnd"
          />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: 8,
            }}
          />
          <Line
            type="monotone"
            dataKey="tx_count"
            stroke="#6366f1"
            strokeWidth={2}
            dot={false}
            name="Transactions"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Product ownership gap chart
// ---------------------------------------------------------------------------

const PRODUCTS: {
  hasKey: keyof CustomerProfile;
  pctKey: keyof ClusterProductProfile;
  label: string;
}[] = [
  { hasKey: "has_wallet", pctKey: "wallet_pct", label: "Wallet" },
  { hasKey: "has_credit_card", pctKey: "credit_card_pct", label: "Credit Card" },
  { hasKey: "has_investment", pctKey: "investment_pct", label: "Investment" },
  { hasKey: "has_insurance", pctKey: "insurance_pct", label: "Insurance" },
  { hasKey: "has_loan", pctKey: "loan_pct", label: "Loan" },
];

function ProductOwnershipChart({ profile }: { profile: CustomerProfile }) {
  const { t } = useTranslation();
  const data = PRODUCTS.map((p) => ({
    product: p.label,
    "Cluster %": profile.cluster_product_profile
      ? Math.round((profile.cluster_product_profile[p.pctKey] as number) * 100)
      : 0,
    owned: (profile[p.hasKey] as boolean) ? 100 : 0,
  }));

  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <h3 className="text-sm font-medium mb-4">{t("customerDetail.sections.productOwnership")}</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} layout="vertical" barGap={4}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            type="number"
            domain={[0, 100]}
            tickFormatter={(v: number) => `${v}%`}
            tick={{ fontSize: 11 }}
          />
          <YAxis
            dataKey="product"
            type="category"
            tick={{ fontSize: 12 }}
            width={80}
          />
          <Tooltip
            formatter={(v) => `${(v as number) ?? 0}%`}
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: 8,
            }}
          />
          <Legend />
          <Bar
            dataKey="owned"
            name="Customer owns"
            fill="#6366f1"
            radius={[0, 3, 3, 0]}
          />
          <Bar dataKey="Cluster %" fill="#c7d2fe" radius={[0, 3, 3, 0]} />
          <ReferenceLine
            x={50}
            stroke="hsl(var(--muted-foreground))"
            strokeDasharray="4 4"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export function CustomerDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [profile, setProfile] = useState<CustomerProfile | null>(null);
  const [timeline, setTimeline] = useState<ActivityTimelineEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    fetchCustomerProfile(id)
      .then((resp) => {
        setProfile(resp.data);
        setTimeline(resp.activity_timeline);
      })
      .catch((err: unknown) => {
        if (err instanceof NotFoundError) setNotFound(true);
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (notFound) {
    return (
      <div className="flex flex-col gap-4 items-center justify-center py-24 text-muted-foreground">
        <p className="text-lg">Customer not found.</p>
        <button
          onClick={() => navigate("/customers")}
          className="text-primary text-sm underline underline-offset-4"
        >
          Back to customers
        </button>
      </div>
    );
  }

  if (loading || !profile) {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-36 rounded-lg" />
          ))}
        </div>
        <Skeleton className="h-48 rounded-lg" />
        <Skeleton className="h-64 rounded-lg" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => navigate("/customers")}
            className="text-xs text-muted-foreground hover:text-foreground mb-1 flex items-center gap-1"
          >
            ← Customers
          </button>
          <h1 className="text-xl font-semibold">{profile.name}</h1>
        </div>
        <ClusterBadge cluster={profile.cluster_name} />
      </div>

      {/* KPI badges */}
      <div className="flex flex-wrap gap-3">
        <KpiBadge
          label={t("customerDetail.kpi.rfmScore")}
          value={profile.rfm_score?.toFixed(2) ?? "—"}
          sub="out of 5.0"
        />
        <KpiBadge
          label={t("customerDetail.kpi.clusterRank")}
          value={clusterPositionLabel(profile.cluster_position)}
          sub={profile.cluster_name ?? "—"}
        />
        <KpiBadge
          label={t("customerDetail.kpi.tenure")}
          value={`${profile.tenure_months}mo`}
          sub={`since ${profile.registration_date}`}
        />
        <KpiBadge
          label={t("customerDetail.kpi.lifecycle")}
          value={profile.lifecycle_stage?.replace(/_/g, " ") ?? "—"}
        />
      </div>

      {/* Two-column layout: info panel + charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Customer info panel */}
        <div className="rounded-lg border border-border bg-card p-5 flex flex-col gap-0.5">
          <h3 className="text-sm font-medium mb-3">{t("customerDetail.sections.customerInfo")}</h3>
          <InfoRow label={t("customerDetail.info.age")} value={String(profile.age)} />
          <InfoRow label={t("customerDetail.info.state")} value={profile.state} />
          <InfoRow
            label={t("customerDetail.info.channel")}
            value={profile.acquisition_channel.replace(/_/g, " ")}
          />
          <InfoRow
            label={t("customerDetail.info.acqCost")}
            value={`R$ ${profile.acquisition_cost.toFixed(2)}`}
          />
          <InfoRow label={t("customerDetail.info.registration")} value={profile.registration_date} />
          <InfoRow
            label={t("customerDetail.info.products")}
            value={`${profile.products_owned_count} / 5`}
          />
          <InfoRow
            label={t("customerDetail.info.recency")}
            value={
              profile.recency_days != null ? `${profile.recency_days}d` : "—"
            }
          />

          {/* Product ownership chips */}
          <div className="mt-4 flex flex-wrap gap-1.5">
            {PRODUCTS.map((p) => (
              <span
                key={p.label}
                className={`text-xs px-2 py-0.5 rounded-full border ${
                  profile[p.hasKey]
                    ? "border-indigo-500 text-indigo-400 bg-indigo-500/10"
                    : "border-border text-muted-foreground"
                }`}
              >
                {p.label}
              </span>
            ))}
          </div>
        </div>

        {/* Charts column */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <RfmComparisonChart profile={profile} />
          <ActivityTimelineChart timeline={timeline} />
        </div>
      </div>

      {/* Product ownership gap chart */}
      {profile.cluster_product_profile && (
        <ProductOwnershipChart profile={profile} />
      )}

      {/* AI Recommendation panel */}
      <AiRecommendationPanel
        customerId={id!}
        initialRecommendation={profile.cached_recommendation}
      />
    </div>
  );
}
