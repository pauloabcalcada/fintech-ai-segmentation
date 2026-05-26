const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface CustomerSummary {
  customer_id: string;
  name: string;
  email: string;
  age: number;
  state: string;
  cluster_name: string | null;
  lifecycle_stage: string | null;
  rfm_score: number | null;
  recency_days: number | null;
}

export interface CustomerListResponse {
  data: CustomerSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface CustomerListParams {
  cluster?: string;
  lifecycle_stage?: string;
  channel?: string;
  q?: string;
  sort?: string;
  order?: string;
  page?: number;
  page_size?: number;
}

export interface RFMAverages {
  recency_score: number;
  frequency_score: number;
  monetary_score: number;
  rfm_score: number;
}

export interface ClusterProductProfile {
  wallet_pct: number;
  credit_card_pct: number;
  investment_pct: number;
  insurance_pct: number;
  loan_pct: number;
}

export interface RecommendationResult {
  risk_level: "low" | "medium" | "high" | "critical";
  recommended_action: string;
  suggested_product: string;
  message_tone: string;
  reasoning: string;
  strategy_used: string;
  notification_text: string;
}

export interface CachedRecommendation {
  generated_at: string;
  model_used: string;
  recommendation: RecommendationResult;
}

export interface CustomerProfile {
  customer_id: string;
  name: string;
  email: string;
  age: number;
  state: string;
  acquisition_channel: string;
  acquisition_cost: number;
  registration_date: string;
  tenure_months: number;
  cluster_name: string | null;
  lifecycle_stage: string | null;
  rfm_score: number | null;
  recency_score: number | null;
  frequency_score: number | null;
  monetary_score: number | null;
  recency_days: number | null;
  products_owned_count: number;
  has_wallet: boolean;
  has_credit_card: boolean;
  has_investment: boolean;
  has_insurance: boolean;
  has_loan: boolean;
  cluster_position: "bottom_20" | "mid_60" | "top_20" | null;
  cluster_averages: RFMAverages | null;
  population_averages: RFMAverages | null;
  cluster_product_profile: ClusterProductProfile | null;
  cached_recommendation: CachedRecommendation | null;
  activity_trend_ratio: number | null;
  early_window_freq_ratio: number | null;
  avg_ticket: number | null;
  avg_days_between_tx: number | null;
  activity_trend_percentile: number | null;
  acquisition_cost_percentile: number | null;
  recency_percentile: number | null;
  avg_ticket_percentile: number | null;
  avg_days_between_tx_percentile: number | null;
}

export interface ActivityTimelineEntry {
  year_month: string;
  tx_count: number;
  total_amount: number;
}

export interface CustomerProfileResponse {
  data: CustomerProfile;
  activity_timeline: ActivityTimelineEntry[];
}

export interface AnalyzeResponse {
  cached: boolean;
  generated_at: string;
  model_used: string;
  recommendation: RecommendationResult;
}

export class NotFoundError extends Error {
  constructor() {
    super("Not found");
    this.name = "NotFoundError";
  }
}

export class RateLimitError extends Error {
  retry_after: string;
  constructor(retry_after: string) {
    super("Rate limit exceeded");
    this.name = "RateLimitError";
    this.retry_after = retry_after;
  }
}

export class ProviderRateLimitError extends Error {
  constructor() {
    super("AI provider temporarily unavailable");
    this.name = "ProviderRateLimitError";
  }
}

export class ServerBusyError extends Error {
  constructor() {
    super("Server is busy with too many concurrent requests");
    this.name = "ServerBusyError";
  }
}

export async function fetchCustomerSample(
  perCluster = 3
): Promise<CustomerListResponse> {
  const url = new URL(`${BASE_URL}/customers/sample`);
  url.searchParams.set("per_cluster", String(perCluster));
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`GET /customers/sample failed: ${res.status}`);
  return res.json() as Promise<CustomerListResponse>;
}

