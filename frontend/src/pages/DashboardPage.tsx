import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
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
  high_value_active: "#dcb8ff",
  low_value_dormant: "#6b7280",
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
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} data-testid="kpi-skeleton-card" className="rounded-lg border border-border bg-card px-5 py-4 flex flex-col gap-2">
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
// TrendBadge
// ---------------------------------------------------------------------------

function TrendBadge({
  delta,
  absolute = false,
  inverse = false,
}: {
  delta: number;
  absolute?: boolean;
  inverse?: boolean;
}) {
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const up = delta >= 0;
  const good = inverse ? !up : up;
  const label = absolute
    ? `${up ? "+" : ""}${delta.toLocaleString()}`
    : `${up ? "+" : ""}${delta.toFixed(1)}%`;
  return (
    <span className="relative inline-flex items-center gap-1">
      <span
        className="inline-flex items-center gap-0.5 text-xs font-medium px-1.5 py-0.5 rounded cursor-default"
        style={{
          backgroundColor: good ? "rgba(34,197,94,0.12)" : "rgba(248,113,113,0.12)",
          color: good ? "#22c55e" : "#f87171",
        }}
        onMouseEnter={() => setTooltipVisible(true)}
        onMouseLeave={() => setTooltipVisible(false)}
      >
        {up ? "▲" : "▼"} {label}
      </span>
      <span className="text-xs text-muted-foreground font-normal">M/M</span>
      {tooltipVisible && (
        <span
          role="tooltip"
          className="absolute left-0 top-6 z-50 w-52 rounded-md px-3 py-2 text-xs shadow-lg whitespace-normal"
          style={{ backgroundColor: "#18181b", color: "#f4f4f5", border: "1px solid #3f3f46" }}
        >
          Placeholder — prototype only. This value is not yet connected to real month-over-month data.
        </span>
      )}
    </span>
  );
}

// ---------------------------------------------------------------------------
// InfoTooltip
// ---------------------------------------------------------------------------

function InfoTooltip({ text }: { text: string }) {
  const [visible, setVisible] = useState(false);
  return (
    <span className="relative inline-flex items-center">
      <button
        type="button"
        className="ml-1 text-muted-foreground hover:text-foreground text-xs leading-none focus:outline-none"
        onMouseEnter={() => setVisible(true)}
        onMouseLeave={() => setVisible(false)}
        aria-label="info"
        data-testid="info-tooltip-trigger"
      >
        ⓘ
      </button>
      {visible && (
        <span
          role="tooltip"
          className="absolute left-5 top-0 z-50 w-56 rounded-md px-3 py-2 text-xs shadow-lg"
          style={{ backgroundColor: "#18181b", color: "#f4f4f5", border: "1px solid #3f3f46" }}
        >
          {text}
        </span>
      )}
    </span>
  );
}

// ---------------------------------------------------------------------------
// KPI Cards
// ---------------------------------------------------------------------------

function KpiCard({
  testId,
  label,
  value,
  sub,
  accent,
  tooltip,
  trend,
  trendAbsolute,
  inverse,
}: {
  testId: string;
  label: string;
  value: string;
  sub?: string;
  accent?: string;
  tooltip?: string;
  trend?: number;
  trendAbsolute?: boolean;
  inverse?: boolean;
}) {
  return (
    <div data-testid={testId} className="flex flex-col gap-1 rounded-lg border border-border bg-card px-5 py-4">
      <span className="flex items-center text-xs text-muted-foreground uppercase tracking-wide">
        {label}
        {tooltip && <InfoTooltip text={tooltip} />}
      </span>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-semibold" style={accent ? { color: accent } : undefined}>
          {value}
        </span>
        {trend !== undefined && <TrendBadge delta={trend} absolute={trendAbsolute} inverse={inverse} />}
      </div>
      {sub && <span className="text-xs text-muted-foreground">{sub}</span>}
    </div>
  );
}

