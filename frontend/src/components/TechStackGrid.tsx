import { useState } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils";

type Tool = { name: string; category: string; why: string };

const CATEGORIES = ["ALL", "DATA", "ML & AI", "API", "FRONTEND", "OPS"] as const;

export function TechStackGrid() {
  const { t } = useTranslation();
  const [activeFilter, setActiveFilter] = useState<string>("ALL");

  const tools = t("landing.stack.tools", { returnObjects: true }) as Tool[];
  const filterAll = t("landing.stack.filterAll");

  const visible = activeFilter === "ALL"
    ? tools
    : tools.filter((tool) => tool.category === activeFilter);

  return (
    <div>
      <div className="mb-6 flex flex-wrap gap-2">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setActiveFilter(cat === "ALL" ? "ALL" : cat)}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-semibold transition-colors",
              (cat === "ALL" && activeFilter === "ALL") ||
              (cat !== "ALL" && activeFilter === cat)
                ? "border-amber-400 bg-amber-400 text-gray-900"
                : "border-border text-muted-foreground hover:border-primary/50 hover:text-foreground"
            )}
          >
            {cat === "ALL" ? filterAll : cat}
          </button>
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {visible.map((tool) => (
          <div
            key={tool.name}
            data-testid="stack-card"
            className="rounded-xl border border-border bg-card p-4"
          >
            <div className="mb-2 flex items-center justify-between">
              <span data-testid="card-name" className="font-semibold text-foreground">
                {tool.name}
              </span>
              <span
                data-testid="card-category"
                className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-semibold text-primary"
              >
                {tool.category}
              </span>
            </div>
            <p data-testid="card-why" className="text-sm leading-relaxed text-muted-foreground">
              {tool.why}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
