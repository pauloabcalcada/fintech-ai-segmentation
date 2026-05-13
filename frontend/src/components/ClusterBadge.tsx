import { Badge } from "@/components/ui/badge";

const CLUSTER_STYLES: Record<string, string> = {
  high_value_active: "bg-emerald-950 text-emerald-300 border-emerald-800",
  mid_value_regular: "bg-blue-950 text-blue-300 border-blue-800",
  low_value_dormant: "bg-zinc-800 text-zinc-400 border-zinc-700",
  at_risk_churner: "bg-red-950 text-red-300 border-red-800",
};

export function ClusterBadge({ cluster }: { cluster: string | null }) {
  if (!cluster) return <span className="text-muted-foreground text-xs">—</span>;
  const style = CLUSTER_STYLES[cluster] ?? "bg-muted text-muted-foreground";
  return (
    <Badge
      variant="outline"
      className={`font-mono text-xs ${style}`}
    >
      {cluster.replace(/_/g, " ")}
    </Badge>
  );
}
