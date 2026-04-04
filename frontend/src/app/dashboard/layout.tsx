"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  LayoutDashboard,
  Calendar,
  Settings,
  Bot,
  Menu,
  X,
  LogOut,
  Activity,
  Puzzle,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthContext } from "@/app/providers/auth-provider";
import { ToastContainer } from "@/components/ui/Toast";

const NAV = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard, badge: null },
  { name: "Calendar", href: "/dashboard/calendar", icon: Calendar, badge: null },
  { name: "AI Copilot", href: "/dashboard/ai", icon: Bot, badge: "new" },
  { name: "Analytics", href: "/dashboard/analytics", icon: Activity, badge: null },
  { name: "Plugins", href: "/dashboard/plugins", icon: Puzzle, badge: null },
  { name: "Settings", href: "/dashboard/settings", icon: Settings, badge: null },
];

// ─── Sidebar nav item ─────────────────────────────────────
function NavItem({
  link,
  active,
  onClick,
}: {
  link: (typeof NAV)[0];
  active: boolean;
  onClick?: () => void;
}) {
  return (
    <Link
      href={link.href}
      onClick={onClick}
      className={`group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all ${
        active
          ? "bg-indigo-600/15 text-indigo-300"
          : "text-slate-500 hover:bg-slate-800/50 hover:text-slate-200"
      }`}
    >
      {active && (
        <motion.div
          layoutId="nav-active"
          className="absolute left-0 h-5 w-0.5 rounded-full bg-indigo-400"
        />
      )}
      <link.icon className={`h-4 w-4 shrink-0 ${active ? "text-indigo-400" : "group-hover:text-slate-300"}`} />
      <span className="flex-1">{link.name}</span>
      {link.badge && (
        <span className="rounded-full bg-indigo-500/20 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-indigo-400 border border-indigo-500/20">
          {link.badge}
        </span>
      )}
    </Link>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, logout } = useAuthContext();
  type DashboardUser = { name?: string; full_name?: string; email?: string } | null;
  const typedUser = user as DashboardUser;

  const displayName = typedUser?.full_name || typedUser?.name || typedUser?.email?.split("@")[0] || "User";
  const displayEmail = typedUser?.email || "";
  const initials = displayName.slice(0, 2).toUpperCase();

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#070711]">
      {/* ── Ambient background ── */}
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute -top-32 right-0 h-96 w-96 rounded-full bg-indigo-600/6 blur-[100px]" />
        <div className="absolute bottom-0 left-20 h-64 w-64 rounded-full bg-violet-600/4 blur-[80px]" />
      </div>

      {/* ── Desktop sidebar ── */}
      <aside className="relative z-20 hidden w-60 flex-col border-r border-slate-800/40 bg-slate-950/60 backdrop-blur-xl lg:flex">
        {/* Logo */}
        <div className="flex items-center gap-2.5 border-b border-slate-800/40 px-5 py-4">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 shadow-md shadow-indigo-500/20">
            <span className="text-xs font-black text-white">G</span>
          </div>
          <span className="text-sm font-bold tracking-tight text-white">GraftAI</span>
          <div className="ml-auto flex h-4 items-center gap-0.5">
            <div className="h-1 w-1 animate-pulse rounded-full bg-emerald-400" />
            <span className="text-[9px] font-bold text-emerald-500">LIVE</span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4">
          <p className="mb-2 px-3 text-[9px] font-bold uppercase tracking-widest text-slate-700">
            Workspace
          </p>
          {NAV.map((link) => (
            <NavItem key={link.href} link={link} active={pathname === link.href} />
          ))}
        </nav>

        {/* AI upsell */}
        <div className="mx-3 mb-3 rounded-xl border border-indigo-500/15 bg-indigo-500/6 p-3">
          <div className="mb-1.5 flex items-center gap-1.5">
            <Sparkles className="h-3 w-3 text-indigo-400" />
            <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">
              Pro tip
            </span>
          </div>
          <p className="text-[11px] leading-snug text-slate-400">
            Try the AI Copilot — just describe your meeting in plain english.
          </p>
          <Link
            href="/dashboard/ai"
            className="mt-2 flex items-center gap-1 text-[11px] font-semibold text-indigo-400 transition-colors hover:text-indigo-300"
          >
            Try it <ChevronRight className="h-3 w-3" />
          </Link>
        </div>

        {/* User */}
        <div className="border-t border-slate-800/40 p-3">
          <div className="flex items-center gap-3 rounded-xl p-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500/30 to-violet-500/30 text-xs font-bold text-slate-200 border border-slate-700">
              {initials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-semibold text-slate-200">{displayName}</p>
              <p className="truncate text-[10px] text-slate-600">{displayEmail}</p>
            </div>
            <button
              onClick={logout}
              title="Sign out"
              className="rounded-lg p-1.5 text-slate-600 transition-colors hover:bg-slate-800/60 hover:text-slate-300"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Mobile overlay ── */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden"
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 28, stiffness: 260 }}
              className="fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-slate-800/50 bg-slate-950 shadow-2xl lg:hidden"
            >
              <div className="flex items-center justify-between border-b border-slate-800/40 px-5 py-4">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600">
                    <span className="text-xs font-black text-white">G</span>
                  </div>
                  <span className="text-sm font-bold text-white">GraftAI</span>
                </div>
                <button
                  onClick={() => setMobileOpen(false)}
                  className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-800/50 hover:text-white"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4">
                {NAV.map((link) => (
                  <NavItem
                    key={link.href}
                    link={link}
                    active={pathname === link.href}
                    onClick={() => setMobileOpen(false)}
                  />
                ))}
              </nav>

              <div className="border-t border-slate-800/40 p-4">
                <button
                  onClick={logout}
                  className="flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-500 transition-colors hover:bg-slate-800/50 hover:text-white"
                >
                  <LogOut className="h-4 w-4" />
                  Sign out
                </button>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* ── Content area ── */}
      <div className="relative z-10 flex flex-1 flex-col overflow-hidden">
        {/* Mobile header */}
        <header className="flex items-center justify-between border-b border-slate-800/40 bg-slate-950/80 px-4 py-3 backdrop-blur-xl lg:hidden">
          <button
            onClick={() => setMobileOpen(true)}
            className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-800/50 hover:text-white"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-br from-indigo-500 to-violet-600">
              <span className="text-[10px] font-black text-white">G</span>
            </div>
            <span className="text-sm font-bold text-white">GraftAI</span>
          </div>
          <div className="flex h-7 w-7 items-center justify-center rounded-full border border-slate-700 bg-slate-800 text-[10px] font-bold text-slate-300">
            {initials}
          </div>
        </header>

        {/* Scrollable page content */}
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-5xl p-4 sm:p-6 lg:p-8">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
            >
              {children}
            </motion.div>
          </div>
        </main>
      </div>

      {/* Global toast notifications */}
      <ToastContainer />
    </div>
  );
}
