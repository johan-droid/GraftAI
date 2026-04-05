"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
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
  Bell,
  Search,
  Plus,
  Zap,
  Command,
} from "lucide-react";
import NotificationCenter from "@/components/NotificationCenter";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthContext } from "@/app/providers/auth-provider";
import { syncUserTimezone, updateUserProfile } from "@/lib/api";

const NAV_GROUPS = [
  {
    label: "Workspace",
    links: [
      { name: "Home", href: "/dashboard", icon: LayoutDashboard },
      { name: "Calendar", href: "/dashboard/calendar", icon: Calendar },
      { name: "Analytics", href: "/dashboard/analytics", icon: Activity },
    ],
  },
  {
    label: "Intelligence",
    links: [
      { name: "Scheduler Assistant", href: "/dashboard/ai", icon: Bot, badge: "New" },
      { name: "Plugins", href: "/dashboard/plugins", icon: Puzzle },
    ],
  },
  {
    label: "Account",
    links: [
      { name: "Settings", href: "/dashboard/settings", icon: Settings },
    ],
  },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { logout, user } = useAuthContext();
  const displayUser = user as { name?: string; email?: string; timezone?: string } | null;

  // Active Timezone Detection & Sync
  useEffect(() => {
    if (displayUser && typeof window !== "undefined") {
      const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const storedTimezone = displayUser.timezone;

      if (browserTimezone && browserTimezone !== storedTimezone) {
        // Silent background sync
        Promise.all([
          syncUserTimezone(browserTimezone),
          updateUserProfile({ timezone: browserTimezone })
        ]).catch(err => console.error("[Timezone] Sync failed", err));
      }
    }
  }, [displayUser]);

  const userInitials = displayUser?.name
    ? displayUser.name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : displayUser?.email?.[0]?.toUpperCase() ?? "U";

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="px-5 py-5 flex items-center gap-3 border-b border-white/5">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 shrink-0">
          <Zap className="w-4 h-4 text-white fill-white" />
        </div>
        <span className="font-semibold text-white tracking-tight text-[15px]">GraftAI</span>
        <div className="ml-auto">
          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/20 tracking-wide">
            PRO
          </span>
        </div>
      </div>

      {/* Search */}
      <div className="px-4 pt-4 pb-2">
        <button className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg bg-white/5 border border-white/8 text-slate-400 text-sm hover:bg-white/8 transition-colors group">
          <Search className="w-3.5 h-3.5" />
          <span className="flex-1 text-left text-[13px]">Search…</span>
          <div className="flex items-center gap-0.5 opacity-60">
            <kbd className="text-[10px] bg-white/10 px-1.5 py-0.5 rounded">⌘</kbd>
            <kbd className="text-[10px] bg-white/10 px-1.5 py-0.5 rounded">K</kbd>
          </div>
        </button>
      </div>

      {/* Quick Create */}
      <div className="px-4 pb-3">
        <Link
          href="/dashboard/calendar"
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-[13px] font-semibold transition-all shadow-lg shadow-indigo-600/20"
        >
          <Plus className="w-3.5 h-3.5" />
          New Event
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2 space-y-5 overflow-y-auto">
        {NAV_GROUPS.map((group) => (
          <div key={group.label}>
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.12em] px-2 mb-1.5">{group.label}</p>
            <div className="space-y-0.5">
              {group.links.map((link) => {
                const isActive = pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setMobileOpen(false)}
                    className={`relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13.5px] font-medium transition-all ${
                      isActive
                        ? "bg-indigo-600/15 text-indigo-300"
                        : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                    }`}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="nav-indicator"
                        className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-indigo-400 rounded-full"
                      />
                    )}
                    <link.icon className={`w-4 h-4 shrink-0 ${isActive ? "text-indigo-400" : ""}`} />
                    <span>{link.name}</span>
                    {"badge" in link && link.badge && (
                      <span className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/20">
                        {link.badge}
                      </span>
                    )}
                    {isActive && <ChevronRight className="w-3.5 h-3.5 ml-auto text-indigo-400/60" />}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* User Profile */}
      <div className="border-t border-white/5 p-3">
        <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 transition-colors cursor-pointer group">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
            {userInitials}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[13px] font-semibold text-white truncate">{displayUser?.name ?? displayUser?.email?.split("@")[0] ?? "User"}</p>
            <p className="text-[11px] text-slate-500 truncate">{displayUser?.email ?? ""}</p>
          </div>
          <button
            onClick={logout}
            className="p-1.5 rounded-md text-slate-500 hover:text-red-400 hover:bg-red-400/10 transition-all opacity-0 group-hover:opacity-100"
            title="Sign out"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen bg-[#030712] overflow-hidden">
      {/* Ambient background */}
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute top-0 left-64 w-[600px] h-[400px] bg-indigo-600/5 rounded-full blur-[100px]" />
        <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-violet-600/5 rounded-full blur-[100px]" />
      </div>

      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex w-[220px] xl:w-[240px] flex-col shrink-0 border-r border-white/[0.06] bg-[#040a18]/60 backdrop-blur-xl z-20 relative">
        <SidebarContent />
      </aside>

      {/* Mobile Overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 lg:hidden"
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              initial={{ x: "-100%" }} animate={{ x: 0 }} exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 28, stiffness: 280 }}
              className="fixed inset-y-0 left-0 w-[260px] bg-[#040a18] border-r border-white/[0.06] z-50 lg:hidden"
            >
              <SidebarContent />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 z-10">
        {/* Topbar */}
        <header className="flex items-center gap-4 px-5 py-3 border-b border-white/[0.06] bg-[#040a18]/40 backdrop-blur-md sticky top-0 z-30">
          <button
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation menu"
            className="lg:hidden p-1.5 rounded-lg bg-white/5 text-slate-400"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Breadcrumb */}
          <div className="hidden md:flex items-center gap-1.5 text-sm text-slate-500">
            <span>GraftAI</span>
            <ChevronRight className="w-3.5 h-3.5" />
            <span className="text-slate-300 font-medium capitalize">
              {pathname.split("/").filter(Boolean).pop()?.replace("-", " ") ?? "Dashboard"}
            </span>
          </div>

          <div className="ml-auto flex items-center gap-2">
            <NotificationCenter />
            <button className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/8 text-slate-400 hover:text-white hover:bg-white/8 transition-all text-[12px] font-medium">
              <Command className="w-3.5 h-3.5" />
              <span>Command</span>
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          <motion.div
            key={pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="h-full"
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
}
