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
import { AnimatePresence, motion } from "framer-motion";
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

const BOTTOM_NAV_LINKS = [
  { name: "Home", href: "/dashboard", icon: LayoutDashboard },
  { name: "Calendar", href: "/dashboard/calendar", icon: Calendar },
  { name: "AI", href: "/dashboard/ai", icon: Bot },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
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

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (typeof document === "undefined") {
      return;
    }
    document.body.style.overflow = mobileMenuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileMenuOpen]);

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
    <div className="relative flex h-[100dvh] overflow-hidden bg-[#030712] pt-[env(safe-area-inset-top)] pl-[env(safe-area-inset-left)] pr-[env(safe-area-inset-right)]">
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute top-0 left-64 w-[600px] h-[400px] bg-indigo-600/5 rounded-full blur-[100px]" />
        <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-violet-600/5 rounded-full blur-[100px]" />
      </div>

      <aside className="hidden lg:flex w-[220px] xl:w-[240px] flex-col shrink-0 border-r border-white/[0.06] bg-[#040a18]/60 backdrop-blur-xl z-20 relative">
        <SidebarContent />
      </aside>

      {/* Mobile Drawer Navigation Removed for Native Bottom Nav */}

      <div className="z-10 flex min-w-0 flex-1 flex-col pb-[calc(86px+env(safe-area-inset-bottom))] lg:pb-0">
        <header className="flex items-center gap-3 sm:gap-4 px-4 sm:px-5 py-3 sm:py-4 border-b border-white/[0.06] bg-[#040a18]/80 backdrop-blur-xl sticky top-0 z-30">
          <div className="flex items-center gap-1.5 text-sm text-slate-500">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex lg:hidden items-center justify-center shadow-lg shadow-indigo-500/20 shrink-0 mr-1.5">
              <Zap className="w-4 h-4 text-white fill-white" />
            </div>
            <span className="font-semibold text-white tracking-tight lg:hidden">GraftAI</span>
            
            <span className="hidden lg:inline">GraftAI</span>
            <ChevronRight className="hidden lg:block w-3.5 h-3.5" />
            <span className="hidden lg:block text-slate-300 font-medium capitalize">
              {pathname.split("/").filter(Boolean).pop()?.replace("-", " ") ?? "Dashboard"}
            </span>
          </div>

          <div className="ml-auto flex items-center gap-1.5 sm:gap-2">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="inline-flex lg:hidden items-center justify-center h-11 w-11 rounded-xl border border-white/10 bg-white/5 text-slate-200"
              aria-label="Open navigation menu"
            >
              <Menu className="w-5 h-5" />
            </button>
            <PrivacyToggle />
            <NotificationCenter />
            <button className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/8 text-slate-400 hover:text-white hover:bg-white/8 transition-all text-[12px] font-medium">
              <Command className="w-3.5 h-3.5" />
              <span>Command</span>
            </button>
          </div>
        </header>

        <main className="touch-pan-y flex-1 overflow-y-auto overscroll-y-contain">
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

        <div className="mobile-safe-bottom fixed inset-x-0 bottom-0 z-50 px-3 pb-2 lg:hidden">
          <nav className="mx-auto flex h-[68px] max-w-md items-center rounded-[24px] border border-white/[0.14] bg-[#040a18]/85 px-1.5 backdrop-blur-2xl shadow-2xl shadow-black/45">
            {BOTTOM_NAV_LINKS.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  aria-current={isActive ? "page" : undefined}
                  className={cn(
                    "relative flex h-full flex-1 flex-col items-center justify-center gap-0.5 rounded-2xl text-[10px] font-semibold tracking-wide",
                    isActive ? "text-indigo-300" : "text-slate-400"
                  )}
                >
                  {isActive && (
                    <motion.span
                      layoutId="dashboard-mobile-tab"
                      className="absolute inset-1 -z-10 rounded-2xl border border-indigo-400/25 bg-indigo-500/18"
                    />
                  )}
                  <link.icon className={cn("h-[20px] w-[20px]", isActive && "drop-shadow-[0_0_10px_rgba(99,102,241,0.4)]")} />
                  <span>{link.name}</span>
                </Link>
              );
            })}

            <button
              onClick={() => setMobileMenuOpen(true)}
              className={cn(
                "relative flex h-full flex-1 flex-col items-center justify-center gap-0.5 rounded-2xl text-[10px] font-semibold tracking-wide",
                mobileMenuOpen ? "text-indigo-300" : "text-slate-400"
              )}
              aria-expanded={mobileMenuOpen ? "true" : "false"}
              aria-label="Open more navigation options"
            >
              {mobileMenuOpen && <span className="absolute inset-1 -z-10 rounded-2xl border border-indigo-400/25 bg-indigo-500/18" />}
              <Menu className="h-[20px] w-[20px]" />
              <span>More</span>
            </button>
          </nav>
        </div>

        <AnimatePresence>
          {mobileMenuOpen && (
            <>
              <motion.button
                aria-label="Close mobile navigation"
                onClick={() => setMobileMenuOpen(false)}
                className="fixed inset-0 z-[60] bg-black/55 lg:hidden"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              />

              <motion.aside
                className="touch-pan-y fixed inset-y-0 right-0 z-[61] w-[min(90vw,380px)] overflow-y-auto border-l border-white/10 bg-[#050b1e]/95 px-4 pb-[calc(100px+env(safe-area-inset-bottom))] pt-[calc(16px+env(safe-area-inset-top))] backdrop-blur-2xl lg:hidden"
                initial={{ x: "100%", opacity: 0.9 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: "100%", opacity: 0.95 }}
                transition={{ duration: 0.24, ease: [0.32, 0.72, 0, 1] }}
              >
                <div className="mb-5 flex items-center justify-between">
                  <div>
                    <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Navigation</p>
                    <h2 className="mt-1 text-base font-semibold text-white">Workspace Menu</h2>
                  </div>
                  <button
                    onClick={() => setMobileMenuOpen(false)}
                    className="inline-flex h-11 w-11 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-slate-200"
                    aria-label="Close navigation menu"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>

                <Link
                  href="/dashboard/calendar"
                  className="mb-5 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-indigo-600 px-4 py-3.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/25"
                >
                  <Plus className="h-4 w-4" />
                  New Event
                </Link>

                <div className="space-y-6">
                  {NAV_GROUPS.map((group) => (
                    <section key={group.label}>
                      <p className="mb-2 px-1 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">{group.label}</p>
                      <div className="space-y-1">
                        {group.links.map((link) => {
                          const isActive = pathname === link.href;
                          return (
                            <Link
                              key={link.href}
                              href={link.href}
                              className={cn(
                                "flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium",
                                isActive ? "bg-indigo-500/15 text-indigo-300" : "text-slate-300 bg-white/[0.02]"
                              )}
                            >
                              <link.icon className="h-4 w-4" />
                              <span>{link.name}</span>
                              {"badge" in link && link.badge && (
                                <span className="ml-auto rounded-full border border-indigo-500/25 bg-indigo-500/20 px-2 py-0.5 text-[10px] font-bold text-indigo-200">
                                  {link.badge}
                                </span>
                              )}
                            </Link>
                          );
                        })}
                      </div>
                    </section>
                  ))}
                </div>

                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    setLogoutModalOpen(true);
                  }}
                  className="mt-7 inline-flex w-full items-center justify-center gap-2 rounded-2xl border border-rose-400/25 bg-rose-500/10 px-4 py-3.5 text-sm font-semibold text-rose-300"
                >
                  <LogOut className="h-4 w-4" />
                  Sign out
                </button>
              </motion.aside>
            </>
          )}
        </AnimatePresence>
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
