import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LineChart,
  Line,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Skeleton } from "@/components/ui/skeleton";
import {
  fetchDashboardSummary,
  fetchDashboardAggregates,
  type DashboardSummaryResponse,
  type DashboardAggregatesResponse,
  type CohortActivityEntry,
  type ChannelM6RetentionEntry,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Colour tokens
// ---------------------------------------------------------------------------

const CLUSTER_COLORS: Record<string, string> = {
  high_value_active: "#34d399",
  mid_value_regular: "#60a5fa",
  low_value_dormant: "#a1a1aa",
  at_risk_churner: "#f87171",
};

const CHANNEL_COLORS: Record<string, string> = {
  organic: "#34d399",
  paid_ads: "#f59e0b",
  referral: "#60a5fa",
  partnership: "#a78bfa",
};

const PRODUCT_COLORS: Record<string, string> = {
  wallet: "#60a5fa",
  credit_card: "#34d399",
  investment: "#a78bfa",
  insurance: "#f59e0b",
  loan: "#f87171",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function clusterLabel(name: string) {
  return name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function monthDiff(from: string, to: string): number {
  const [fy, fm] = from.split("-").map(Number);
  const [ty, tm] = to.split("-").map(Number);
  return (ty - fy) * 12 + (tm - fm);
}

function rateColor(rate: number): string {
  if (rate === 0) return "rgba(39,39,42,0.4)";
  const r = Math.round(34 + rate * 0);
  const g = Math.round(197 * rate + 100 * (1 - rate));
  const b = Math.round(94 * rate + 180 * (1 - rate));
  const alpha = 0.2 + rate * 0.8;
  return `rgba(${r},${g},${b},${alpha})`;
}

// ---------------------------------------------------------------------------
// Skeleton cards
// ---------------------------------------------------------------------------

function KpiSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="rounded-lg border border-border bg-card px-5 py-4 flex flex-col gap-2">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-3 w-16" />
        </div>
      ))}
    </div>
  );
}

function ChartSkeleton({ height = 280 }: { height?: number }) {
  return (
    <div className="rounded-lg border border-border bg-card p-5 flex flex-col gap-3">
      <Skeleton className="h-4 w-40" />
      <Skeleton className={`w-full rounded`} style={{ height }} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// KPI Cards
// ---------------------------------------------------------------------------

function KpiCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: string;
}) {
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-border bg-card px-5 py-4">
      <span className="text-xs text-muted-foreground uppercase tracking-wide">{label}</span>
      <span className="text-2xl font-semibold" style={accent ? { color: accent } : undefined}>
        {value}
      </span>
      {sub && <span className="text-xs text-muted-foreground">{sub}</span>}
    </div>
  );
}

