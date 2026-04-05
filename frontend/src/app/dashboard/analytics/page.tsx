"use client";

import { useEffect, useState } from "react";
import { getAnalyticsSummary } from "@/lib/api";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  Calendar,
  Clock,
  Users,
  BarChart3,
  Zap,
  Globe,
} from "lucide-react";

const STAGGER = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const ITEM = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
};

const WEEKLY_DATA = [
  { day: "Mon", meetings: 4, hours: 3.5 },
  { day: "Tue", meetings: 7, hours: 6.0 },
  { day: "Wed", meetings: 5, hours: 4.5 },
  { day: "Thu", meetings: 9, hours: 7.5 },
  { day: "Fri", meetings: 6, hours: 5.0 },
  { day: "Sat", meetings: 2, hours: 1.5 },
  { day: "Sun", meetings: 1, hours: 1.0 },
];

const MEETING_TYPES = [
  { label: "Discovery calls", count: 24, pct: 42, color: "bg-indigo-500" },
  { label: "Team syncs", count: 18, pct: 31, color: "bg-violet-500" },
  { label: "1:1 sessions", count: 10, pct: 17, color: "bg-cyan-500" },
  { label: "Other", count: 6, pct: 10, color: "bg-slate-500" },
];

const KPI_STYLES: Record<string, { bg: string; border: string; icon: string }> = {
  indigo: {
    bg: "bg-indigo-500/10",
    border: "border-indigo-500/20",
    icon: "text-indigo-400",
  },
  violet: {
    bg: "bg-violet-500/10",
    border: "border-violet-500/20",
    icon: "text-violet-400",
  },
  cyan: {
    bg: "bg-cyan-500/10",
    border: "border-cyan-500/20",
    icon: "text-cyan-400",
  },
  emerald: {
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    icon: "text-emerald-400",
  },
};

function MiniBar({ value, max, color }: { value: number; max: number; color: string }) {
  return (
    <div className="relative h-16 flex items-end">
      <motion.div
        initial={{ height: 0 }}
        animate={{ height: `${(value / max) * 100}%` }}
        transition={{ duration: 0.7, ease: "easeOut", delay: 0.2 }}
        className={`w-full rounded-t-md ${color}`}
      />
    </div>
  );
}

