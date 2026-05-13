import { Outlet } from "react-router-dom";
import { AppSidebar } from "./AppSidebar";

export function AppShell() {
  return (
    <div className="flex min-h-screen">
      <AppSidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <header className="h-14 border-b border-border flex items-center px-6 shrink-0">
          <span className="text-muted-foreground text-sm">
            Customer Intelligence Platform
          </span>
        </header>
        <main className="flex-1 p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
