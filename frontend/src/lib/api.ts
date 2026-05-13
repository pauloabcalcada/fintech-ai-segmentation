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
  cached_recommendation: null;
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

export class NotFoundError extends Error {
  constructor() {
    super("Not found");
    this.name = "NotFoundError";
  }
}
