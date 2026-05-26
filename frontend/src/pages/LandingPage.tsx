import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { ArrowRight, ExternalLink } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { LandingNavbar } from "@/components/LandingNavbar";

const TECH_STACK = [
  "Faker", "Pandas", "Scikit-learn", "LangGraph",
  "FastAPI", "React", "Supabase", "Vercel", "Fly.io",
];

const HERO_METRICS = [
  { label: "customers_generated", value: "8,000" },
  { label: "planted_segments", value: "4" },
  { label: "operational_clusters_k", value: "3" },
  { label: "months_of_history", value: "50" },
  { label: "avg_recommendation_latency", value: "1.4s" },
  { label: "agent_routes", value: "4" },
];

export function LandingPage() {
  const { t } = useTranslation();

  return (
    <div className="dark">
    <LandingNavbar />
    <main className="min-h-screen bg-background">
      {/* Hero — 01 */}
      <section className="mx-auto max-w-6xl px-6 pt-20 pb-16">
        <div className="grid grid-cols-1 gap-12 lg:grid-cols-2 lg:items-center">
          {/* Left — STAR narrative */}
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
              01 · SynaptiqPay · AI Segmentation
            </div>
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
              {t("landing.hero.heading")}
            </h1>
            <p className="mt-4 text-base leading-relaxed text-muted-foreground sm:text-lg">
              {t("landing.hero.situation")}
            </p>
            <p className="mt-3 text-base leading-relaxed text-muted-foreground sm:text-lg">
              {t("landing.hero.result")}
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                to="/dashboard"
                className={cn(buttonVariants({ size: "lg" }), "cursor-pointer gap-2")}
              >
                {t("landing.hero.cta")}
                <ArrowRight className="size-4" />
              </Link>
              <Link
                to="/customers"
                className={cn(buttonVariants({ variant: "outline", size: "lg" }), "cursor-pointer gap-2")}
              >
                {t("landing.hero.ctaCustomers")}
              </Link>
              <a
                href="https://github.com/pauloabcalcada/fintech-ai-segmentation"
                target="_blank"
                rel="noopener noreferrer"
                className={cn(buttonVariants({ variant: "ghost", size: "lg" }), "cursor-pointer gap-2")}
              >
                <ExternalLink className="size-4" />
                {t("landing.github.label")}
              </a>
            </div>
          </div>

          {/* Right — terminal metrics panel */}
          <div
            data-testid="hero-metrics"
            className="rounded-xl border border-border bg-gray-950 p-5 font-mono text-sm"
          >
            <div className="mb-3 flex items-center gap-2">
              <span className="size-3 rounded-full bg-red-500" />
              <span className="size-3 rounded-full bg-yellow-500" />
              <span className="size-3 rounded-full bg-green-500" />
              <span className="ml-2 text-xs text-gray-500">synaptiqpay_ai_seg — dataset stats</span>
            </div>
            <div className="space-y-1.5">
              {HERO_METRICS.map(({ label, value }) => (
                <div key={label} className="flex items-center gap-2">
                  <span className="text-green-400">›</span>
                  <span className="text-gray-400">{label}:</span>
                  <span className="font-semibold text-white">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-3xl space-y-10 px-6 pb-24">
        {/* What this is */}
        <section className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-3 text-lg font-semibold text-foreground">
            {t("landing.about.heading")}
          </h2>
          <p className="text-sm leading-relaxed text-muted-foreground">
            {t("landing.about.body")}
          </p>
        </section>

        {/* Tech Stack */}
        <section data-testid="tech-stack" className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-4 text-lg font-semibold text-foreground">
            {t("landing.stack.heading")}
          </h2>
          <div className="flex flex-wrap gap-2">
            {TECH_STACK.map((tech) => (
              <Badge key={tech} variant="secondary" className="text-sm">
                {tech}
              </Badge>
            ))}
          </div>
        </section>

        {/* Out of Scope */}
        <section data-testid="out-of-scope" className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-4 text-lg font-semibold text-foreground">
            {t("landing.outOfScope.heading")}
          </h2>
          <ul className="space-y-2 text-sm text-muted-foreground">
            {(
              [
                "cacPayback",
                "churnModel",
                "ltvHeatmap",
                "chatbot",
              ] as const
            ).map((key) => (
              <li key={key} className="flex gap-2">
                <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                {t(`landing.outOfScope.${key}`)}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
    </div>
  );
}
