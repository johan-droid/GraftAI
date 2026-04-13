"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import {
  LayoutDashboard, Calendar, Settings, Bot, LogOut,
  Activity, Puzzle, Menu, X, ChevronRight, Sun, Moon,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/app/providers/auth-provider";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { Toaster } from "@/components/ui/Toast";

const NAV_LINKS = [
  { name: "Overview",   href: "/dashboard",           icon: LayoutDashboard },
  { name: "Analytics",  href: "/dashboard/analytics", icon: Activity },
  { name: "Calendar",   href: "/dashboard/calendar",  icon: Calendar },
  { name: "AI Copilot", href: "/dashboard/ai",        icon: Bot },
  { name: "Plugins",    href: "/dashboard/plugins",   icon: Puzzle },
  { name: "Settings",   href: "/dashboard/settings",  icon: Settings },
] as const;

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname  = usePathname();
  const { logout, user } = useAuth();
  const [drawerOpen, setDrawerOpen]   = useState(false);
  const [darkMode, setDarkMode]       = useState(true);
  const [collapsed, setCollapsed]     = useState(false);

  useEffect(() => { setDrawerOpen(false); }, [pathname]);

  useEffect(() => {
    document.documentElement.classList.toggle("light", !darkMode);
  }, [darkMode]);

  const isActive = (href: string) =>
    href === "/dashboard" ? pathname === href : pathname.startsWith(href);

  type DashUser = { name?: string; email?: string } | null;
  const displayUser = user as DashUser;
  const initials = displayUser?.name
    ? displayUser.name.split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase()
    : displayUser?.email?.[0]?.toUpperCase() ?? "U";

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[var(--bg)]">
      <Toaster />

      <aside
        className={`hidden lg:flex flex-col z-20 border-r transition-[width] duration-200 bg-[var(--bg-surface)] border-[var(--border)] flex-shrink-0 ${collapsed ? 'w-[64px]' : 'w-[220px]'}`}
      >
        <div className="flex items-center gap-3 px-4 py-5 border-b min-h-[64px] border-[var(--border)]">
          <div className="w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center font-bold text-sm bg-peach text-[#1A0F0A]">
            G
          </div>
          {!collapsed && (
            <span className="font-bold text-base tracking-tight text-white">GraftAI</span>
          )}
        </div>

        <nav className="flex-1 px-2 py-4 space-y-0.5 overflow-y-auto scrollbar-hide">
          {NAV_LINKS.map(({ name, href, icon: Icon }) => {
            const active = isActive(href);
            return (
              <Link
                key={href}
                href={href}
                title={collapsed ? name : undefined}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all relative group ${active ? 'bg-[var(--peach-ghost)] text-[var(--peach)] border-r-2 border-[var(--peach)]' : 'text-[var(--text-muted)]'}`}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {!collapsed && <span>{name}</span>}
                {active && !collapsed && (
                  <ChevronRight className="w-3.5 h-3.5 ml-auto opacity-50" />
                )}
                {collapsed && (
                  <span className="absolute left-full ml-2 px-2 py-1 rounded text-xs font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 bg-[var(--bg-hover)] text-[var(--text)] border border-[var(--border)]">
                    {name}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        <div className="p-2 border-t space-y-1 border-[var(--border)]">
          <button
            onClick={() => setDarkMode(v => !v)}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-[var(--text-muted)]"
            title={collapsed ? (darkMode ? "Light mode" : "Dark mode") : undefined}
          >
            {darkMode ? <Sun className="w-5 h-5 flex-shrink-0" /> : <Moon className="w-5 h-5 flex-shrink-0" />}
            {!collapsed && <span>{darkMode ? "Light mode" : "Dark mode"}</span>}
          </button>

          <button
            onClick={() => setCollapsed(v => !v)}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors text-[var(--text-faint)]"
          >
            <Menu className="w-4 h-4 flex-shrink-0" />
            {!collapsed && <span className="text-xs">Collapse</span>}
          </button>

          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-[var(--text-muted)]"
            title={collapsed ? "Sign out" : undefined}
          >
            <LogOut className="w-5 h-5 flex-shrink-0" />
            {!collapsed && <span>Sign out</span>}
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <header className="lg:hidden flex items-center justify-between px-4 border-b sticky top-0 z-30 h-[56px] bg-[var(--bg-surface)] border-[var(--border)]">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center font-bold text-sm bg-peach text-[#1A0F0A]">G</div>
            <span className="font-bold text-sm text-white">GraftAI</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setDarkMode(v => !v)}
              className="p-2 rounded-lg min-h-0 min-w-0 text-[var(--text-muted)]"
            >
              {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
            <button
              onClick={() => setDrawerOpen(true)}
              className="p-2 rounded-lg min-h-0 min-w-0 text-[var(--text-muted)]"
            >
              <Menu className="w-5 h-5" />
            </button>
          </div>
        </header>

        <AnimatePresence>
          {drawerOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="fixed inset-0 z-40 lg:hidden bg-[rgba(0,0,0,0.6)] backdrop-blur-[4px]"
                onClick={() => setDrawerOpen(false)}
              />
              <motion.aside
                initial={{ x: "100%" }}
                animate={{ x: 0 }}
                exit={{ x: "100%" }}
                transition={{ type: "spring", damping: 28, stiffness: 250 }}
                className="fixed inset-y-0 right-0 z-50 flex flex-col w-72 lg:hidden bg-[var(--bg-surface)] border-l border-[var(--border)]"
              >
                <div className="flex items-center justify-between px-4 py-4 border-b border-[var(--border)]">
                  <span className="font-semibold text-sm text-white">Menu</span>
                  <button onClick={() => setDrawerOpen(false)} className="p-1 min-h-0 min-w-0 text-[var(--text-muted)]">
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="px-4 py-3 border-b border-[var(--border)]">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold bg-peach text-[#1A0F0A]">{initials}</div>
                    <div>
                      <p className="text-sm font-medium text-white">{displayUser?.name ?? "User"}</p>
                      <p className="text-xs text-[var(--text-muted)]">{displayUser?.email ?? ""}</p>
                    </div>
                  </div>
                </div>

                <nav className="flex-1 px-3 py-4 space-y-0.5">
                  {NAV_LINKS.map(({ name, href, icon: Icon }) => {
                    const active = isActive(href);
                    return (
                      <Link key={href} href={href}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${active ? 'bg-[var(--peach-ghost)] text-[var(--peach)]' : 'text-[var(--text-muted)]'}`}
                      >
                        <Icon className="w-5 h-5" />
                        {name}
                      </Link>
                    );
                  })}
                </nav>

                <div className="p-3 border-t border-[var(--border)]">
                  <button onClick={logout}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-[var(--text-muted)]"
                  >
                    <LogOut className="w-5 h-5" /> Sign out
                  </button>
                </div>
              </motion.aside>
            </>
          )}
        </AnimatePresence>

        <main className="flex-1 overflow-y-auto">
          <div className="max-w-6xl mx-auto px-4 py-6 md:px-8 md:py-8 pb-24 lg:pb-8">
            <ErrorBoundary>
              <motion.div
                key={pathname}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25 }}
              >
                {children}
              </motion.div>
            </ErrorBoundary>
          </div>
        </main>

        <nav className="lg:hidden fixed bottom-0 inset-x-0 z-30 flex border-t bg-[var(--bg-surface)] border-[var(--border)] pb-[env(safe-area-inset-bottom)]">
          {NAV_LINKS.slice(0, 5).map(({ name, href, icon: Icon }) => {
            const active = isActive(href);
            return (
              <Link
                key={href}
                href={href}
                className={`flex-1 flex flex-col items-center justify-center gap-1 py-2 text-center min-h-0 transition-colors ${active ? 'text-[var(--peach)]' : 'text-[var(--text-faint)]'}`}
              >
                <Icon className="w-5 h-5" />
                <span className="text-[10px] font-semibold">{name.split(" ")[0]}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}