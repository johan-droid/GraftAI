"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  Calendar,
  Clock,
  Users,
  BarChart3,
  Zap,
  Loader2,
} from "lucide-react";
import { getAnalyticsRealtime, type AnalyticsRealtimeResponse } from "@/lib/api";
import TimelineLineChart from "@/components/TimelineLineChart";
import { cn } from "@/lib/utils";

const STAGGER = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const ITEM = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
};

const KPI_STYLES: Record<string, { bg: string; border: string; icon: string }> = {
  indigo: { bg: "bg-indigo-500/10", border: "border-indigo-500/20", icon: "text-indigo-400" },
  violet: { bg: "bg-violet-500/10", border: "border-violet-500/20", icon: "text-violet-400" },
  cyan: { bg: "bg-cyan-500/10", border: "border-cyan-500/20", icon: "text-cyan-400" },
  emerald: { bg: "bg-emerald-500/10", border: "border-emerald-500/20", icon: "text-emerald-400" },
};

export default function AnalyticsPage() {
  const [range, setRange] = useState<"7d" | "30d" | "90d">("30d");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AnalyticsRealtimeResponse | null>(null);

  const handleRangeChange = (nextRange: "7d" | "30d" | "90d") => {
    setError(null);
    setLoading(true);
    setRange(nextRange);
  };

  useEffect(() => {
    let alive = true;

    getAnalyticsRealtime(range)
      .then((payload) => {
        if (!alive) return;
        setData(payload);
      })
      .catch((err) => {
        if (!alive) return;
        setError(err instanceof Error ? err.message : "Failed to load analytics");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [range]);

  const series = useMemo(() => data?.series ?? [], [data]);
  const totals = data?.totals || {
    meetings: 0,
    hours: 0,
    growth: 0,
    unique_attendees: 0,
    cancellations: 0,
  };

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto">
      <motion.div variants={STAGGER} initial="hidden" animate="visible" className="space-y-8">
        <motion.div variants={ITEM} className="flex flex-col sm:flex-row sm:items-center gap-6">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">Analytics</h1>
            <p className="text-slate-500 text-[15px] mt-1.5 leading-relaxed">Advanced scheduling intelligence and workspace metrics.</p>
          </div>
          <div className="sm:ml-auto flex items-center gap-1.5 p-1.5 rounded-xl bg-white/5 border border-white/8 backdrop-blur-md">
            {(["7d", "30d", "90d"] as const).map((r) => (
              <button
                key={r}
                onClick={() => handleRangeChange(r)}
                className={`px-4 py-2 rounded-lg text-[13px] font-bold transition-all ${
                  range === r ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20" : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                }`}
              >
                {r === "7d" ? "7 Days" : r === "30d" ? "30 Days" : "90 Days"}
              </button>
            ))}
          </div>
        </motion.div>

        {error && (
          <motion.div variants={ITEM} className="rounded-xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-sm text-red-200 backdrop-blur-sm">
            {error}
          </motion.div>
        )}

        <motion.div variants={ITEM} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {[
            { label: "Scheduled Meetings", value: totals.meetings.toString(), icon: Calendar, color: "indigo", sub: "Currently active" },
            { label: "Total Focus Time", value: `${totals.hours}h`, icon: Clock, color: "violet", sub: "Across all calendars" },
            { label: "Client Contacts", value: totals.unique_attendees.toString(), icon: Users, color: "cyan", sub: "Network depth" },
            { label: "Success Rate", value: `${Math.max(0, 100 - (totals.cancellations * 5))}%`, icon: Zap, color: "emerald", sub: "Meeting integrity" },
          ].map((kpi) => {
            const styles = KPI_STYLES[kpi.color];
            return (
              <div key={kpi.label} className="relative flex flex-col justify-between aspect-auto sm:aspect-square lg:aspect-square overflow-hidden rounded-3xl border border-white/[0.08] bg-[#0d1424]/60 p-6 transition-all hover:bg-[#0d1424]/80 hover:border-white/20">
                {/* Subtle Glow */}
                <div className={`absolute -right-8 -top-8 w-28 h-28 blur-[50px] opacity-20 group-hover:opacity-40 transition-opacity bg-current ${styles.icon.replace('text-', 'bg-')}`} />
                
                <div className="flex items-start justify-between">
                  <div className={`w-12 h-12 rounded-2xl flex items-center justify-center bg-white/5 border border-white/10 group-hover:scale-110 transition-transform`}>
                    <kpi.icon className={`w-6 h-6 ${styles.icon}`} />
                  </div>
                  <span className="text-[10px] font-bold text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded-full leading-none tracking-wide">Healthy</span>
                </div>
                
                <div className="mt-6 md:mt-auto">
                  {loading ? (
                    <div className="h-10 w-24 rounded-lg bg-white/10 animate-pulse mb-2" />
                  ) : (
                    <div className="flex items-baseline gap-2 mb-1">
                      <p className="text-4xl font-extrabold text-white tracking-tighter">{kpi.value}</p>
                    </div>
                  )}
                  <p className="text-[14px] font-bold text-slate-300">{kpi.label}</p>
                  <p className="text-[11px] text-slate-500 mt-1 uppercase tracking-widest font-bold">{kpi.sub}</p>
                </div>
              </div>
            );
          })}
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6 items-start">
          <motion.div variants={ITEM} className="rounded-2xl border border-white/[0.08] bg-[#0d1424]/40 p-6 backdrop-blur-md relative overflow-hidden group">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-indigo-400" />
                  Meetings timeline
                </h2>
                <p className="text-[12px] text-slate-500 mt-1">Daily distribution across sectors</p>
              </div>
              <div className="px-2 py-1 rounded bg-white/5 border border-white/10 text-[10px] font-bold text-slate-500 uppercase">Realtime</div>
            </div>

            {loading ? (
              <div className="min-h-[9rem] flex items-center justify-center">
                <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
              </div>
            ) : (
              <div className="min-h-[9rem]">
                <TimelineLineChart data={series.slice(-10)} height={140} />

                <div className="mt-3 flex flex-wrap gap-3 items-center">
                  {((data?.meeting_types) || []).map((t) => {
                    const colorMap: Record<string, string> = {
                      meeting: "bg-violet-600",
                      event: "bg-cyan-500",
                      birthday: "bg-orange-500",
                      task: "bg-emerald-500",
                      other: "bg-slate-400",
                    };
                    const color = colorMap[t.label] ?? colorMap.other;
                    return (
                      <div key={t.label} className="flex items-center gap-2 text-xs text-slate-400">
                        <span className={cn("w-3 h-3 rounded", color)} />
                        <span className="capitalize">{t.label}</span>
                        <span className="text-[11px] text-slate-500">{t.pct}%</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </motion.div>

          <div className="space-y-5">
            <motion.div variants={ITEM} className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-5">
              <h2 className="text-sm font-bold text-white mb-4">Meeting types</h2>
              <div className="space-y-3">
                {(data?.meeting_types || []).map((type) => (
                  <div key={type.label}>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs text-slate-400 font-medium capitalize">{type.label}</span>
                      <span className="text-xs text-slate-500">{type.count} ({type.pct}%)</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${type.pct}%` }}
                        transition={{ duration: 0.6, ease: "easeOut" }}
                        className="h-full rounded-full bg-violet-500"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            <motion.div variants={ITEM} className="rounded-xl border border-violet-500/20 bg-violet-500/5 p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-3.5 h-3.5 text-violet-400" />
                <span className="text-[11px] font-bold text-violet-300 uppercase tracking-wide">Summary</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">{data?.summary || "No analytics summary available yet."}</p>
            </motion.div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
