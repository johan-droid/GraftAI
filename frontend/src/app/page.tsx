"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Bot, ShieldCheck, Sparkles, Zap, Lock, Globe, Flash, Cloud } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

type ToastLevel = "info" | "success" | "warning" | "error";
type ToastItem = { id: string; message: string; level: ToastLevel };

type BackendStatus = "unknown" | "waking" | "live" | "sleeping";


const features = [
  { icon: <Zap className="w-6 h-6" />, title: "Instant sync", description: "Auto-update events across every calendar provider in milliseconds." },
  { icon: <Bot className="w-6 h-6" />, title: "AI strategy", description: "Predict conflicts and suggest reschedules before they happen." },
  { icon: <ShieldCheck className="w-6 h-6" />, title: "Security first", description: "Cloud-strong identity with optional FIDO2 and SSO." },
  { icon: <Globe className="w-6 h-6" />, title: "Global federated", description: "Multi-region architecture with zero single-point lock-in." },
  { icon: <Lock className="w-6 h-6" />, title: "Privacy guard", description: "Opaque data control and self-hosted workspace isolation." },
  { icon: <Sparkles className="w-6 h-6" />, title: "Workflow automation", description: "Trigger custom rules for meetings, follow-ups, and reminders." },
];

function statusTag(status: BackendStatus) {
  const map: Record<BackendStatus, { label: string; className: string }> = {
    unknown: { label: "Unknown", className: "bg-slate-500/20 text-slate-100" },
    waking: { label: "Waking...", className: "bg-amber-500/20 text-amber-200" },
    live: { label: "Backend live ✅", className: "bg-emerald-500/20 text-emerald-200" },
    sleeping: { label: "Backend sleeping 😴", className: "bg-violet-500/20 text-violet-200" },
  };
  return map[status];
}

function getToastStyle(level: ToastLevel) {
  switch (level) {
    case "success": return "bg-emerald-500/90 text-white";
    case "error": return "bg-rose-500/90 text-white";
    case "warning": return "bg-amber-500/90 text-slate-900";
    default: return "bg-slate-800/90 text-white";
  }
}

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<BackendStatus>("unknown");
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [pending, setPending] = useState(false);

  const status = statusTag(backendStatus);

  const addToast = (message: string, level: ToastLevel = "info") => {
    const id = crypto.randomUUID();
    setToasts((prev) => [{ id, message, level }, ...prev].slice(0, 3));
    window.setTimeout(() => setToasts((prev) => prev.filter((item) => item.id !== id)), 4200);
  };

  const checkBackend = useCallback(async () => {
    setPending(true);
    if (backendStatus !== "live") {
      setBackendStatus("waking");
      addToast("⏳ Backend waking up, this may take a few seconds.", "info");
    }

    await new Promise((resolve) => setTimeout(resolve, 2000));

    try {
      const resp = await fetch("/health", { cache: "no-store" });
      if (!resp.ok) throw new Error(`Status ${resp.status}`);
      const data = await resp.json();
      if (backendStatus === "sleeping" || backendStatus === "waking" || backendStatus === "unknown") {
        addToast(`✅ Backend is live: ${data.status}. You can proceed.`, "success");
      }
      setBackendStatus("live");
    } catch {
      if (backendStatus !== "sleeping") {
        addToast("💤 Backend is still sleeping. Will retry automatically.", "warning");
      }
      setBackendStatus("sleeping");
    } finally {
      setPending(false);
    }
  }, [backendStatus]);

  useEffect(() => {
    checkBackend();
    const timer = setInterval(checkBackend, 18000);
    return () => clearInterval(timer);
  }, [checkBackend]);

  const activeFeatureCards = useMemo(() => features, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-3">
        {toasts.map((toast) => (
          <motion.div key={toast.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 10 }} className={`${getToastStyle(toast.level)} rounded-xl px-4 py-2 shadow-lg border border-white/10 max-w-[280px]`}>{toast.message}</motion.div>
        ))}
      </div>

      <main className="mx-auto w-full max-w-6xl px-5 py-16 sm:px-6 md:px-8">
        <header className="text-center mb-12">
          <p className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-amber-300">
            <Cloud className="w-4 h-4" /> Backend status: {status.label}
          </p>
          <h1 className="mt-4 text-3xl font-black sm:text-5xl md:text-6xl">GraftAI · Minimal Ops Calendar Intelligence</h1>
          <p className="mt-3 text-slate-300 max-w-xl mx-auto text-base sm:text-lg">A clean, mobile-first landing experience with fast feature highlights and real backend readiness feedback from Render cold starts.</p>

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link href="/login" className="rounded-xl bg-gradient-to-r from-indigo-500 to-cyan-500 px-6 py-3 text-sm font-bold text-white transition hover:brightness-110">Start building</Link>
            <button onClick={checkBackend} className="rounded-xl border border-slate-700 bg-slate-900 px-6 py-3 text-sm font-semibold text-slate-100 hover:bg-slate-800">Re-check backend</button>
          </div>
        </header>

        <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {activeFeatureCards.map((feature) => (
            <motion.article key={feature.title} whileHover={{ y: -4, scale: 1.01 }} transition={{ type: "spring", stiffness: 160 }} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 backdrop-blur-sm shadow-lg">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800 text-cyan-300">{feature.icon}</div>
              <h3 className="mt-4 text-lg font-black text-white">{feature.title}</h3>
              <p className="mt-2 text-sm text-slate-300">{feature.description}</p>
            </motion.article>
          ))}
        </section>

        <section className="mt-12 rounded-2xl border border-slate-800 bg-slate-900/80 p-6">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <span className="inline-flex items-center gap-2 rounded-lg bg-slate-800/70 px-3 py-1 text-xs font-bold uppercase tracking-wide text-slate-200">Health</span>
            <span className="text-sm text-slate-300">Last check: {pending ? "Checking..." : backendStatus === "live" ? "Live" : backendStatus === "sleeping" ? "Sleeping" : "Unknown"}</span>
          </div>
          <p className="mt-4 text-sm leading-relaxed text-slate-300">Backend cold-start on Render: retries run automatically every 18 seconds, with a toast on transitions for live/sleep messages. If you see sleeping state for 30+, click Re-check backend.</p>
          <div className="mt-4 inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200">
            <Flash className="h-4 w-4 text-amber-300" /> Wake-up flow active
          </div>
        </section>

      </main>
    </div>
  );
}

