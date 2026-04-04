"use client";

import { useState } from "react";
import { ArrowUpRight, Loader2, Globe2, Monitor, Sparkles, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useAuthContext } from "@/app/providers/auth-provider";

interface ClientInfo {
  userAgent: string;
  browser: string;
  platform: string;
  timezone: string;
  locale: string;
  viewport: string;
  online: boolean;
  cookiesEnabled: boolean;
  localStorageEnabled: boolean;
}

export default function ClientSystemPage() {
  const { user } = useAuthContext();
  const [clientInfo] = useState<ClientInfo>(() => {
    if (typeof window === "undefined") {
      return {
        userAgent: "Unknown",
        browser: "Unknown",
        platform: "Unknown",
        timezone: "UTC",
        locale: "en-US",
        viewport: "0×0",
        online: true,
        cookiesEnabled: false,
        localStorageEnabled: false,
      };
    }

    const ua = navigator.userAgent;
    const browser = /chrome|crios|crmo/i.test(ua)
      ? "Chrome"
      : /firefox|fxios/i.test(ua)
      ? "Firefox"
      : /safari/i.test(ua) && !/chrome|crios|crmo/i.test(ua)
      ? "Safari"
      : /edg/i.test(ua)
      ? "Edge"
      : "Browser";

    let localStorageEnabled = false;
    try {
      localStorage.setItem("__graftai_test", "1");
      localStorage.removeItem("__graftai_test");
      localStorageEnabled = true;
    } catch {
      localStorageEnabled = false;
    }

    return {
      userAgent: navigator.userAgent,
      browser,
      platform: navigator.platform || "Unknown",
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
      locale: Intl.DateTimeFormat().resolvedOptions().locale || navigator.language || "en-US",
      viewport: `${window.innerWidth}×${window.innerHeight}`,
      online: navigator.onLine,
      cookiesEnabled: navigator.cookieEnabled,
      localStorageEnabled,
    };
  });

  const loading = false;
  const status = "Client environment ready.";

  const quickStats = [
    {
      label: "Current Browser",
      value: clientInfo.browser,
      icon: Globe2,
    },
    {
      label: "Time Zone",
      value: clientInfo.timezone,
      icon: Monitor,
    },
    {
      label: "Locale",
      value: clientInfo.locale,
      icon: ShieldCheck,
    },
  ];

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-black text-white tracking-tight">Client Tools</h1>
          <p className="text-xs md:text-sm text-slate-400 font-medium">Browser and session diagnostics for your workspace.</p>
        </div>
        <Link href="/dashboard" className="text-primary hover:text-primary-glow inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-tighter">
          Dashboard <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      <div className="rounded-[1.5rem] md:rounded-2xl border border-slate-800/60 bg-slate-950/40 backdrop-blur-xl p-5 md:p-6">
        {loading ? (
          <div className="flex items-center gap-2 text-slate-500 text-xs font-bold">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> GATHERING CLIENT DATA...
          </div>
        ) : (
          <>
            <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold mb-3">{status}</p>
            <div className="grid gap-4 lg:grid-cols-[1.6fr_0.9fr]">
              <div className="space-y-4">
                <div className="rounded-3xl border border-slate-800/60 bg-slate-900/40 p-6">
                  <div className="flex items-center justify-between gap-3 mb-4">
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">Client Overview</p>
                      <h2 className="text-xl font-black text-white mt-2">Environment health</h2>
                    </div>
                    <Sparkles className="w-6 h-6 text-primary" />
                  </div>
                  <div className="space-y-3 text-sm text-slate-300">
                    <div className="flex justify-between gap-4">
                      <span className="text-slate-400">Connectivity</span>
                      <span className={clientInfo.online ? "text-emerald-400 font-bold" : "text-amber-400 font-bold"}>
                        {clientInfo.online ? "Online" : "Offline"}
                      </span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-slate-400">Cookies</span>
                      <span className="font-bold text-slate-100">{clientInfo.cookiesEnabled ? "Enabled" : "Disabled"}</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-slate-400">Local storage</span>
                      <span className="font-bold text-slate-100">{clientInfo.localStorageEnabled ? "Available" : "Unavailable"}</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-slate-400">Viewport</span>
                      <span className="font-bold text-slate-100">{clientInfo.viewport}</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-slate-400">User agent</span>
                      <span className="font-mono text-[11px] text-slate-300 truncate">{clientInfo.userAgent}</span>
                    </div>
                  </div>
                </div>

                <div className="rounded-3xl border border-slate-800/60 bg-slate-900/40 p-6">
                  <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">Session status</p>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl bg-slate-950/60 p-4 border border-slate-800/70">
                      <p className="text-[9px] uppercase tracking-[0.18em] text-slate-500 font-black mb-2">Signed in as</p>
                      <p className="text-sm font-semibold text-white truncate">{user?.email || "Unknown user"}</p>
                    </div>
                    <div className="rounded-2xl bg-slate-950/60 p-4 border border-slate-800/70">
                      <p className="text-[9px] uppercase tracking-[0.18em] text-slate-500 font-black mb-2">Subscription</p>
                      <p className="text-sm font-semibold text-white capitalize">{user?.tier || "free"} / {user?.subscription_status || "inactive"}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                {quickStats.map((stat) => {
                  const Icon = stat.icon;
                  return (
                    <div key={stat.label} className="rounded-3xl border border-slate-800/60 bg-slate-900/40 p-5 flex items-start gap-4">
                      <div className="rounded-2xl bg-slate-800 p-3 text-primary">
                        <Icon className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">{stat.label}</p>
                        <p className="mt-1 text-lg font-black text-white">{stat.value}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Link href="/dashboard/calendar" className="rounded-3xl border border-slate-800/60 bg-slate-950/60 p-5 text-sm font-bold uppercase tracking-[0.2em] text-white transition hover:border-primary hover:text-primary">
          View calendar health
        </Link>
        <Link href="/dashboard/settings/billing" className="rounded-3xl border border-slate-800/60 bg-slate-950/60 p-5 text-sm font-bold uppercase tracking-[0.2em] text-white transition hover:border-primary hover:text-primary">
          Review quota & billing
        </Link>
        <Link href="/dashboard/settings" className="rounded-3xl border border-slate-800/60 bg-slate-950/60 p-5 text-sm font-bold uppercase tracking-[0.2em] text-white transition hover:border-primary hover:text-primary">
          Open settings
        </Link>
      </div>
    </div>
  );
}
