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
  Search,
  Plus,
  Zap,
  Command,
  Eye,
  EyeOff,
} from "lucide-react";
import NotificationCenter from "@/components/NotificationCenter";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthContext } from "@/app/providers/auth-provider";
import { syncUserTimezone, updateUserProfile, submitLogoutFeedback } from "@/lib/api";
import { DashboardProvider, useDashboard } from "@/providers/dashboard-provider";

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

type ClassValue = string | boolean | null | undefined;
const cn = (...classes: ClassValue[]) => classes.filter(Boolean).join(" ");

function PrivacyToggle() {
  const { isPrivacyMode, togglePrivacyMode } = useDashboard();
  return (
    <button
      onClick={togglePrivacyMode}
      className={cn(
        "flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all text-[12px] font-medium",
        isPrivacyMode 
          ? "bg-indigo-500/20 border-indigo-500/30 text-indigo-300" 
          : "bg-white/5 border-white/8 text-slate-400 hover:text-white"
      )}
      title={isPrivacyMode ? "Disable Privacy Mode" : "Enable Privacy Mode"}
    >
      {isPrivacyMode ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
      <span className="hidden sm:inline">{isPrivacyMode ? "Private" : "Privacy"}</span>
    </button>
  );
}

function DashboardContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [logoutModalOpen, setLogoutModalOpen] = useState(false);
  const [logoutReason, setLogoutReason] = useState("");
  const [logoutDetails, setLogoutDetails] = useState("");
  const [logoutSubmitting, setLogoutSubmitting] = useState(false);
  const { logout, user, loading } = useAuthContext();
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

  if (loading) {
    return (
      <div className="min-h-screen bg-[#030612] flex items-center justify-center">
        <div className="relative">
          <div className="w-12 h-12 rounded-full border-2 border-indigo-500/20 border-t-indigo-500 animate-spin" />
          <div className="absolute inset-0 bg-indigo-500/10 blur-xl rounded-full animate-pulse" />
        </div>
      </div>
    );
  }

  // Double guard: If no user and not loading (redirection handled by AuthProvider)
  if (!user) return null;

  const userInitials = displayUser?.name
    ? displayUser.name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : displayUser?.email?.[0]?.toUpperCase() ?? "U";

  const handleLogoutFeedbackSubmit = async () => {
    if (!logoutReason) {
      return;
    }
    setLogoutSubmitting(true);
    try {
      await submitLogoutFeedback({ reason: logoutReason, details: logoutDetails });
    } catch (err) {
      console.error("Logout feedback submission failed", err);
    } finally {
      setLogoutSubmitting(false);
      setLogoutModalOpen(false);
      await logout();
    }
  };

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
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

      <div className="px-4 pb-3">
        <Link
          href="/dashboard/calendar"
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-[13px] font-semibold transition-all shadow-lg shadow-indigo-600/20"
        >
          <Plus className="w-3.5 h-3.5" />
          New Event
        </Link>
      </div>

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
            onClick={() => setLogoutModalOpen(true)}
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
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute top-0 left-64 w-[600px] h-[400px] bg-indigo-600/5 rounded-full blur-[100px]" />
        <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-violet-600/5 rounded-full blur-[100px]" />
      </div>

      <aside className="hidden lg:flex w-[220px] xl:w-[240px] flex-col shrink-0 border-r border-white/[0.06] bg-[#040a18]/60 backdrop-blur-xl z-20 relative">
        <SidebarContent />
      </aside>

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

      <div className="flex-1 flex flex-col min-w-0 z-10">
        <header className="flex items-center gap-3 sm:gap-4 px-3 sm:px-5 py-2.5 sm:py-3 border-b border-white/[0.06] bg-[#040a18]/40 backdrop-blur-md sticky top-0 z-30">
          <button
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation menu"
            className="lg:hidden min-h-11 min-w-11 p-2 rounded-lg bg-white/5 text-slate-400"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="hidden md:flex items-center gap-1.5 text-sm text-slate-500">
            <span>GraftAI</span>
            <ChevronRight className="w-3.5 h-3.5" />
            <span className="text-slate-300 font-medium capitalize">
              {pathname.split("/").filter(Boolean).pop()?.replace("-", " ") ?? "Dashboard"}
            </span>
          </div>

          <div className="ml-auto flex items-center gap-1.5 sm:gap-2">
            <PrivacyToggle />
            <NotificationCenter />
            <button className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/8 text-slate-400 hover:text-white hover:bg-white/8 transition-all text-[12px] font-medium">
              <Command className="w-3.5 h-3.5" />
              <span>Command</span>
            </button>
          </div>
        </header>

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

        {logoutModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
            <div className="w-full max-w-xl rounded-3xl border border-white/10 bg-[#01050e] p-6 shadow-2xl shadow-black/40">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-xl font-bold text-white">Before you log out</h2>
                  <p className="mt-2 text-sm text-slate-400">Let us know why you&apos;re signing out so we can improve the product.</p>
                </div>
                <button
                  onClick={() => setLogoutModalOpen(false)}
                  className="text-slate-400 hover:text-white"
                  aria-label="Close feedback dialog"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="mt-6 space-y-4">
                <div>
                  <label htmlFor="logout-reason" className="block text-sm font-medium text-slate-200">Reason for logging out</label>
                  <select
                    id="logout-reason"
                    value={logoutReason}
                    onChange={(event) => setLogoutReason(event.target.value)}
                    className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-900 px-4 py-3 text-sm text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="">Select a reason</option>
                    <option value="Finished for now">Finished for now</option>
                    <option value="Taking a break">Taking a break</option>
                    <option value="Privacy concerns">Privacy concerns</option>
                    <option value="Found another tool">Found another tool</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-200">More details</label>
                  <textarea
                    rows={3}
                    value={logoutDetails}
                    onChange={(event) => setLogoutDetails(event.target.value)}
                    placeholder="Optional details (what could we improve?)"
                    className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-900 px-4 py-3 text-sm text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="mt-6 flex items-center justify-end gap-3">
                <button
                  onClick={() => setLogoutModalOpen(false)}
                  className="rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-semibold text-slate-200 hover:bg-white/10 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleLogoutFeedbackSubmit}
                  disabled={!logoutReason || logoutSubmitting}
                  className="rounded-2xl bg-indigo-500 px-5 py-3 text-sm font-semibold text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-indigo-400 transition-colors"
                >
                  {logoutSubmitting ? "Sending…" : "Send feedback & log out"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <DashboardProvider>
      <DashboardContent>{children}</DashboardContent>
    </DashboardProvider>
  );
}