function KpiRow({ data }: { data: DashboardSummaryResponse["kpi_cards"] }) {
  const { t } = useTranslation();
  const atRiskPct = ((data.at_risk_count / data.total_customers) * 100).toFixed(1);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <KpiCard
        testId="kpi-total-customers"
        label={t("dashboard.kpi.totalCustomers")}
        value={data.total_customers.toLocaleString()}
        sub={t("dashboard.kpi.totalCustomersSub")}
        tooltip={t("dashboard.kpi.totalCustomersTooltip")}
        trend={247}
        trendAbsolute
      />
      <KpiCard
        testId="kpi-lapsed"
        label={t("dashboard.kpi.atRisk")}
        value={data.at_risk_count.toLocaleString()}
        sub={t("dashboard.kpi.atRiskSub", { pct: atRiskPct })}
        accent="#f87171"
        tooltip={t("dashboard.kpi.atRiskTooltip")}
        trend={3.2}
        inverse
      />
      <KpiCard
        testId="kpi-no-activity"
        label={t("dashboard.kpi.noActivity")}
        value={data.no_transaction_count.toLocaleString()}
        sub={t("dashboard.kpi.noActivitySub", { pct: ((data.no_transaction_count / data.total_customers) * 100).toFixed(1) })}
        tooltip={t("dashboard.kpi.noActivityTooltip")}
        trend={-1.8}
        inverse
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Cluster KPI strip
// ---------------------------------------------------------------------------

const CLUSTER_TREND: Record<string, number> = {
  high_value_active: 4.1,
  low_value_dormant: -2.3,
  at_risk_churner: 1.7,
};

const CLUSTER_TREND_INVERSE: Record<string, boolean> = {
  high_value_active: false,
  low_value_dormant: true,
  at_risk_churner: true,
};

function ClusterStrip({ data }: { data: DashboardSummaryResponse["kpi_cards"] }) {
  const { t } = useTranslation();
  return (
    <div data-testid="cluster-strip" className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {data.by_cluster.map((cluster) => (
        <div
          key={cluster.cluster_name}
          data-testid={`cluster-col-${cluster.cluster_name}`}
          className="rounded-lg border border-border bg-card px-5 py-4 flex flex-col gap-3"
        >
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span
                className="h-3 w-3 rounded-full shrink-0"
                data-brand-color={CLUSTER_COLORS[cluster.cluster_name] ?? "#71717a"}
                style={{ backgroundColor: CLUSTER_COLORS[cluster.cluster_name] ?? "#71717a" }}
              />
              <span className="text-sm font-medium text-foreground">{clusterLabel(cluster.cluster_name)}</span>
            </div>
            {CLUSTER_TREND[cluster.cluster_name] !== undefined && (
              <TrendBadge
                delta={CLUSTER_TREND[cluster.cluster_name]}
                inverse={CLUSTER_TREND_INVERSE[cluster.cluster_name]}
              />
            )}
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div className="flex flex-col gap-0.5">
              <span className="flex items-center text-xs text-muted-foreground uppercase tracking-wide">
                {t("dashboard.cluster.customerCount")}
                <InfoTooltip text={t("dashboard.cluster.customerCountTooltip")} />
              </span>
              <span data-testid="cluster-count" className="text-lg font-semibold">
                {cluster.customer_count.toLocaleString()}
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="flex items-center text-xs text-muted-foreground uppercase tracking-wide">
                {t("dashboard.cluster.pctOfTotal")}
                <InfoTooltip text={t("dashboard.cluster.pctOfTotalTooltip", { total: data.total_customers.toLocaleString() })} />
              </span>
              <span data-testid="cluster-pct" className="text-lg font-semibold">
                {cluster.pct_of_total.toFixed(1)}%
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="flex items-center text-xs text-muted-foreground uppercase tracking-wide">
                {t("dashboard.cluster.avgRfm")}
                <InfoTooltip text={t("dashboard.cluster.avgRfmTooltip")} />
              </span>
              <span data-testid="cluster-avg-rfm" className="text-lg font-semibold">
                {cluster.avg_rfm_score.toFixed(2)}
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="flex items-center text-xs text-muted-foreground uppercase tracking-wide">
                {t("dashboard.cluster.avgAcqCost")}
                <InfoTooltip text={t("dashboard.cluster.avgAcqCostTooltip")} />
              </span>
              <span data-testid="cluster-avg-acq-cost" className="text-lg font-semibold">
                R$ {cluster.avg_acquisition_cost.toFixed(0)}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chart 1: Acquisition cost by channel
// ---------------------------------------------------------------------------

function useChannelLabel() {
  const { t } = useTranslation();
  return (ch: string): string =>
    ({
      organic: t("customers.organic"),
      paid_ads: t("customers.paidAds"),
      referral: t("customers.referral"),
      partnership: t("customers.partnership"),
    }[ch] ?? ch.replace("_", " "));
}

function AcqCostChart({ data }: { data: DashboardSummaryResponse["acquisition_cost_by_channel"] }) {
  const { t } = useTranslation();
  const channelLabel = useChannelLabel();
  const formatted = data.map((r) => ({
    channel: channelLabel(r.acquisition_channel),
    cost: Math.round(r.avg_acquisition_cost),
    fill: CHANNEL_COLORS[r.acquisition_channel] ?? "#71717a",
  }));

  return (
    <div className="rounded-lg border border-border bg-card px-5 py-4 flex flex-col gap-3">
      <span className="text-sm font-medium text-foreground">{t("dashboard.chart.acqCost")}</span>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={formatted} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11, fill: "#a1a1aa" }} tickLine={false} axisLine={false} />
          <YAxis type="category" dataKey="channel" tick={{ fontSize: 11, fill: "#a1a1aa" }} tickLine={false} axisLine={false} width={80} />
          <Tooltip
            contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: 6 }}
            labelStyle={{ color: "#e4e4e7" }}
            itemStyle={{ color: "#a1a1aa" }}
            formatter={(v) => [`R$ ${((v as number) ?? 0).toLocaleString()}`, t("dashboard.tooltip.avgCost")]}
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
  const { t } = useTranslation();
  return (
    <div className="rounded-lg border border-border bg-card px-5 py-4 flex flex-col gap-3">
      <span className="text-sm font-medium text-foreground">{t("dashboard.chart.productsOwned")}</span>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
          <XAxis dataKey="products_owned_count" tick={{ fontSize: 11, fill: "#a1a1aa" }} tickLine={false} axisLine={false} label={{ value: "products", position: "insideBottom", offset: -2, fontSize: 10, fill: "#71717a" }} />
          <YAxis tick={{ fontSize: 11, fill: "#a1a1aa" }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: 6 }}
            labelStyle={{ color: "#e4e4e7" }}
            itemStyle={{ color: "#a1a1aa" }}
            formatter={(v) => [((v as number) ?? 0).toLocaleString(), t("dashboard.tooltip.customers")]}
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
  const { t } = useTranslation();
  const TENURE_ORDER = ["0-6m", "6-12m", "12-24m", "24m+"];
  const sorted = [...data].sort(
    (a, b) => TENURE_ORDER.indexOf(a.tenure_bucket) - TENURE_ORDER.indexOf(b.tenure_bucket)
  );

  return (
    <div className="rounded-lg border border-border bg-card px-5 py-4 flex flex-col gap-3">
      <span className="text-sm font-medium text-foreground">{t("dashboard.chart.tenure")}</span>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={sorted} margin={{ left: 0, right: 16, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
          <XAxis dataKey="tenure_bucket" tick={{ fontSize: 11, fill: "#a1a1aa" }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fontSize: 11, fill: "#a1a1aa" }} tickLine={false} axisLine={false} domain={[0, "auto"]} />
          <Tooltip
            contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: 6 }}
            labelStyle={{ color: "#e4e4e7" }}
            itemStyle={{ color: "#a1a1aa" }}
            formatter={(v) => [((v as number) ?? 0).toFixed(2), t("dashboard.tooltip.avgProducts")]}
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
  const { t } = useTranslation();
  const formatted = data.map((r) => ({
    ...r,
    label: r.product_type.replace("_", " "),
    fill: PRODUCT_COLORS[r.product_type] ?? "#71717a",
  }));

  return (
    <div className="rounded-lg border border-border bg-card px-5 py-4 flex flex-col gap-3">
      <span className="text-sm font-medium text-foreground">{t("dashboard.chart.commonProducts")}</span>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={formatted} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#a1a1aa" }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fontSize: 11, fill: "#a1a1aa" }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: 6 }}
            labelStyle={{ color: "#e4e4e7" }}
            itemStyle={{ color: "#a1a1aa" }}
            formatter={(v) => [((v as number) ?? 0).toLocaleString(), t("dashboard.tooltip.activeOwners")]}
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

  const nonZero = rows.map((r) => r.active_rate).filter((r) => r > 0);
  const minRate = nonZero.length > 0 ? Math.min(...nonZero) : 0;
  const maxRate = nonZero.length > 0 ? Math.max(...nonZero) : 1;

  return { cohortMonths, maxOffset, grid, minRate, maxRate };
}

type HeatmapTooltip = { x: number; y: number; cohort: string; offset: number; rate: number };

function CohortHeatmap({ data }: { data: CohortActivityEntry[] }) {
  const { t } = useTranslation();
  const { cohortMonths, maxOffset, grid, minRate, maxRate } = buildHeatmapGrid(data);
  const normalize = (rate: number) =>
    rate === 0 ? 0 : (rate - minRate) / (maxRate - minRate || 1);
  const offsets = Array.from({ length: maxOffset + 1 }, (_, i) => i);
  const [tooltip, setTooltip] = useState<HeatmapTooltip | null>(null);

  const CELL_H = 16;
  const LABEL_W = 62;
  const MIN_CELL_W = 10;
  const minGridW = LABEL_W + offsets.length * MIN_CELL_W;

  return (
    <div className="rounded-lg border border-border bg-card px-5 py-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-foreground">{t("dashboard.chart.cohortHeatmap")}</span>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{(minRate * 100).toFixed(0)}%</span>
          <div className="flex gap-px">
            {[0, 0.25, 0.5, 0.75, 1].map((v) => (
              <div key={v} className="h-3 w-4 rounded-sm" style={{ backgroundColor: rateColor(v) }} />
            ))}
          </div>
          <span>{(maxRate * 100).toFixed(0)}%</span>
        </div>
      </div>
      <div className="overflow-x-auto">
        <div style={{ minWidth: minGridW, width: "100%" }}>
          {/* Header row: month offsets */}
          <div className="flex" style={{ marginLeft: LABEL_W }}>
            {offsets.map((o) => (
              <div
                key={o}
                style={{ flex: 1, minWidth: MIN_CELL_W, fontSize: 9, color: "#71717a", textAlign: "center" }}
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
                      flex: 1,
                      minWidth: MIN_CELL_W,
                      height: CELL_H - 2,
                      marginRight: 1,
                      borderRadius: 2,
                      backgroundColor: rate !== undefined ? rateColor(normalize(rate)) : "transparent",
                      cursor: rate !== undefined ? "default" : undefined,
                    }}
                    onMouseEnter={(e) => {
                      if (rate !== undefined)
                        setTooltip({ x: e.clientX, y: e.clientY, cohort, offset: o, rate });
                    }}
                    onMouseMove={(e) => {
                      if (rate !== undefined)
                        setTooltip((prev) => prev ? { ...prev, x: e.clientX, y: e.clientY } : null);
                    }}
                    onMouseLeave={() => setTooltip(null)}
                  />
                );
              })}
            </div>
          ))}
        </div>
      </div>
      <p className="text-xs text-muted-foreground">{t("dashboard.chart.cohortHeatmapDesc")}</p>

      {tooltip && (
        <div
          style={{
            position: "fixed",
            left: tooltip.x + 14,
            top: tooltip.y - 36,
            pointerEvents: "none",
            zIndex: 50,
            backgroundColor: "#18181b",
            border: "1px solid #27272a",
            borderRadius: 6,
            padding: "5px 10px",
            fontSize: 12,
            color: "#e4e4e7",
            whiteSpace: "nowrap",
          }}
        >
          <span style={{ color: "#a1a1aa" }}>
            {tooltip.cohort} · M+{tooltip.offset}
          </span>
          {"  "}
          <span style={{ color: "#34d399", fontWeight: 600 }}>
            {(tooltip.rate * 100).toFixed(1)}%
          </span>
          <span style={{ color: "#71717a" }}> active</span>
        </div>
      )}
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
  const { t } = useTranslation();
  const channelLabel = useChannelLabel();
  const { series, channels } = buildRetentionSeries(data);

  return (
    <div className="rounded-lg border border-border bg-card px-5 py-4 flex flex-col gap-3">
      <span className="text-sm font-medium text-foreground">{t("dashboard.chart.m6retention")}</span>
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
            formatter={(v, name) => [
              `${(((v as number) ?? 0) * 100).toFixed(1)}%`,
              channelLabel(name as string),
            ]}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, color: "#a1a1aa" }}
            formatter={(value) => channelLabel(value)}
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
      <p className="text-xs text-muted-foreground">{t("dashboard.chart.m6retentionDesc")}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// DashboardPage
// ---------------------------------------------------------------------------

export function DashboardPage() {
  const { t } = useTranslation();
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
      <h1 className="text-xl font-semibold">{t("dashboard.title")}</h1>

      {/* KPI cards */}
      {summaryLoading || !summary ? (
        <KpiSkeleton />
      ) : (
        <KpiRow data={summary.kpi_cards} />
      )}

      {/* Cluster KPI strip */}
      {summaryLoading || !summary ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => <ChartSkeleton key={i} height={140} />)}
        </div>
      ) : (
        <ClusterStrip data={summary.kpi_cards} />
      )}

      {/* Acquisition cost */}
      <div className="grid grid-cols-1 gap-4">
        {summaryLoading || !summary ? (
          <ChartSkeleton height={220} />
        ) : (
          <AcqCostChart data={summary.acquisition_cost_by_channel} />
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
