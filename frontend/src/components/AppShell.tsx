import { NavLink, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { LanguageToggle } from "./LanguageToggle";

export function AppShell() {
  const { t } = useTranslation();

  const NAV = [
    { to: "/dashboard", label: t("nav.dashboard") },
    { to: "/customers", label: t("nav.customers") },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <nav className="flex items-center h-14 px-6 gap-6">
          <NavLink
            to="/"
            className="text-primary font-semibold text-lg tracking-tight shrink-0"
          >
            SynaptiqPay
          </NavLink>
          <div className="flex items-center gap-1">
            {NAV.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  [
                    "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent/50",
                  ].join(" ")
                }
              >
                {label}
              </NavLink>
            ))}
          </div>
          <div className="ml-auto flex items-center" data-testid="topnav-right-slot">
            <LanguageToggle />
          </div>
        </nav>
      </header>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}
