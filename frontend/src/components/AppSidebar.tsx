import { NavLink } from "react-router-dom";

const NAV = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/customers", label: "Customers" },
];

export function AppSidebar() {
  return (
    <aside className="flex flex-col w-56 min-h-screen bg-sidebar border-r border-sidebar-border px-4 py-6 gap-2 shrink-0">
      <div className="mb-6 px-2">
        <span className="text-primary font-semibold text-lg tracking-tight">
          SynaptiqPay
        </span>
      </div>
      <nav className="flex flex-col gap-1">
        {NAV.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              [
                "rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-accent text-sidebar-foreground"
                  : "text-sidebar-foreground/60 hover:text-sidebar-foreground hover:bg-sidebar-accent/50",
              ].join(" ")
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
