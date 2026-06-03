import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { ArrowRight, ExternalLink, Sparkles, Mail } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { LandingNavbar } from "@/components/LandingNavbar";
import { useTheme } from "@/context/ThemeContext";
import { TechStackGrid } from "@/components/TechStackGrid";
import dashboardPreview from "@/assets/dashboard-preview.png";
import architectureLight from "@/assets/architecture-light.png";
import architectureDark from "@/assets/architecture-dark.png";


export function LandingPage() {
  const { t } = useTranslation();
  const { theme } = useTheme();

  return (
    <div>
    <LandingNavbar />
    <main className="min-h-screen bg-background">
      {/* Hero — 01 */}
      <section className="mx-auto max-w-6xl px-6 pt-20 pb-16">
        {/* Badge + heading — full width */}
        <div className="mb-6">
<h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            {t("landing.hero.heading")}
          </h1>
        </div>

        {/* Subhead paragraphs (left) + images (right) — centered against each other */}
        <div className="grid grid-cols-1 gap-12 lg:grid-cols-2 lg:items-center">
          <div>
            <p className="text-base leading-relaxed text-muted-foreground sm:text-lg text-justify indent-8">
              {t("landing.hero.subhead1")}
            </p>
            <p className="mt-3 text-base leading-relaxed text-muted-foreground sm:text-lg text-justify indent-8">
              {t("landing.hero.subhead2")}
            </p>
            <p className="mt-3 text-base leading-relaxed text-muted-foreground sm:text-lg text-justify indent-8">
              {t("landing.hero.subhead3")}
            </p>
          </div>

          {/* Right — dashboard preview + AI agent card */}
          <div className="flex flex-col gap-3">
            <div
              data-testid="hero-browser-chrome"
              className="overflow-hidden rounded-xl border border-border shadow-2xl"
            >
              <img
                src={dashboardPreview}
                alt="SynaptiqPay dashboard preview"
                className="w-full block"
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

        {/* CTAs — full width below the two-column block */}
        <div className="mt-8 flex flex-wrap gap-3 justify-center">
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

        {/* Top half — Architecture diagram */}
        <div data-testid="arch-workflow" className="mb-12 overflow-hidden">
          <img
            src={theme === "dark" ? architectureDark : architectureLight}
            alt="Project architecture diagram"
            className="w-full block scale-[1.04] origin-center"
          />
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
        <div className="flex flex-col gap-6">
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
              <ul className="space-y-3 text-sm text-white/70">
                <li>
                  <a href="mailto:pauloabcalcada@gmail.com" className="flex items-center gap-2 hover:text-white transition-colors">
                    <Mail className="size-4 shrink-0" />
                    pauloabcalcada@gmail.com
                  </a>
                </li>
                <li>
                  <a href="https://github.com/pauloabcalcada" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:text-white transition-colors">
                    <svg className="size-4 shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.335-1.755-1.335-1.755-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 21.795 24 17.295 24 12c0-6.63-5.37-12-12-12z"/>
                    </svg>
                    github.com/pauloabcalcada
                  </a>
                </li>
                <li>
                  <a href="https://linkedin.com/in/paulo-calcada" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:text-white transition-colors">
                    <svg className="size-4 shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                    </svg>
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
