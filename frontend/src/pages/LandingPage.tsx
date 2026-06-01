import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { ArrowRight, ExternalLink, Sparkles } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { LandingNavbar } from "@/components/LandingNavbar";
import { TechStackGrid } from "@/components/TechStackGrid";
import dashboardPreview from "@/assets/dashboard-preview.png";


export function LandingPage() {
  const { t } = useTranslation();

  return (
    <div>
    <LandingNavbar />
    <main className="min-h-screen bg-background">
      {/* Hero — 01 */}
      <section className="mx-auto max-w-6xl px-6 pt-20 pb-16">
        <div className="grid grid-cols-1 gap-12 lg:grid-cols-2 lg:items-center">
          {/* Left — narrative */}
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border px-3 py-1 text-xs font-medium text-amber-400">
              {t("landing.hero.badge")}
            </div>
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
              {t("landing.hero.heading")}
            </h1>
            <p className="mt-4 text-base leading-relaxed text-muted-foreground sm:text-lg">
              {t("landing.hero.subhead")}
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
                className={cn(buttonVariants({ size: "lg" }), "cursor-pointer gap-2")}
              >
                {t("landing.hero.ctaCustomers")}
                <ArrowRight className="size-4" />
              </Link>
              <a
                href="https://github.com/pauloabcalcada/fintech-ai-segmentation"
                target="_blank"
                rel="noopener noreferrer"
                className={cn(buttonVariants({ size: "lg" }), "cursor-pointer gap-2")}
              >
                {t("landing.github.label")}
                <ExternalLink className="size-4" />
              </a>
            </div>
          </div>

          {/* Right — dashboard preview + AI agent card */}
          <div className="flex flex-col gap-3">
            <div
              data-testid="hero-browser-chrome"
              className="overflow-hidden rounded-xl border border-border bg-gray-900 shadow-2xl"
            >
              <div className="flex items-center gap-2 border-b border-border px-4 py-2.5">
                <span className="size-3 rounded-full bg-red-500" />
                <span className="size-3 rounded-full bg-yellow-500" />
                <span className="size-3 rounded-full bg-green-500" />
                <span className="ml-3 flex-1 rounded bg-gray-800 px-3 py-1 text-xs text-gray-400">
                  {t("landing.hero.urlBar")}
                </span>
              </div>
              <img
                src={dashboardPreview}
                alt="SynaptiqPay dashboard preview"
                className="w-full"
              />
            </div>

            {/* AI agent simulation card */}
            <div
              data-testid="hero-agent-card"
              className="rounded-xl border border-border bg-card p-4"
            >
              {/* Header */}
              <div className="mb-3 flex items-center gap-2">
                <Sparkles className="size-4 text-amber-400" />
                <span className="text-xs font-semibold uppercase tracking-widest text-amber-400">
                  {t("landing.hero.agentCard.label")}
                </span>
                <span className="ml-auto rounded-full bg-muted px-2 py-0.5 font-mono text-xs text-muted-foreground">
                  {t("landing.hero.agentCard.segment")}
                </span>
              </div>

              {/* Customer snapshot */}
              <p className="mb-3 text-xs text-muted-foreground">
                {t("landing.hero.agentCard.customerLine")}
              </p>

              {/* Offer row */}
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <span className="rounded-full border border-red-500 px-2 py-0.5 text-xs font-bold text-red-400">
                  {t("aiPanel.fields.riskLevels.critical").toUpperCase()}
                </span>
                <span className="rounded-full bg-amber-400/10 px-2 py-0.5 text-xs font-medium text-amber-400">
                  {t("landing.hero.agentCard.suggestedProduct")}
                </span>
              </div>

              {/* Notification text */}
              <p className="text-xs italic text-muted-foreground">
                &ldquo;{t("landing.hero.agentCard.notificationText")}&rdquo;
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Summary Block — case at a glance */}
      <section
        data-testid="summary-block"
        className="mx-auto max-w-6xl px-6 pb-16"
      >
        <div className="mb-8 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          {t("landing.summary.heading")}
        </div>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {(t("landing.summary.cards", { returnObjects: true }) as Array<{
            label: string; body: string;
          }>).map((card) => (
            <div
              key={card.label}
              data-testid="summary-card"
              className="border-l-2 border-amber-400 bg-card pl-4 py-2"
            >
              <div className="mb-2 text-xs uppercase tracking-widest text-muted-foreground">
                {card.label}
              </div>
              <p className="text-sm leading-relaxed text-foreground">{card.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Methodology — 02 */}
      <section
        id="methodology"
        data-testid="methodology-section"
        className="mx-auto max-w-6xl scroll-mt-16 px-6 py-16"
      >
        <div className="mb-2 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          {t("landing.methodology.sectionLabel")}
        </div>
        <h2 className="mb-10 text-3xl font-bold tracking-tight text-foreground">
          {t("landing.methodology.heading")}
        </h2>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {(t("landing.methodology.phases", { returnObjects: true }) as Array<{
            number: string; title: string; description: string; tools: string[];
          }>).map((phase) => (
            <div
              key={phase.number}
              data-testid="phase"
              className="flex flex-col rounded-xl border border-border bg-card p-5"
            >
              <div className="mb-2 text-2xl font-bold text-amber-400">{phase.number}</div>
              <h3 className="mb-2 font-semibold text-foreground">{phase.title}</h3>
              <p className="mb-4 flex-1 text-sm leading-relaxed text-muted-foreground">
                {phase.description}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {phase.tools.map((tool) => (
                  <span
                    key={tool}
                    className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                  >
                    {tool}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div
          data-testid="methodology-callout"
          className="mt-8 border-l-2 border-amber-400 bg-muted px-4 py-3"
        >
          <p className="text-sm leading-relaxed text-foreground">
            {t("landing.methodology.callout")}
          </p>
        </div>
      </section>

      {/* Deliverables — What Was Built */}
      <section
        id="deliverables"
        data-testid="deliverables-section"
        className="mx-auto max-w-6xl scroll-mt-16 px-6 py-16"
      >
        <div className="mb-10 text-xs uppercase tracking-widest text-muted-foreground">
          {t("landing.deliverables.label")}
        </div>

        {/* Product 01 — Business Dashboard */}
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-2 lg:items-center">
          <div>
            <div className="mb-3 inline-flex items-center rounded-full border border-border px-3 py-1 text-xs font-medium text-amber-400">
              {t("landing.deliverables.product1.badge")}
            </div>
            <h3 className="mb-4 text-2xl font-bold tracking-tight text-foreground">
              {t("landing.deliverables.product1.title")}
            </h3>
            <p className="mb-6 text-base leading-relaxed text-muted-foreground">
              {t("landing.deliverables.product1.body")}
            </p>
            <Link
              to="/dashboard"
              className={cn(buttonVariants({ variant: "outline" }), "cursor-pointer gap-2")}
            >
              {t("landing.deliverables.product1.cta")}
              <ArrowRight className="size-4" />
            </Link>
          </div>
          <div
            data-testid="deliverable-browser-chrome"
            className="overflow-hidden rounded-xl border border-border bg-gray-900 shadow-2xl"
          >
            <div className="flex items-center gap-2 border-b border-border px-4 py-2.5">
              <span className="size-3 rounded-full bg-red-500" />
              <span className="size-3 rounded-full bg-yellow-500" />
              <span className="size-3 rounded-full bg-green-500" />
              <span className="ml-3 flex-1 rounded bg-gray-800 px-3 py-1 text-xs text-gray-400">
                {t("landing.deliverables.product1.urlBar")}
              </span>
            </div>
            <img
              src={dashboardPreview}
              alt={t("landing.deliverables.product1.alt")}
              className="w-full"
            />
          </div>
        </div>

        {/* Product 02 — AI Recommendation Agent */}
        <div className="mt-16 grid grid-cols-1 gap-10 lg:grid-cols-2 lg:items-center">
          <div>
            <div className="mb-3 inline-flex items-center rounded-full border border-border px-3 py-1 text-xs font-medium text-amber-400">
              {t("landing.deliverables.product2.badge")}
            </div>
            <h3 className="mb-4 flex items-center gap-2 text-2xl font-bold tracking-tight text-foreground">
              <Sparkles data-testid="deliverable-sparkles" className="size-6 text-amber-400" />
              {t("landing.deliverables.product2.title")}
            </h3>
            <p className="mb-3 text-base leading-relaxed text-muted-foreground">
              {t("landing.deliverables.product2.body")}
            </p>
            <p className="mb-6 text-base leading-relaxed text-muted-foreground">
              {t("landing.deliverables.product2.bodyDynamic")}
            </p>
            <Link
              to="/customers"
              className={cn(buttonVariants({ variant: "outline" }), "cursor-pointer gap-2")}
            >
              {t("landing.deliverables.product2.cta")}
              <ArrowRight className="size-4" />
            </Link>
          </div>
          <div
            data-testid="deliverable-code"
            className="grid grid-cols-1 gap-4 sm:grid-cols-2"
          >
            <pre className="overflow-x-auto rounded-xl border border-border bg-secondary p-4 font-mono text-xs leading-relaxed text-foreground">
              <span className="text-muted-foreground">{"// agent input (per customer)\n"}</span>
              {"{\n"}
              {"  "}<span className="text-amber-400">customer_name</span>{": \"Ana Souza\",\n"}
              {"  "}<span className="text-amber-400">cluster_name</span>{": \"at_risk_churner\",\n"}
              {"  "}<span className="text-amber-400">cluster_position</span>{": \"bottom_20\",\n"}
              {"  "}<span className="text-amber-400">lifecycle_stage</span>{": \"dormant\",\n"}
              {"  "}<span className="text-amber-400">rfm_score</span>{": 1.4,\n"}
              {"  "}<span className="text-amber-400">cluster_avg_rfm</span>{": 1.61,\n"}
              {"  "}<span className="text-amber-400">recency_score</span>{": 1,\n"}
              {"  "}<span className="text-amber-400">frequency_score</span>{": 1,\n"}
              {"  "}<span className="text-amber-400">monetary_score</span>{": 2,\n"}
              {"  "}<span className="text-amber-400">recency_days</span>{": 92,\n"}
              {"  "}<span className="text-amber-400">products_owned</span>{": [\"wallet\"],\n"}
              {"  "}<span className="text-amber-400">acquisition_channel</span>{": \"paid_ads\",\n"}
              {"  "}<span className="text-amber-400">acquisition_cost</span>{": 280.0,\n"}
              {"  "}<span className="text-amber-400">tenure_months</span>{": 8,\n"}
              {"  "}<span className="text-amber-400">cohort_health</span>{": \"n/a\",\n"}
              {"  "}<span className="text-amber-400">activity_trend</span>{":\n"}
              {"    \"2025-07: 3 tx (R$42);\n"}
              {"     2025-08: 1 tx (R$15)\"\n"}
              {"}"}
            </pre>
            <pre className="overflow-x-auto rounded-xl border border-border bg-secondary p-4 font-mono text-xs leading-relaxed text-foreground">
              <span className="text-muted-foreground">{"// agent output\n"}</span>
              {"{\n"}
              {"  "}<span className="text-amber-400">risk_level</span>{": \"critical\",\n"}
              {"  "}<span className="text-amber-400">recommended_action</span>{":\n"}
              {"    \"immediate retention offer\",\n"}
              {"  "}<span className="text-amber-400">suggested_product</span>{":\n"}
              {"    \"cashback credit card\",\n"}
              {"  "}<span className="text-amber-400">message_tone</span>{":\n"}
              {"    \"urgent, empathetic\",\n"}
              {"  "}<span className="text-amber-400">notification_text</span>{":\n"}
              {"    \"Exclusive offer just for you\n"}
              {"     — unlock cashback on every\n"}
              {"     purchase today.\",\n"}
              {"  "}<span className="text-amber-400">reasoning</span>{":\n"}
              {"    \"Registered via paid_ads 8mo\n"}
              {"     ago (R$280 CAC). Low RFM,\n"}
              {"     92 days silent, wallet only.\n"}
              {"     Credit card offer could\n"}
              {"     reactivate before churn.\",\n"}
              {"  "}<span className="text-amber-400">strategy_used</span>{": \"retention\"\n"}
              {"}"}
            </pre>
          </div>
        </div>

        {/* Tool logo placeholder row */}
        {/* TODO: replace placeholders with actual tool logo <img> tags when assets are provided */}
        <div className="mt-16 flex flex-wrap gap-4">
          {Array.from({ length: 6 }).map((_, idx) => (
            <div
              key={idx}
              data-testid="logo-placeholder"
              className="w-12 h-12 rounded bg-muted flex items-center justify-center text-xs text-muted-foreground"
            >
              logo
            </div>
          ))}
        </div>
      </section>

      {/* Stack and Architecture — 06 */}
      <section
        id="stack"
        data-testid="stack-section"
        className="mx-auto max-w-6xl scroll-mt-16 px-6 py-16"
      >
        <div className="mb-2 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          {t("landing.stack.sectionLabel")}
        </div>
        <h2 className="mb-10 text-3xl font-bold tracking-tight text-foreground">
          {t("landing.stack.heading")}
        </h2>

        {/* Top half — Architecture workflow diagram */}
        <div
          data-testid="arch-workflow"
          className="mb-12 flex flex-col items-center gap-4 lg:flex-row lg:justify-between"
        >
          {["Faker", "Pandas", "Supabase", "FastAPI", "LangGraph", "React"].map(
            (node, idx, arr) => (
              <div key={node} className="flex flex-col items-center gap-4 lg:flex-row">
                {/* TODO: replace logo placeholder with <img src={...} alt="Faker" /> when asset is available */}
                <div
                  data-testid="arch-node"
                  className="flex flex-col items-center gap-2"
                >
                  <div className="w-12 h-12 rounded bg-muted flex items-center justify-center text-xs text-muted-foreground">
                    logo
                  </div>
                  <span className="text-sm font-medium text-foreground">{node}</span>
                </div>
                {idx < arr.length - 1 && (
                  <span
                    data-testid="arch-arrow"
                    className="text-muted-foreground"
                    aria-hidden="true"
                  >
                    <span className="hidden lg:inline">→</span>
                    <span className="lg:hidden">↓</span>
                  </span>
                )}
              </div>
            )
          )}
        </div>

        {/* Bottom half — Filterable tech stack */}
        <div data-testid="tech-stack">
          <TechStackGrid />
        </div>
      </section>

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
                      ? "text-amber-400 border border-amber-400"
                      : phase.status === "ACTIVE"
                      ? "text-muted-foreground border border-muted"
                      : "text-gray-500 border border-gray-600"
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
      <footer className="border-t border-border bg-[#0d0f14] px-6 py-12">
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
                <li><a href="#methodology" className="hover:text-white transition-colors">{t("landing.footer.methodology")}</a></li>
                <li><a href="#deliverables" className="hover:text-white transition-colors">{t("landing.footer.deliverables")}</a></li>
                <li><a href="#stack" className="hover:text-white transition-colors">{t("landing.footer.stack")}</a></li>
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
          <div
            data-testid="footer-disclaimer"
            className="mt-4 text-center text-xs text-muted-foreground"
          >
            {t("landing.footer.disclaimer")}
          </div>
        </div>
      </footer>
    </main>
    </div>
  );
}
