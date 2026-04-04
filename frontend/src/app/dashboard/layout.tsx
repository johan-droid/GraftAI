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
];

const SETTINGS_NAV = [
  { name: "Settings", href: "/dashboard/settings", icon: Settings, badge: null },
];

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
      className={`group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium transition-all duration-300 ${
        active
          ? "bg-indigo-500/10 text-indigo-300 shadow-sm shadow-indigo-500/5 ring-1 ring-indigo-500/20"
          : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-200"
      }`}
    >
      <div className={`flex items-center justify-center ${active ? "text-indigo-400" : "text-slate-500 group-hover:text-slate-300 transition-colors"}`}>
        <link.icon className="h-4 w-4 shrink-0" strokeWidth={active ? 2.5 : 2} />
      </div>
      <span className="flex-1">{link.name}</span>
      {link.badge && (
        <span className="rounded-full bg-indigo-500/20 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-indigo-400 border border-indigo-500/10">
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
    <div className="flex h-[100dvh] w-full overflow-hidden bg-[#070711] text-slate-200 font-sans selection:bg-indigo-500/30">
      {/* ── Immersive background ── */}
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute top-0 right-1/4 h-[800px] w-[800px] rounded-full bg-indigo-600/5 blur-[120px]" />
        <div className="absolute -bottom-32 -left-32 h-[600px] w-[600px] rounded-full bg-violet-600/4 blur-[100px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[800px] w-[800px] rounded-full bg-blue-600/3 blur-[120px]" />
        <div 
          className="absolute inset-0 opacity-[0.02]" 
          style={{ 
            backgroundImage: "linear-gradient(rgba(148,163,184,1) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,1) 1px, transparent 1px)", 
            backgroundSize: "60px 60px" 
          }} 
        />
      </div>

      {/* ── Desktop sidebar ── */}
      <aside className="relative z-20 flex w-[260px] flex-col bg-slate-900/40 backdrop-blur-2xl border-r border-white/[0.05] shadow-2xl shrink-0 max-lg:hidden">
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 h-16 shrink-0 mt-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/20">
            <span className="text-sm font-black text-white leading-none">G</span>
          </div>
          <span className="text-[15px] font-bold tracking-tight text-white drop-shadow-sm" style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}>GraftAI</span>
        </div>

        {/* Scrollable Nav */}
        <nav className="flex-1 space-y-1.5 overflow-y-auto px-4 py-6 scrollbar-hide">
          <p className="mb-3 px-2 text-[10px] font-bold uppercase tracking-widest text-slate-500/70">
            Platform
          </p>
          {NAV.map((link) => (
            <NavItem key={link.href} link={link} active={pathname === link.href} />
          ))}

          <div className="my-6 border-t border-white/[0.05]" />

          {SETTINGS_NAV.map((link) => (
            <NavItem key={link.href} link={link} active={pathname === link.href} />
          ))}
        </nav>

        {/* User Card */}
        <div className="p-4 shrink-0">
          <div className="flex items-center gap-3 rounded-2xl p-2.5 hover:bg-white/[0.04] transition-colors border border-transparent hover:border-white/[0.05] cursor-pointer group">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500/20 to-violet-500/20 text-[13px] font-bold text-indigo-300 ring-1 ring-indigo-500/30 group-hover:ring-indigo-500/50 transition-all">
              {initials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-semibold text-slate-200 group-hover:text-white transition-colors">{displayName}</p>
              <p className="truncate text-[11px] text-slate-500 group-hover:text-slate-400 transition-colors">{displayEmail}</p>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); logout(); }}
              title="Sign out"
              className="rounded-lg p-2 text-slate-500 opacity-0 group-hover:opacity-100 transition-all hover:bg-white/10 hover:text-rose-400 focus:opacity-100"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Mobile functionality ── */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden pointer-events-auto"
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed inset-y-0 left-0 z-50 flex w-[280px] flex-col border-r border-white/[0.08] bg-[#070711]/95 backdrop-blur-2xl shadow-2xl lg:hidden pointer-events-auto"
            >
              <div className="flex items-center justify-between px-6 h-16 shrink-0 border-b border-white/[0.05]">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/20">
                    <span className="text-sm font-black text-white">G</span>
                  </div>
                  <span className="text-[15px] font-bold text-white drop-shadow-sm" style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}>GraftAI</span>
                </div>
                <button
                  onClick={() => setMobileOpen(false)}
                  className="rounded-xl p-2 text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <nav className="flex-1 space-y-1.5 overflow-y-auto px-4 py-6">
                {[...NAV, ...SETTINGS_NAV].map((link) => (
                  <NavItem
                    key={link.href}
                    link={link}
                    active={pathname === link.href}
                    onClick={() => setMobileOpen(false)}
                  />
                ))}
              </nav>

              <div className="p-4 border-t border-white/[0.05]">
                <div className="flex items-center justify-between rounded-2xl p-3 bg-white/[0.03] border border-white/[0.05]">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500/20 to-violet-500/20 text-[13px] font-bold text-indigo-300 ring-1 ring-indigo-500/30">
                      {initials}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[13px] font-semibold text-slate-200">{displayName}</p>
                      <p className="truncate text-[11px] text-slate-500">{displayEmail}</p>
                    </div>
                  </div>
                  <button
                    onClick={logout}
                    className="rounded-xl p-2 text-slate-400 hover:bg-rose-500/20 hover:text-rose-400 transition-colors shrink-0"
                  >
                    <LogOut className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* ── Main content area ── */}
      <div className="relative z-10 flex flex-1 flex-col overflow-hidden">
        {/* Mobile top bar */}
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-white/[0.05] bg-[#070711]/60 px-4 backdrop-blur-xl lg:hidden pointer-events-auto">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="rounded-xl p-2 text-slate-300 hover:bg-white/10 transition-colors"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 shadow-sm shadow-indigo-500/20">
                <span className="text-[12px] font-black text-white">G</span>
              </div>
            </div>
          </div>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-indigo-500/30 bg-indigo-500/10 text-[11px] font-bold text-indigo-300">
            {initials}
          </div>
        </header>

        {/* Scrollable Workspace container */}
        <main className="flex-1 overflow-y-auto relative scrollbar-hide">
          <div className="h-full mx-auto w-full max-w-6xl">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 15, scale: 0.99 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
              className="h-full min-h-full"
            >
              {children}
            </motion.div>
          </div>
        </main>
      </div>

      <ToastContainer />
    </div>
  );
}
