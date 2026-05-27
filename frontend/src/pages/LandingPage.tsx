import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { ArrowRight, ExternalLink } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { LandingNavbar } from "@/components/LandingNavbar";
import { TechStackGrid } from "@/components/TechStackGrid";
import dashboardPreview from "@/assets/dashboard-preview.png";


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
    <div>
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
            className="rounded-xl border border-border bg-gray-950 dark:bg-white p-5 font-mono text-sm"
          >
            <div className="mb-3 flex items-center gap-2">
              <span className="size-3 rounded-full bg-red-500" />
              <span className="size-3 rounded-full bg-yellow-500" />
              <span className="size-3 rounded-full bg-green-500" />
              <span className="ml-2 text-xs text-gray-500 dark:text-gray-600">synaptiqpay_ai_seg — dataset stats</span>
            </div>
            <div className="space-y-1.5">
              {HERO_METRICS.map(({ label, value }) => (
                <div key={label} className="flex items-center gap-2">
                  <span className="text-green-400 dark:text-green-600">›</span>
                  <span className="text-gray-400 dark:text-gray-700">{label}:</span>
                  <span className="font-semibold text-white dark:text-gray-900">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* How It Works — 02 */}
      <section
        id="how-it-works"
        className="mx-auto max-w-6xl scroll-mt-16 px-6 py-16"
      >
        <div className="mb-2 text-xs font-semibold uppercase tracking-widest text-primary">
          {t("landing.howItWorks.sectionLabel")}
        </div>
        <h2 className="mb-10 text-3xl font-bold tracking-tight text-foreground">
          {t("landing.howItWorks.heading")}
        </h2>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {(t("landing.howItWorks.cards", { returnObjects: true }) as Array<{
            badge: string; category: string; title: string; why: string;
          }>).map((card) => (
            <div
              key={card.badge}
              className="rounded-xl border border-border bg-card p-5"
            >
              <div className="mb-3 flex items-center gap-2">
                <span className="flex size-7 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                  {card.badge}
                </span>
                <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                  {card.category}
                </span>
              </div>
              <h3 className="mb-2 font-semibold text-foreground">{card.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{card.why}</p>
            </div>
          ))}
        </div>
      </section>

      {/* AI Agent — 05 */}
      <section
        id="ai-agent"
        className="mx-auto max-w-6xl scroll-mt-16 px-6 py-16"
      >
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-2 lg:items-start">
          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-widest text-primary">
              {t("landing.agent.sectionLabel")}
            </div>
            <h2 className="mb-4 text-3xl font-bold tracking-tight text-foreground">
              {t("landing.agent.heading")}
            </h2>
            <p className="text-base leading-relaxed text-muted-foreground">
              {t("landing.agent.body")}
            </p>
          </div>
          <div className="space-y-4">
            {/* Terminal panels */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-border bg-gray-950 dark:bg-white p-4 font-mono text-xs">
                <div className="mb-2 text-gray-500 dark:text-gray-600">// input</div>
                {[
                  ["segment", '"at_risk_churner"'],
                  ["rfm_score", "1.4"],
                  ["recency_days", "92"],
                  ["frequency_score", "1"],
                  ["monetary_score", "1"],
                  ["cohort_health", '"weak — 38%"'],
                  ["products_owned", '["wallet"]'],
                  ["acquisition_channel", '"paid_ads"'],
                  ["acquisition_cost", "280.0"],
                  ["tenure_months", "8"],
                ].map(([k, v]) => (
                  <div key={k} className="flex gap-1">
                    <span className="text-blue-400 dark:text-blue-600">{k}</span>
                    <span className="text-gray-500 dark:text-gray-600">:</span>
                    <span className="text-green-300 dark:text-green-700">{v}</span>
                  </div>
                ))}
              </div>
              <div className="rounded-xl border border-border bg-gray-950 dark:bg-white p-4 font-mono text-xs">
                <div className="mb-2 text-gray-500 dark:text-gray-600">// output</div>
                {[
                  ["risk_level", '"critical"'],
                  ["recommended_action", '"retention offer"'],
                  ["suggested_product", '"cashback card"'],
                  ["message_tone", '"urgent, empathetic"'],
                  ["reasoning", '"8mo tenure, R$280…"'],
                ].map(([k, v]) => (
                  <div key={k} className="flex gap-1">
                    <span className="text-blue-400 dark:text-blue-600">{k}</span>
                    <span className="text-gray-500 dark:text-gray-600">:</span>
                    <span className="text-green-300 dark:text-green-700">{v}</span>
                  </div>
                ))}
              </div>
            </div>
            {/* Node flow */}
            <div
              data-testid="agent-node-flow"
              className="flex flex-wrap items-center gap-2 rounded-xl border border-border bg-card p-4"
            >
              {[
                "fetch_customer_profile",
                "analyze_segment",
                "assess_products",
                "generate_recommendation",
                "validate_output",
              ].map((node, idx, arr) => (
                <div key={node} className="flex items-center gap-2">
                  <span
                    data-testid="agent-node"
                    className="rounded-lg border border-primary/30 bg-primary/10 px-2 py-1 text-xs font-mono text-primary"
                  >
                    {node}
                  </span>
                  {idx < arr.length - 1 && (
                    <span className="text-muted-foreground">→</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Dashboard Preview — 04 */}
      <section
        id="dashboard"
        className="mx-auto max-w-6xl scroll-mt-16 px-6 py-16"
      >
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-2 lg:items-center">
          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-widest text-primary">
              {t("landing.dashboard.sectionLabel")}
            </div>
            <h2 className="mb-4 text-3xl font-bold tracking-tight text-foreground">
              {t("landing.dashboard.heading")}
            </h2>
            <p className="text-base leading-relaxed text-muted-foreground">
              {t("landing.dashboard.body")}
            </p>
          </div>
          <div>
            <div
              data-testid="browser-chrome"
              className="overflow-hidden rounded-xl border border-border bg-gray-900 shadow-2xl"
            >
              <div className="flex items-center gap-2 border-b border-border px-4 py-2.5">
                <span className="size-3 rounded-full bg-red-500" />
                <span className="size-3 rounded-full bg-yellow-500" />
                <span className="size-3 rounded-full bg-green-500" />
                <span className="ml-3 flex-1 rounded bg-gray-800 px-3 py-1 text-xs text-gray-400">
                  {t("landing.dashboard.urlBar")}
                </span>
              </div>
              <img
                src={dashboardPreview}
                alt="SynaptiqPay dashboard preview"
                className="w-full"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Pipeline — 03 */}
      <section
        data-testid="pipeline-section"
        className="mx-auto max-w-2xl px-6 py-16"
      >
        <div className="mb-2 text-xs font-semibold uppercase tracking-widest text-primary">
          {t("landing.pipeline.sectionLabel")}
        </div>
        <h2 className="mb-10 text-3xl font-bold tracking-tight text-foreground">
          {t("landing.pipeline.heading")}
        </h2>
        <div className="flex flex-col items-center">
          {(t("landing.pipeline.steps", { returnObjects: true }) as Array<{
            title: string; tools: string[];
          }>).map((step, idx, arr) => (
            <div key={step.title} className="flex w-full flex-col items-center">
              <div
                data-testid="pipeline-step"
                className="w-full rounded-xl border border-border bg-card p-4"
              >
                <p className="mb-2 font-semibold text-foreground">{step.title}</p>
                <div className="flex flex-wrap gap-1.5">
                  {step.tools.map((tool) => (
                    <span
                      key={tool}
                      className="rounded-full border border-primary/20 bg-primary/10 px-2 py-0.5 text-xs text-primary"
                    >
                      {tool}
                    </span>
                  ))}
                </div>
              </div>
              {idx < arr.length - 1 && (
                <div className="h-8 w-px border-l-2 border-dashed border-border" />
              )}
            </div>
          ))}
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

        {/* Tech Stack — 06 */}
        <section data-testid="tech-stack" className="rounded-xl border border-border bg-card p-6">
          <div className="mb-2 text-xs font-semibold uppercase tracking-widest text-primary">
            {t("landing.stack.sectionLabel")}
          </div>
          <h2 className="mb-6 text-lg font-semibold text-foreground">
            {t("landing.stack.heading")}
          </h2>
          <TechStackGrid />
        </section>

      </div>

      {/* Roadmap — 07 */}
      <section
        id="roadmap"
        className="mx-auto max-w-6xl scroll-mt-16 px-6 py-16"
      >
        <div className="mb-2 text-xs font-semibold uppercase tracking-widest text-primary">
          {t("landing.roadmap.sectionLabel")}
        </div>
        <h2 className="mb-10 text-3xl font-bold tracking-tight text-foreground">
          {t("landing.roadmap.heading")}
        </h2>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          {(t("landing.roadmap.phases", { returnObjects: true }) as Array<{
            phase: string; title: string; status: string; items: string[];
          }>).map((phase) => (
            <div
              key={phase.phase}
              data-testid="roadmap-card"
              className="rounded-xl border border-border bg-card p-5"
            >
              <div className="mb-3 flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                  {phase.phase}
                </span>
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-xs font-bold",
                    phase.status === "SHIPPED"
                      ? "bg-green-500/10 text-green-400"
                      : phase.status === "ACTIVE"
                      ? "bg-blue-500/10 text-blue-400"
                      : "bg-gray-500/10 text-gray-400"
                  )}
                >
                  {phase.status}
                </span>
              </div>
              <h3 className="mb-3 font-semibold text-foreground">{phase.title}</h3>
              <ul className="space-y-1.5">
                {phase.items.map((item) => (
                  <li key={item} className="flex gap-2 text-sm text-muted-foreground">
                    <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-gray-950/80 px-6 py-12">
        <div className="mx-auto max-w-6xl">
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
            <div>
              <h4 className="mb-3 text-sm font-bold text-white">{t("landing.footer.projectCol")}</h4>
              <ul className="space-y-2 text-sm text-white/70">
                <li>
                  <a
                    href="https://github.com/pauloabcalcada/fintech-ai-segmentation"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-white transition-colors"
                  >
                    {t("landing.footer.githubRepo")}
                  </a>
                </li>
                <li>
                  <Link to="/dashboard" className="hover:text-white transition-colors">
                    {t("landing.footer.liveDemo")}
                  </Link>
                </li>
                <li>
                  <a href="#roadmap" className="hover:text-white transition-colors">
                    {t("landing.footer.roadmapLink")}
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="mb-3 text-sm font-bold text-white">{t("landing.footer.sectionsCol")}</h4>
              <ul className="space-y-2 text-sm text-white/70">
                <li><a href="#how-it-works" className="hover:text-white transition-colors">{t("landing.footer.howItWorks")}</a></li>
                <li><a href="#dashboard" className="hover:text-white transition-colors">{t("landing.footer.problem")}</a></li>
                <li><a href="#ai-agent" className="hover:text-white transition-colors">{t("landing.footer.aiAgent")}</a></li>
              </ul>
            </div>
            <div>
              <h4 className="mb-3 text-sm font-bold text-white">{t("landing.footer.contactCol")}</h4>
              <ul className="space-y-2 text-sm text-white/70">
                <li>
                  <a href="mailto:pauloabcalcada@gmail.com" className="hover:text-white transition-colors">
                    pauloabcalcada@gmail.com
                  </a>
                </li>
                <li>
                  <a href="https://github.com/pauloabcalcada" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
                    github.com/pauloabcalcada
                  </a>
                </li>
                <li>
                  <a href="https://linkedin.com/in/paulo-calcada" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
                    linkedin.com/in/paulo-calcada
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="mt-10 border-t border-white/10 pt-6 text-center text-xs text-white/50">
            {t("landing.footer.copyright")}
          </div>
        </div>
      </footer>
    </main>
    </div>
  );
}
