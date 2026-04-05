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

function Bar({ value, max }: { value: number; max: number }) {
  const levels = ["h-2", "h-3", "h-4", "h-6", "h-8", "h-10", "h-12", "h-14", "h-16", "h-20"];
  const idx = max > 0 ? Math.min(levels.length - 1, Math.max(0, Math.round((value / max) * (levels.length - 1)))) : 0;
  return <div className={`w-full rounded-t-md bg-indigo-500/70 ${levels[idx]}`} />;
}

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
  const maxMeetings = useMemo(
    () => (series.length ? Math.max(...series.map((point) => point.meetings)) : 1),
    [series]
  );

  const totals = data?.totals || {
    meetings: 0,
    hours: 0,
    growth: 0,
    unique_attendees: 0,
    cancellations: 0,
  };

  return (
    <div className="p-5 md:p-7 max-w-[1300px] mx-auto">
      <motion.div variants={STAGGER} initial="hidden" animate="visible" className="space-y-6">
        <motion.div variants={ITEM} className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Analytics</h1>
            <p className="text-slate-500 text-sm mt-0.5">Real-time scheduling metrics from your calendar records</p>
          </div>
          <div className="sm:ml-auto flex items-center gap-1 p-1 rounded-lg bg-white/5 border border-white/8">
            {(["7d", "30d", "90d"] as const).map((r) => (
              <button
                key={r}
                onClick={() => handleRangeChange(r)}
                className={`px-3 py-1.5 rounded-md text-[13px] font-semibold transition-all ${
                  range === r ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-white"
                }`}
              >
                {r === "7d" ? "7 days" : r === "30d" ? "30 days" : "90 days"}
              </button>
            ))}
          </div>
        </motion.div>

        {error && (
          <motion.div variants={ITEM} className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
            {error}
          </motion.div>
        )}

        <motion.div variants={ITEM} className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Total meetings", value: totals.meetings.toString(), icon: Calendar, color: "indigo", sub: `${totals.growth}% growth` },
            { label: "Hours scheduled", value: `${totals.hours}h`, icon: Clock, color: "violet", sub: "Computed from event durations" },
            { label: "Unique attendees", value: totals.unique_attendees.toString(), icon: Users, color: "cyan", sub: "Distinct attendee emails" },
            { label: "Cancellations", value: totals.cancellations.toString(), icon: Zap, color: "emerald", sub: "Canceled events in range" },
          ].map((kpi) => {
            const styles = KPI_STYLES[kpi.color];
            return (
              <div key={kpi.label} className="rounded-xl border border-white/[0.07] bg-white/[0.025] p-4">
                <div className={`w-8 h-8 rounded-lg mb-3 flex items-center justify-center ${styles.bg} ${styles.border}`}>
                  <kpi.icon className={`w-4 h-4 ${styles.icon}`} />
                </div>
                {loading ? (
                  <div className="h-7 w-20 rounded bg-white/10 animate-pulse" />
                ) : (
                  <p className="text-2xl font-bold text-white mb-0.5">{kpi.value}</p>
                )}
                <p className="text-xs text-slate-500">{kpi.label}</p>
                <p className="text-[11px] text-slate-500 mt-1">{kpi.sub}</p>
              </div>
            );
          })}
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-5">
          <motion.div variants={ITEM} className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-5">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-sm font-bold text-white">Meetings timeline</h2>
                <p className="text-xs text-slate-500 mt-0.5">Live daily buckets from backend aggregation</p>
              </div>
              <BarChart3 className="w-4 h-4 text-slate-600" />
            </div>

            {loading ? (
              <div className="h-36 flex items-center justify-center">
                <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
              </div>
            ) : (
              <div className="grid grid-cols-7 md:grid-cols-10 gap-2 items-end h-36">
                {series.slice(-10).map((point) => (
                  <div key={`${point.bucket}-${point.meetings}-${point.hours}`} className="flex flex-col items-center gap-1">
                    <span className="text-[10px] text-slate-500 font-semibold">{point.meetings}</span>
                    <div className="relative h-20 w-full flex items-end">
                      <Bar value={point.meetings} max={maxMeetings} />
                    </div>
                    <span className="text-[10px] text-slate-600 font-medium">{point.bucket}</span>
                  </div>
                ))}
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