export default function AnalyticsPage() {
  const [data, setData] = useState<{ summary: string; details?: { meetings: number; hours: number; growth: number } }>({ summary: "" });
  const [loading, setLoading] = useState(true);
  const [range, setRange] = useState<"7d" | "30d" | "90d">("30d");

  useEffect(() => {
    getAnalyticsSummary()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [range]);

  const meetings = data.details?.meetings ?? 58;
  const hours = data.details?.hours ?? 42.5;
  const growth = data.details?.growth ?? 14.2;
  const maxMeetings = Math.max(...WEEKLY_DATA.map((d) => d.meetings));

  return (
    <div className="p-5 md:p-7 max-w-[1400px] mx-auto">
      <motion.div variants={STAGGER} initial="hidden" animate="visible" className="space-y-6">

        {/* Header */}
        <motion.div variants={ITEM} className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Analytics</h1>
            <p className="text-slate-500 text-sm mt-0.5">Your scheduling insights at a glance</p>
          </div>
          <div className="sm:ml-auto flex items-center gap-1 p-1 rounded-lg bg-white/5 border border-white/8">
            {(["7d", "30d", "90d"] as const).map((r) => (
              <button
                key={r}
                onClick={() => {
                  setLoading(true);
                  setRange(r);
                }}
                className={`px-3 py-1.5 rounded-md text-[13px] font-semibold transition-all ${
                  range === r ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-white"
                }`}
              >
                {r === "7d" ? "7 days" : r === "30d" ? "30 days" : "90 days"}
              </button>
            ))}
          </div>
        </motion.div>

        {/* KPI Cards */}
        <motion.div variants={ITEM} className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            {
              label: "Total meetings",
              value: meetings.toString(),
              sub: `+${growth}% vs prev.`,
              trend: "up",
              icon: Calendar,
              color: "indigo",
            },
            {
              label: "Hours scheduled",
              value: `${hours}h`,
              sub: "+8.5h vs prev.",
              trend: "up",
              icon: Clock,
              color: "violet",
            },
            {
              label: "Unique attendees",
              value: "47",
              sub: "+12 new",
              trend: "up",
              icon: Users,
              color: "cyan",
            },
            {
              label: "Cancellations",
              value: "5",
              sub: "-2 vs prev.",
              trend: "down",
              icon: Zap,
              color: "emerald",
            },
          ].map((kpi) => {
            const styles = KPI_STYLES[kpi.color];
            return (
              <div key={kpi.label} className="rounded-xl border border-white/[0.07] bg-white/[0.025] p-4">
                <div className={`w-8 h-8 rounded-lg mb-3 flex items-center justify-center ${styles.bg} ${styles.border}`}>
                  <kpi.icon className={`w-4 h-4 ${styles.icon}`} />
                </div>
                {loading ? (
                  <div className="h-8 w-20 bg-white/5 rounded-lg animate-pulse mb-1" />
                ) : (
                  <p className="text-2xl font-bold text-white mb-0.5">{kpi.value}</p>
                )}
                <p className="text-xs text-slate-500">{kpi.label}</p>
                <div className={`flex items-center gap-1 mt-1.5 text-xs font-semibold ${kpi.trend === "up" ? "text-emerald-400" : "text-red-400"}`}>
                  {kpi.trend === "up" ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                  {kpi.sub}
                </div>
              </div>
            );
          })}
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-5">
          {/* Bar Chart */}
          <motion.div variants={ITEM} className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-5">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-sm font-bold text-white">Meetings per day</h2>
                <p className="text-xs text-slate-500 mt-0.5">This week&apos;s distribution</p>
              </div>
              <BarChart3 className="w-4 h-4 text-slate-600" />
            </div>

            <div className="grid grid-cols-7 gap-2 items-end h-24">
              {WEEKLY_DATA.map((d) => (
                <div key={d.day} className="flex flex-col items-center gap-1">
                  <span className="text-[10px] text-slate-500 font-semibold">{d.meetings}</span>
                  <div className="w-full">
                    <MiniBar value={d.meetings} max={maxMeetings} color="bg-indigo-500/60 hover:bg-indigo-500 transition-colors" />
                  </div>
                  <span className="text-[10px] text-slate-600 font-medium">{d.day}</span>
                </div>
              ))}
            </div>

            <div className="mt-6 pt-5 border-t border-white/[0.05]">
              <div className="flex items-center gap-4 mb-3">
                <span className="flex items-center gap-1.5 text-xs text-slate-400">
                  <span className="w-3 h-0.5 bg-indigo-400 rounded-full inline-block" /> Meetings
                </span>
                <span className="flex items-center gap-1.5 text-xs text-slate-400">
                  <span className="w-3 h-0.5 bg-violet-400 rounded-full inline-block" /> Hours
                </span>
              </div>
              <svg viewBox="0 0 300 60" className="w-full h-14" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="meetGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6366f1" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
                  </linearGradient>
                  <linearGradient id="hourGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <path d="M0,45 L43,30 L86,38 L129,15 L172,22 L215,35 L258,12 L300,18 L300,60 L0,60 Z" fill="url(#meetGrad)" />
                <path d="M0,45 L43,30 L86,38 L129,15 L172,22 L215,35 L258,12 L300,18" fill="none" stroke="#6366f1" strokeWidth="1.5" strokeLinecap="round" />
                <path d="M0,50 L43,36 L86,42 L129,22 L172,28 L215,40 L258,18 L300,25 L300,60 L0,60 Z" fill="url(#hourGrad)" />
                <path d="M0,50 L43,36 L86,42 L129,22 L172,28 L215,40 L258,18 L300,25" fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="4 2" />
              </svg>
            </div>
          </motion.div>

          {/* Right column */}
          <div className="space-y-5">
            <motion.div variants={ITEM} className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-5">
              <h2 className="text-sm font-bold text-white mb-4">Meeting types</h2>
              <div className="space-y-3">
                {MEETING_TYPES.map((mt) => (
                  <div key={mt.label}>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs text-slate-400 font-medium">{mt.label}</span>
                      <span className="text-xs text-slate-500">{mt.count} ({mt.pct}%)</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${mt.pct}%` }}
                        transition={{ duration: 0.8, ease: "easeOut", delay: 0.3 }}
                        className={`h-full rounded-full ${mt.color}`}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            <motion.div variants={ITEM} className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-5">
              <h2 className="text-sm font-bold text-white mb-4">Peak booking hours</h2>
              <div className="space-y-2">
                {[
                  { time: "10:00 AM", count: 18, pct: 85 },
                  { time: "2:00 PM", count: 15, pct: 72 },
                  { time: "11:00 AM", count: 12, pct: 58 },
                  { time: "3:00 PM", count: 9, pct: 43 },
                ].map((t) => (
                  <div key={t.time} className="flex items-center gap-3">
                    <span className="text-[12px] text-slate-500 font-mono w-20 shrink-0">{t.time}</span>
                    <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${t.pct}%` }}
                        transition={{ duration: 0.7, ease: "easeOut", delay: 0.4 }}
                        className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500"
                      />
                    </div>
                    <span className="text-[11px] text-slate-600 font-medium w-6 text-right">{t.count}</span>
                  </div>
                ))}
              </div>
            </motion.div>

            <motion.div variants={ITEM} className="rounded-xl border border-violet-500/20 bg-violet-500/5 p-4">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="w-3.5 h-3.5 text-violet-400" />
                <span className="text-[11px] font-bold text-violet-300 uppercase tracking-wide">AI Summary</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                {data.summary ||
                  "Your busiest day is Thursday with 9 meetings. Consider blocking focus time on Wednesday mornings to balance your schedule."}
              </p>
            </motion.div>
          </div>
        </div>

        <motion.div variants={ITEM} className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-5">
          <div className="flex items-center gap-2 mb-5">
            <Globe className="w-4 h-4 text-slate-500" />
            <h2 className="text-sm font-bold text-white">Geographic reach</h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { country: "🇮🇳 India", attendees: 28, pct: 48 },
              { country: "🇺🇸 United States", attendees: 18, pct: 31 },
              { country: "🇬🇧 United Kingdom", attendees: 8, pct: 14 },
              { country: "🌍 Other", attendees: 4, pct: 7 },
            ].map((g) => (
              <div key={g.country} className="p-3 rounded-lg bg-white/[0.025] border border-white/[0.05]">
                <p className="text-sm font-medium text-slate-300 mb-1">{g.country}</p>
                <p className="text-xl font-bold text-white">{g.attendees}</p>
                <p className="text-xs text-slate-600 mt-0.5">{g.pct}% of total</p>
                <div className="mt-2 h-1 rounded-full bg-white/5">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${g.pct}%` }}
                    transition={{ duration: 0.7, delay: 0.5 }}
                    className="h-full rounded-full bg-indigo-500/60"
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>

      </motion.div>
    </div>
  );
}
