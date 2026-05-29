import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { LanguageToggle } from "./LanguageToggle";
import { ThemeToggle } from "./ThemeToggle";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function LandingNavbar() {
  const { t } = useTranslation();

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-gray-950/80 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center h-14 px-6 gap-6">
        <Link
          to="/"
          className="text-white font-semibold text-lg tracking-tight shrink-0"
        >
          SYNAPTIQPAY / AI-SEG
        </Link>
        <div className="hidden md:flex items-center gap-4 text-sm text-gray-400">
          <a href="#methodology" className="hover:text-white transition-colors">
            {t("landing.nav.methodology")}
          </a>
          <a href="#deliverables" className="hover:text-white transition-colors">
            {t("landing.nav.deliverables")}
          </a>
          <a href="#stack" className="hover:text-white transition-colors">
            {t("landing.nav.stack")}
          </a>
          <a href="#roadmap" className="hover:text-white transition-colors">
            {t("landing.nav.roadmap")}
          </a>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <ThemeToggle />
          <LanguageToggle />
          <Link
            to="/dashboard"
            className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "text-gray-300 hover:text-white")}
          >
            {t("landing.nav.ctaDashboard")}
          </Link>
          <Link
            to="/customers"
            className={cn(buttonVariants({ size: "sm" }))}
          >
            {t("landing.nav.ctaCustomers")}
          </Link>
        </div>
      </nav>
    </header>
  );
}
