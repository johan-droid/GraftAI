"use client";

import { useEffect, useState } from "react";
import { getAnalyticsSummary } from "@/lib/api";
import { ArrowUpRight, Loader2 } from "lucide-react";
import Link from "next/link";

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<string>("");
  const [details, setDetails] = useState<{ meetings: number; hours: number; growth: number }>({ meetings: 0, hours: 0, growth: 0 });
  const [status, setStatus] = useState("Loading analytics...");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAnalyticsSummary()
      .then((data) => {
        setSummary(data.summary);
        if (data.details) {
          setDetails({
            meetings: data.details.meetings || 0,
            hours: data.details.hours || 0,
            growth: data.details.growth || 0,
          });
        }
        setStatus("Analytics loaded successfully.");
      })
      .catch((err) => {
        console.error("Analytics load error:", err);
        setStatus("Could not load analytics right now.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-black text-white tracking-tight">Analytics</h1>
          <p className="text-xs md:text-sm text-slate-400 font-medium">AI performance & activity metrics</p>
        </div>
        <Link href="/dashboard" className="text-primary hover:text-primary-glow inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-tighter">
          Dashboard <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      <div className="rounded-[1.5rem] md:rounded-2xl border border-slate-800/60 bg-slate-950/40 backdrop-blur-xl p-5 md:p-6">
        {loading ? (
          <div className="flex items-center gap-2 text-slate-500 text-xs font-bold">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> SYNCHRONIZING ANALYTICS...
          </div>
        ) : (
          <>
            <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold mb-3">{status}</p>
            <p className="text-xs md:text-sm text-slate-300 mb-6 leading-relaxed font-medium">{summary || "No analytics data available right now."}</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="rounded-xl border border-slate-800/60 bg-slate-900/30 p-4">
                <p className="text-[9px] uppercase tracking-widest text-slate-500 font-black mb-1">Meetings</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-2xl font-black text-white">{details.meetings}</p>
                  <span className="text-emerald-400 text-[10px] font-bold">+2</span>
                </div>
              </div>
              <div className="rounded-xl border border-slate-800/60 bg-slate-900/30 p-4">
                <p className="text-[9px] uppercase tracking-widest text-slate-500 font-black mb-1">Hours Managed</p>
                <div className="flex items-baseline gap-2">
                   <p className="text-2xl font-black text-white">{details.hours}h</p>
                </div>
              </div>
              <div className="rounded-xl border border-slate-800/60 bg-slate-900/30 p-4">
                <p className="text-[9px] uppercase tracking-widest text-slate-500 font-black mb-1">Growth Index</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-2xl font-black text-white">{details.growth}%</p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

    </div>
  );
}
