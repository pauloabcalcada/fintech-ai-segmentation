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