function KpiRow({ data }: { data: DashboardSummaryResponse["kpi_cards"] }) {
  const topCluster = [...data.by_cluster].sort((a, b) => b.customer_count - a.customer_count)[0];
  const atRiskPct = ((data.at_risk_count / data.total_customers) * 100).toFixed(1);

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <KpiCard
        label="Total Customers"
        value={data.total_customers.toLocaleString()}
        sub="registered wallets"
      />
      <KpiCard
        label="Avg RFM Score"
        value={data.avg_rfm_score.toFixed(2)}
        sub="population-wide"
        accent="#60a5fa"
      />
      <KpiCard
        label="At-Risk / Churned"
        value={data.at_risk_count.toLocaleString()}
        sub={`${atRiskPct}% of population`}
        accent="#f87171"
      />
      <KpiCard
        label="Largest Segment"
        value={clusterLabel(topCluster?.cluster_name ?? "—")}
        sub={topCluster ? `${topCluster.customer_count.toLocaleString()} customers` : undefined}
        accent={CLUSTER_COLORS[topCluster?.cluster_name ?? ""] ?? undefined}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Segment breakdown (horizontal stacked bar-style)
// ---------------------------------------------------------------------------

function SegmentBreakdown({ data }: { data: DashboardSummaryResponse["kpi_cards"] }) {
  const total = data.total_customers;
  return (
    <div className="rounded-lg border border-border bg-card px-5 py-4 flex flex-col gap-3">
      <span className="text-sm font-medium text-foreground">Segment Breakdown</span>
      <div className="flex h-4 w-full rounded overflow-hidden">
        {data.by_cluster.map((seg) => (
          <div
            key={seg.cluster_name}
            style={{
              width: `${(seg.customer_count / total) * 100}%`,
              backgroundColor: CLUSTER_COLORS[seg.cluster_name] ?? "#71717a",
            }}
            title={`${clusterLabel(seg.cluster_name)}: ${seg.customer_count.toLocaleString()}`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1">
        {data.by_cluster.map((seg) => (
          <div key={seg.cluster_name} className="flex items-center gap-1.5">
            <div
              className="h-2.5 w-2.5 rounded-full shrink-0"
              style={{ backgroundColor: CLUSTER_COLORS[seg.cluster_name] ?? "#71717a" }}
            />
            <span className="text-xs text-muted-foreground">
              {clusterLabel(seg.cluster_name)}{" "}
              <span className="text-foreground font-medium">
                {((seg.customer_count / total) * 100).toFixed(1)}%
              </span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chart 1: Acquisition cost by channel
// ---------------------------------------------------------------------------

function AcqCostChart({ data }: { data: DashboardSummaryResponse["acquisition_cost_by_channel"] }) {
  const formatted = data.map((r) => ({
    channel: r.acquisition_channel.replace("_", " "),
    cost: Math.round(r.avg_acquisition_cost),
    fill: CHANNEL_COLORS[r.acquisition_channel] ?? "#71717a",
  }));

  return (
    <div className="rounded-lg border border-border bg-card px-5 py-4 flex flex-col gap-3">
      <span className="text-sm font-medium text-foreground">Avg Acquisition Cost by Channel (R$)</span>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={formatted} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11, fill: "#a1a1aa" }} tickLine={false} axisLine={false} />
          <YAxis type="category" dataKey="channel" tick={{ fontSize: 11, fill: "#a1a1aa" }} tickLine={false} axisLine={false} width={80} />
          <Tooltip
            contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: 6 }}
            labelStyle={{ color: "#e4e4e7" }}
            itemStyle={{ color: "#a1a1aa" }}
            formatter={(v: number) => [`R$ ${v.toLocaleString()}`, "Avg cost"]}
          />
          <Bar dataKey="cost" radius={[0, 4, 4, 0]}>
            {formatted.map((entry, i) => (
              <Cell key={i} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chart 2: Population by products owned
// ---------------------------------------------------------------------------

function ProductsOwnedChart({ data }: { data: DashboardSummaryResponse["population_by_products_owned"] }) {
  return (
    <div className="rounded-lg border border-border bg-card px-5 py-4 flex flex-col gap-3">
      <span className="text-sm font-medium text-foreground">Customers by Products Owned</span>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
          <XAxis dataKey="products_owned_count" tick={{ fontSize: 11, fill: "#a1a1aa" }} tickLine={false} axisLine={false} label={{ value: "products", position: "insideBottom", offset: -2, fontSize: 10, fill: "#71717a" }} />
          <YAxis tick={{ fontSize: 11, fill: "#a1a1aa" }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: 6 }}
            labelStyle={{ color: "#e4e4e7" }}
            itemStyle={{ color: "#a1a1aa" }}
            formatter={(v: number) => [v.toLocaleString(), "customers"]}
            labelFormatter={(l) => `${l} product(s)`}
          />
          <Bar dataKey="customer_count" fill="#60a5fa" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chart 3: Product ownership vs tenure
// ---------------------------------------------------------------------------

function TenureChart({ data }: { data: DashboardSummaryResponse["product_ownership_vs_tenure"] }) {
  const TENURE_ORDER = ["0-6m", "6-12m", "12-24m", "24m+"];
  const sorted = [...data].sort(
    (a, b) => TENURE_ORDER.indexOf(a.tenure_bucket) - TENURE_ORDER.indexOf(b.tenure_bucket)
  );

  return (
    <div className="rounded-lg border border-border bg-card px-5 py-4 flex flex-col gap-3">
      <span className="text-sm font-medium text-foreground">Avg Products Owned vs Tenure</span>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={sorted} margin={{ left: 0, right: 16, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
          <XAxis dataKey="tenure_bucket" tick={{ fontSize: 11, fill: "#a1a1aa" }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fontSize: 11, fill: "#a1a1aa" }} tickLine={false} axisLine={false} domain={[0, "auto"]} />
          <Tooltip
            contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: 6 }}
            labelStyle={{ color: "#e4e4e7" }}
            itemStyle={{ color: "#a1a1aa" }}
            formatter={(v: number) => [v.toFixed(2), "avg products"]}
          />
          <Line
            type="monotone"
            dataKey="avg_products_owned"
            stroke="#a78bfa"
            strokeWidth={2}
            dot={{ r: 4, fill: "#a78bfa" }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chart 4: Most common products
// ---------------------------------------------------------------------------

function CommonProductsChart({ data }: { data: DashboardSummaryResponse["most_common_products"] }) {
  const formatted = data.map((r) => ({
    ...r,
    label: r.product_type.replace("_", " "),
    fill: PRODUCT_COLORS[r.product_type] ?? "#71717a",
  }));

  return (
    <div className="rounded-lg border border-border bg-card px-5 py-4 flex flex-col gap-3">
      <span className="text-sm font-medium text-foreground">Active Product Ownership</span>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={formatted} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#a1a1aa" }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fontSize: 11, fill: "#a1a1aa" }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: 6 }}
            labelStyle={{ color: "#e4e4e7" }}
            itemStyle={{ color: "#a1a1aa" }}
            formatter={(v: number) => [v.toLocaleString(), "active owners"]}
          />
          <Bar dataKey="ownership_count" radius={[4, 4, 0, 0]}>
            {formatted.map((entry, i) => (
              <Cell key={i} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chart 5: Cohort activity heatmap
// ---------------------------------------------------------------------------

function buildHeatmapGrid(rows: CohortActivityEntry[]) {
  const cohortMonths = [...new Set(rows.map((r) => r.cohort_month))].sort();
  const maxOffset = Math.max(...rows.map((r) => monthDiff(r.cohort_month, r.activity_month)));

  const grid: Map<string, Map<number, number>> = new Map();
  for (const cohort of cohortMonths) {
    grid.set(cohort, new Map());
  }
  for (const row of rows) {
    const offset = monthDiff(row.cohort_month, row.activity_month);
    grid.get(row.cohort_month)!.set(offset, row.active_rate);
  }
  return { cohortMonths, maxOffset, grid };
}

function CohortHeatmap({ data }: { data: CohortActivityEntry[] }) {
  const { cohortMonths, maxOffset, grid } = buildHeatmapGrid(data);
  const offsets = Array.from({ length: maxOffset + 1 }, (_, i) => i);

  const CELL_W = 18;
  const CELL_H = 16;
  const LABEL_W = 62;
  const totalW = LABEL_W + offsets.length * CELL_W;

  return (
    <div className="rounded-lg border border-border bg-card px-5 py-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-foreground">Cohort Activity Heatmap</span>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>0%</span>
          <div className="flex gap-px">
            {[0, 0.25, 0.5, 0.75, 1].map((v) => (
              <div key={v} className="h-3 w-4 rounded-sm" style={{ backgroundColor: rateColor(v) }} />
            ))}
          </div>
          <span>100%</span>
        </div>
      </div>
      <div className="overflow-x-auto">
        <div style={{ minWidth: totalW }}>
          {/* Header row: month offsets */}
          <div className="flex" style={{ marginLeft: LABEL_W }}>
            {offsets.map((o) => (
              <div
                key={o}
                style={{ width: CELL_W, fontSize: 9, color: "#71717a", textAlign: "center" }}
              >
                {o === 0 ? "M0" : o % 3 === 0 ? `M${o}` : ""}
              </div>
            ))}
          </div>
          {/* Data rows */}
          {cohortMonths.map((cohort) => (
            <div key={cohort} className="flex items-center" style={{ height: CELL_H }}>
              <div
                style={{
                  width: LABEL_W,
                  fontSize: 9,
                  color: "#a1a1aa",
                  paddingRight: 4,
                  textAlign: "right",
                  flexShrink: 0,
                }}
              >
                {cohort}
              </div>
              {offsets.map((o) => {
                const rate = grid.get(cohort)?.get(o);
                return (
                  <div
                    key={o}
                    style={{
                      width: CELL_W - 1,
                      height: CELL_H - 2,
                      marginRight: 1,
                      borderRadius: 2,
                      backgroundColor: rate !== undefined ? rateColor(rate) : "transparent",
                      flexShrink: 0,
                    }}
                    title={
                      rate !== undefined
                        ? `${cohort} M+${o}: ${(rate * 100).toFixed(1)}%`
                        : undefined
                    }
                  />
                );
              })}
            </div>
          ))}
        </div>
      </div>
      <p className="text-xs text-muted-foreground">
        Each row = acquisition cohort. Columns = months since registration (M0…). Colour = % active that month.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chart 6: M6 retention by channel
// ---------------------------------------------------------------------------

function buildRetentionSeries(rows: ChannelM6RetentionEntry[]) {
  const channels = [...new Set(rows.map((r) => r.acquisition_channel))].sort();
  const cohortMonths = [...new Set(rows.map((r) => r.cohort_month))].sort();

  const byMonth: Record<string, Record<string, number>> = {};
  for (const cohort of cohortMonths) {
    byMonth[cohort] = { cohort_month: cohort as unknown as number } as Record<string, number>;
  }
  for (const row of rows) {
    byMonth[row.cohort_month][row.acquisition_channel] = row.m6_active_rate;
  }

  return { series: Object.values(byMonth), channels };
}

function M6RetentionChart({ data }: { data: ChannelM6RetentionEntry[] }) {
  const { series, channels } = buildRetentionSeries(data);

  return (
    <div className="rounded-lg border border-border bg-card px-5 py-4 flex flex-col gap-3">
      <span className="text-sm font-medium text-foreground">M6 Active Rate by Channel over Cohorts</span>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={series} margin={{ left: 0, right: 16, top: 4, bottom: 40 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
          <XAxis
            dataKey="cohort_month"
            tick={{ fontSize: 9, fill: "#71717a" }}
            tickLine={false}
            axisLine={false}
            angle={-45}
            textAnchor="end"
            interval={2}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#a1a1aa" }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            domain={[0, 1]}
          />
          <Tooltip
            contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: 6 }}
            labelStyle={{ color: "#e4e4e7" }}
            itemStyle={{ color: "#a1a1aa" }}
            formatter={(v: number, name: string) => [
              `${(v * 100).toFixed(1)}%`,
              name.replace("_", " "),
            ]}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, color: "#a1a1aa" }}
            formatter={(value) => value.replace(/_/g, " ")}
          />
          {channels.map((ch) => (
            <Line
              key={ch}
              type="monotone"
              dataKey={ch}
              stroke={CHANNEL_COLORS[ch] ?? "#71717a"}
              strokeWidth={2}
              dot={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <p className="text-xs text-muted-foreground">
        % of customers still active 6 months after first transaction, by acquisition cohort.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// DashboardPage
// ---------------------------------------------------------------------------

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null);
  const [aggregates, setAggregates] = useState<DashboardAggregatesResponse | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [aggregatesLoading, setAggregatesLoading] = useState(true);

  useEffect(() => {
    fetchDashboardSummary()
      .then(setSummary)
      .catch(console.error)
      .finally(() => setSummaryLoading(false));

    fetchDashboardAggregates()
      .then(setAggregates)
      .catch(console.error)
      .finally(() => setAggregatesLoading(false));
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold">Population Overview</h1>

      {/* KPI cards */}
      {summaryLoading || !summary ? (
        <KpiSkeleton />
      ) : (
        <KpiRow data={summary.kpi_cards} />
      )}

      {/* Segment breakdown + Acquisition cost */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {summaryLoading || !summary ? (
          <>
            <ChartSkeleton height={120} />
            <ChartSkeleton height={220} />
          </>
        ) : (
          <>
            <SegmentBreakdown data={summary.kpi_cards} />
            <AcqCostChart data={summary.acquisition_cost_by_channel} />
          </>
        )}
      </div>

      {/* Products owned + Tenure */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {summaryLoading || !summary ? (
          <>
            <ChartSkeleton />
            <ChartSkeleton />
          </>
        ) : (
          <>
            <ProductsOwnedChart data={summary.population_by_products_owned} />
            <TenureChart data={summary.product_ownership_vs_tenure} />
          </>
        )}
      </div>

      {/* Most common products */}
      {summaryLoading || !summary ? (
        <ChartSkeleton />
      ) : (
        <CommonProductsChart data={summary.most_common_products} />
      )}

      {/* Cohort heatmap */}
      {aggregatesLoading || !aggregates ? (
        <ChartSkeleton height={320} />
      ) : (
        <CohortHeatmap data={aggregates.cohort_activity_matrix} />
      )}

      {/* M6 retention chart */}
      {aggregatesLoading || !aggregates ? (
        <ChartSkeleton height={280} />
      ) : (
        <M6RetentionChart data={aggregates.channel_m6_retention} />
      )}
    </div>
  );
}
