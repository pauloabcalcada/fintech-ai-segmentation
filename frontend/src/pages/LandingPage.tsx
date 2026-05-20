import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { ArrowRight, ExternalLink } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const TECH_STACK = [
  "Faker", "Pandas", "Scikit-learn", "LangGraph",
  "FastAPI", "React", "Supabase", "Vercel", "Fly.io",
];

export function LandingPage() {
  const { t } = useTranslation();

  return (
    <main className="min-h-screen bg-background">
      {/* Hero */}
      <section className="flex flex-col items-center justify-center px-6 pt-24 pb-16 text-center">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
          SynaptiqPay · AI Segmentation
        </div>
        <h1 className="max-w-2xl text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
          {t("landing.hero.heading")}
        </h1>
        <p className="mt-4 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg">
          {t("landing.hero.tagline")}
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Link
            to="/dashboard"
            className={cn(buttonVariants({ size: "lg" }), "cursor-pointer gap-2 px-6 text-base")}
          >
            {t("landing.hero.cta")}
            <ArrowRight className="size-4" />
          </Link>
          <a
            href="https://github.com/pauloabcalcada/fintech-ai-segmentation"
            target="_blank"
            rel="noopener noreferrer"
            className={cn(buttonVariants({ variant: "outline", size: "lg" }), "cursor-pointer gap-2 px-6 text-base")}
          >
            <ExternalLink className="size-4" />
            {t("landing.github.label")}
          </a>
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
  );
}
