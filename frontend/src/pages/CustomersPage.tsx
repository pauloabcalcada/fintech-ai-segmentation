import React, { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { ClusterBadge } from "@/components/ClusterBadge";
import { CustomerDetailInline } from "@/components/CustomerDetailInline";
import {
  fetchCustomerSample,
  type CustomerSummary,
  type CustomerProfileResponse,
} from "@/lib/api";
import { InfoTooltip } from "@/components/ui/InfoTooltip";
import { Info, RotateCcw } from "lucide-react";

function SkeletonRows({ count }: { count: number }) {
  return Array.from({ length: count }).map((_, i) => (
    <TableRow key={i}>
      {Array.from({ length: 4 }).map((_, j) => (
        <TableCell key={j}>
          <Skeleton className="h-4 w-full" />
        </TableCell>
      ))}
    </TableRow>
  ));
}

export function CustomersPage() {
  const { t } = useTranslation();
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [profileCache, setProfileCache] = useState<Map<string, CustomerProfileResponse>>(new Map());

  const load = useCallback(async () => {
    setLoading(true);
    setExpandedId(null);
    setProfileCache(new Map());
    try {
      const resp = await fetchCustomerSample(3);
      setCustomers(resp.data);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleProfileLoaded = useCallback((customerId: string, data: CustomerProfileResponse) => {
    setProfileCache((prev) => new Map(prev).set(customerId, data));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function handleRowClick(id: string) {
    setExpandedId((prev) => (prev === id ? null : id));
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">{t("customers.title")}</h1>
          <p className="text-sm text-muted-foreground mt-0.5">{t("customers.expandHint")}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-muted-foreground text-sm">
            {loading
              ? t("customers.loading")
              : t("customers.results", { count: customers.length.toLocaleString() })}
          </span>
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-border bg-card text-sm hover:bg-muted/40 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ↻ {t("customers.refresh")}
          </button>
        </div>
      </div>

      {/* Disclosure banner */}
      <div className="flex items-start gap-2 rounded-md border border-border bg-muted/30 px-3 py-2">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        <p className="text-xs text-muted-foreground">{t("customers.disclosure")}</p>
      </div>

      {/* Rotate hint — mobile only */}
      <div className="flex items-center gap-2 rounded-md border border-amber-400/30 bg-amber-400/5 px-3 py-2 sm:hidden">
        <RotateCcw className="h-3.5 w-3.5 shrink-0 text-amber-400" />
        <p className="text-xs text-amber-400">
          {t("customers.rotateHint", "For a better experience, rotate your phone to landscape.")}
        </p>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead>{t("customers.col.name")}</TableHead>
              <TableHead>{t("customers.col.age")}</TableHead>
              <TableHead>{t("customers.col.state")}</TableHead>
              <TableHead>
                {t("customers.col.cluster")}
                <InfoTooltip text={t("customers.clusterTooltip")} side="left" />
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <SkeletonRows count={9} />
            ) : customers.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={4}
                  className="text-center text-muted-foreground py-12"
                >
                  {t("customers.noResults")}
                </TableCell>
              </TableRow>
            ) : (
              customers.map((c) => (
                <React.Fragment key={c.customer_id}>
                  <TableRow
                    className="cursor-pointer hover:bg-muted/30 border-border"
                    onClick={() => handleRowClick(c.customer_id)}
                    data-testid={`customer-row-${c.customer_id}`}
                  >
                    <TableCell className="font-medium">{c.name}</TableCell>
                    <TableCell>{c.age}</TableCell>
                    <TableCell>{c.state}</TableCell>
                    <TableCell>
                      <ClusterBadge cluster={c.cluster_name} />
                    </TableCell>
                  </TableRow>
                  {expandedId === c.customer_id && (
                    <TableRow>
                      <TableCell colSpan={4} className="p-0 whitespace-normal">
                        <CustomerDetailInline
                          customerId={c.customer_id}
                          cachedData={profileCache.get(c.customer_id)}
                          onLoaded={handleProfileLoaded}
                        />
                      </TableCell>
                    </TableRow>
                  )}
                </React.Fragment>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
