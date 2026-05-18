import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ClusterBadge } from "@/components/ClusterBadge";
import { fetchCustomers, type CustomerSummary } from "@/lib/api";

const PAGE_SIZE = 50;
const ACTIVE_LIFECYCLE = "active_clustered";

const CLUSTERS = [
  { value: "all", label: "All clusters" },
  { value: "high_value_active", label: "High value active" },
  { value: "low_value_dormant", label: "Low value dormant" },
  { value: "at_risk_churner", label: "At risk churner" },
];

const CHANNELS = [
  { value: "all", label: "All channels" },
  { value: "paid_ads", label: "Paid ads" },
  { value: "organic", label: "Organic" },
  { value: "referral", label: "Referral" },
  { value: "partnership", label: "Partnership" },
];

type SortCol = "rfm_score" | "recency_days" | "monetary_total";
type SortOrder = "asc" | "desc";

function SkeletonRows({ count }: { count: number }) {
  return Array.from({ length: count }).map((_, i) => (
    <TableRow key={i}>
      {Array.from({ length: 7 }).map((_, j) => (
        <TableCell key={j}>
          <Skeleton className="h-4 w-full" />
        </TableCell>
      ))}
    </TableRow>
  ));
}

export function CustomersPage() {
  const navigate = useNavigate();
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const [cluster, setCluster] = useState("all");
  const [channel, setChannel] = useState("all");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [sort, setSort] = useState<SortCol>("rfm_score");
  const [order, setOrder] = useState<SortOrder>("desc");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    setPage(1);
  }, [cluster, channel, debouncedSearch, sort, order]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetchCustomers({
        lifecycle_stage: ACTIVE_LIFECYCLE,
        cluster: cluster === "all" ? undefined : cluster,
        channel: channel === "all" ? undefined : channel,
        q: debouncedSearch || undefined,
        sort,
        order,
        page,
        page_size: PAGE_SIZE,
      });
      setCustomers(resp.data);
      setTotal(resp.total);
    } finally {
      setLoading(false);
    }
  }, [cluster, channel, debouncedSearch, sort, order, page]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  function toggleSort(col: SortCol) {
    if (sort === col) {
      setOrder((o) => (o === "desc" ? "asc" : "desc"));
    } else {
      setSort(col);
      setOrder("desc");
    }
  }

  function SortArrow({ col }: { col: SortCol }) {
    if (sort !== col) return <span className="text-muted-foreground ml-1">↕</span>;
    return <span className="ml-1">{order === "desc" ? "↓" : "↑"}</span>;
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Customers</h1>
        <span className="text-muted-foreground text-sm">
          {loading ? "Loading…" : `${total.toLocaleString()} results`}
        </span>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <Input
          placeholder="Search name or email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-64 bg-card border-border"
        />
        <Select value={cluster} onValueChange={(v) => setCluster(v ?? "all")}>
          <SelectTrigger className="w-44 bg-card border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {CLUSTERS.map((c) => (
              <SelectItem key={c.value} value={c.value}>
                {c.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={channel} onValueChange={(v) => setChannel(v ?? "all")}>
          <SelectTrigger className="w-40 bg-card border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {CHANNELS.map((ch) => (
              <SelectItem key={ch.value} value={ch.value}>
                {ch.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Age</TableHead>
              <TableHead>State</TableHead>
              <TableHead>Cluster</TableHead>
              <TableHead
                className="cursor-pointer select-none"
                onClick={() => toggleSort("rfm_score")}
              >
                RFM Score <SortArrow col="rfm_score" />
              </TableHead>
              <TableHead
                className="cursor-pointer select-none"
                onClick={() => toggleSort("recency_days")}
              >
                Recency (days) <SortArrow col="recency_days" />
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <SkeletonRows count={10} />
            ) : customers.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={7}
                  className="text-center text-muted-foreground py-12"
                >
                  No customers match your filters.
                </TableCell>
              </TableRow>
            ) : (
              customers.map((c) => (
                <TableRow
                  key={c.customer_id}
                  className="cursor-pointer hover:bg-muted/30 border-border"
                  onClick={() => navigate(`/customers/${c.customer_id}`)}
                >
                  <TableCell className="font-medium">{c.name}</TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {c.email}
                  </TableCell>
                  <TableCell>{c.age}</TableCell>
                  <TableCell>{c.state}</TableCell>
                  <TableCell>
                    <ClusterBadge cluster={c.cluster_name} />
                  </TableCell>
                  <TableCell>
                    <span className="font-mono text-primary text-sm">
                      {c.rfm_score?.toFixed(2) ?? "—"}
                    </span>
                  </TableCell>
                  <TableCell>
                    <span className="font-mono text-sm">
                      {c.recency_days ?? "—"}
                    </span>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            Page {page} of {totalPages} — {total.toLocaleString()} customers
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 rounded-md border border-border bg-card hover:bg-muted/40 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1.5 rounded-md border border-border bg-card hover:bg-muted/40 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