export async function fetchCustomers(
  params: CustomerListParams = {}
): Promise<CustomerListResponse> {
  const url = new URL(`${BASE_URL}/customers`);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "" && v !== null) {
      url.searchParams.set(k, String(v));
    }
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`GET /customers failed: ${res.status}`);
  return res.json() as Promise<CustomerListResponse>;
}

export async function fetchCustomerProfile(
  id: string
): Promise<CustomerProfileResponse> {
  const res = await fetch(`${BASE_URL}/customers/${id}`);
  if (res.status === 404) throw new NotFoundError();
  if (!res.ok) throw new Error(`GET /customers/${id} failed: ${res.status}`);
  return res.json() as Promise<CustomerProfileResponse>;
}

export async function analyzeCustomer(
  customerId: string,
  language: string = "en"
): Promise<AnalyzeResponse> {
  const res = await fetch(`${BASE_URL}/customers/${customerId}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ language }),
  });
  if (res.status === 429) {
    const body = await res.json();
    throw new RateLimitError(body.detail.retry_after as string);
  }
  if (res.status === 503) {
    const body = await res.json().catch(() => ({}));
    if (body?.detail?.error === "server_busy") throw new ServerBusyError();
    throw new ProviderRateLimitError();
  }
  if (!res.ok) throw new Error(`POST /customers/${customerId}/analyze failed: ${res.status}`);
  return res.json() as Promise<AnalyzeResponse>;
}

// ---------------------------------------------------------------------------
// Dashboard types
// ---------------------------------------------------------------------------

export interface ClusterKpi {
  cluster_name: string;
  customer_count: number;
  pct_of_total: number;
  avg_rfm_score: number;
  avg_acquisition_cost: number;
}

export interface KpiCards {
  total_customers: number;
  no_transaction_count: number;
  at_risk_count: number;
  by_cluster: ClusterKpi[];
}

export interface AcquisitionCostByChannel {
  acquisition_channel: string;
  avg_acquisition_cost: number;
}

export interface PopulationByProductsOwned {
  products_owned_count: number;
  customer_count: number;
}

export interface ProductOwnershipVsTenure {
  tenure_bucket: string;
  avg_products_owned: number;
}

export interface MostCommonProduct {
  product_type: string;
  ownership_count: number;
}

export interface DashboardSummaryResponse {
  kpi_cards: KpiCards;
  acquisition_cost_by_channel: AcquisitionCostByChannel[];
  population_by_products_owned: PopulationByProductsOwned[];
  product_ownership_vs_tenure: ProductOwnershipVsTenure[];
  most_common_products: MostCommonProduct[];
}

export interface CohortActivityEntry {
  cohort_month: string;
  activity_month: string;
  active_rate: number;
  cohort_size: number;
}

export interface ChannelM6RetentionEntry {
  acquisition_channel: string;
  cohort_month: string;
  m6_active_rate: number;
  cohort_size: number;
}

export interface DashboardAggregatesResponse {
  cohort_activity_matrix: CohortActivityEntry[];
  channel_m6_retention: ChannelM6RetentionEntry[];
}

export async function fetchDashboardSummary(): Promise<DashboardSummaryResponse> {
  const res = await fetch(`${BASE_URL}/dashboard/summary`);
  if (!res.ok) throw new Error(`GET /dashboard/summary failed: ${res.status}`);
  return res.json() as Promise<DashboardSummaryResponse>;
}

export async function fetchDashboardAggregates(): Promise<DashboardAggregatesResponse> {
  const res = await fetch(`${BASE_URL}/dashboard/aggregates`);
  if (!res.ok) throw new Error(`GET /dashboard/aggregates failed: ${res.status}`);
  return res.json() as Promise<DashboardAggregatesResponse>;
}

const _MODEL_LABELS: Record<string, string> = {
  "smart-auto": "Smart Auto",
};

export function formatProvenance(generated_at: string, model_used: string): string {
  const date = new Date(generated_at);
  const formatted = date.toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
  const label = _MODEL_LABELS[model_used] ?? model_used;
  return `Generated ${formatted} · ${label}`;
}
