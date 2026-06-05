import { useState } from "react";
import { Link } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { LanguageToggle } from "./LanguageToggle";
import { ThemeToggle } from "./ThemeToggle";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function LandingNavbar() {
  const { t } = useTranslation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const closeMenu = () => setMobileMenuOpen(false);

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-gray-950/80 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center h-14 px-4 sm:px-6 gap-2 sm:gap-3">
        <Link
          to="/"
          className="text-white font-semibold text-base sm:text-lg tracking-tight shrink-0"
        >
          SYNAPTIQPAY
        </Link>

        {/* Desktop section links */}
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

        {/* Right actions */}
        <div className="ml-auto flex items-center gap-1 sm:gap-2">
          <ThemeToggle />
          <LanguageToggle />
          {/* Dashboard link — hidden on mobile to give Customers button room */}
          <Link
            to="/dashboard"
            className={cn(
              buttonVariants({ variant: "ghost", size: "sm" }),
              "hidden md:inline-flex text-gray-300 hover:text-white"
            )}
          >
            {t("landing.nav.ctaDashboard")}
          </Link>
          <Link
            to="/customers"
            className={cn(buttonVariants({ size: "sm" }))}
          >
            {t("landing.nav.ctaCustomers")}
          </Link>

          {/* Hamburger — mobile only */}
          <button
            className="md:hidden p-1.5 text-gray-400 hover:text-white transition-colors"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            aria-label="Toggle navigation menu"
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
      </nav>

      {/* Mobile dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-white/10 bg-gray-950 px-6 py-4 flex flex-col gap-3">
          <p className="text-xs uppercase tracking-widest text-gray-600 pb-1">
            Sections
          </p>
          <a
            href="#methodology"
            className="text-sm text-gray-400 hover:text-white transition-colors"
            onClick={closeMenu}
          >
            {t("landing.nav.methodology")}
          </a>
          <a
            href="#deliverables"
            className="text-sm text-gray-400 hover:text-white transition-colors"
            onClick={closeMenu}
          >
            {t("landing.nav.deliverables")}
          </a>
          <a
            href="#stack"
            className="text-sm text-gray-400 hover:text-white transition-colors"
            onClick={closeMenu}
          >
            {t("landing.nav.stack")}
          </a>
          <a
            href="#roadmap"
            className="text-sm text-gray-400 hover:text-white transition-colors"
            onClick={closeMenu}
          >
            {t("landing.nav.roadmap")}
          </a>
          <hr className="border-white/10" />
          <Link
            to="/dashboard"
            className={cn(
              buttonVariants({ variant: "ghost", size: "sm" }),
              "justify-start text-gray-300 hover:text-white"
            )}
            onClick={closeMenu}
          >
            {t("landing.nav.ctaDashboard")}
          </Link>
        </div>
      )}
    </header>
  );
}
