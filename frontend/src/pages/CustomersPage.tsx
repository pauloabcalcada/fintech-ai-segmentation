import { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
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


type SortCol = "rfm_score" | "recency_days" | "monetary_total";
type SortOrder = "asc" | "desc";

function SkeletonRows({ count }: { count: number }) {
  return Array.from({ length: count }).map((_, i) => (
    <TableRow key={i}>
      {Array.from({ length: 5 }).map((_, j) => (
        <TableCell key={j}>
          <Skeleton className="h-4 w-full" />
        </TableCell>
      ))}
    </TableRow>
  ));
}

export function CustomersPage() {
  const { t } = useTranslation();
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

  const CLUSTERS = [
    { value: "all", label: t("customers.allClusters") },
    { value: "high_value_active", label: t("customers.highValueActive") },
    { value: "low_value_dormant", label: t("customers.lowValueDormant") },
    { value: "at_risk_churner", label: t("customers.atRiskChurner") },
  ];

  const CHANNELS = [
    { value: "all", label: t("customers.allChannels") },
    { value: "paid_ads", label: t("customers.paidAds") },
    { value: "organic", label: t("customers.organic") },
    { value: "referral", label: t("customers.referral") },
    { value: "partnership", label: t("customers.partnership") },
  ];

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
        <h1 className="text-xl font-semibold">{t("customers.title")}</h1>
        <span className="text-muted-foreground text-sm">
          {loading ? t("customers.loading") : t("customers.results", { count: total.toLocaleString() })}
        </span>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <Input
          placeholder={t("customers.searchPlaceholder")}
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
              <TableHead>{t("customers.col.name")}</TableHead>
              <TableHead>{t("customers.col.age")}</TableHead>
              <TableHead>{t("customers.col.state")}</TableHead>
              <TableHead>{t("customers.col.cluster")}</TableHead>
              <TableHead
                className="cursor-pointer select-none"
                onClick={() => toggleSort("recency_days")}
              >
                {t("customers.col.recency")} <SortArrow col="recency_days" />
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <SkeletonRows count={10} />
            ) : customers.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="text-center text-muted-foreground py-12"
                >
                  {t("customers.noResults")}
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
                  <TableCell>{c.age}</TableCell>
                  <TableCell>{c.state}</TableCell>
                  <TableCell>
                    <ClusterBadge cluster={c.cluster_name} />
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
            {t("customers.pagination", { page, total: totalPages, count: total.toLocaleString() })}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 rounded-md border border-border bg-card hover:bg-muted/40 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {t("customers.prev")}
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1.5 rounded-md border border-border bg-card hover:bg-muted/40 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {t("customers.next")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
