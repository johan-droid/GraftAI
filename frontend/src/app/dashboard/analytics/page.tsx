"use client";

import { useQuery } from "@/hooks/useQuery";
import { getAnalyticsSummary } from "@/lib/api";
import { motion } from "framer-motion";
import {
  TrendingUp, Calendar, Clock, Activity,
  ArrowUpRight, RefreshCw,
} from "lucide-react";
import { StatCardSkeleton, SkeletonText } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

export default function AnalyticsPage() {
  const { data, isLoading, error, refetch } = useQuery<{
    summary: string;
    details?: {
      meetings: number;
      hours: number;
      growth: number;
        meetingsTrend?: string;
        hoursTrend?: string;
        growthTrend?: string;
      weeklyBreakdown?: { day: string; count: number }[];
      categoryBreakdown?: { category: string; count: number }[];
    };
  }>("/api/analytics", { revalidateInterval: 60_000 });

  const item = { hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0 } };
  const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };

  return (
    <ErrorBoundary>
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">

        <motion.div variants={item} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-h1" style={{ color: "var(--text)" }}>Analytics</h1>
            <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
              Your scheduling performance and AI usage metrics
            </p>
          </div>
          <button className="btn btn-ghost self-start" onClick={() => refetch()}>
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </motion.div>

        {error && (
          <motion.div variants={item}
            className="flex items-center gap-3 p-4 rounded-xl text-sm"
            style={{ background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.2)", color: "var(--error)" }}>
            <Activity className="w-4 h-4 flex-shrink-0" />
            Failed to load analytics. {error.message}
            <button className="ml-auto underline text-xs" onClick={() => refetch()}>Retry</button>
          </motion.div>
        )}

        <motion.div variants={item} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => <StatCardSkeleton key={i} />)
          ) : (
            <>
              <MetricCard
                icon={Calendar}
                label="Meetings This Period"
                value={data?.details?.meetings ?? 0}
                suffix=""
                color="peach"
                trend={data?.details?.meetingsTrend ?? "(Example) +12% vs last month"}
              />
              <MetricCard
                icon={Clock}
                label="AI Copilot Hours"
                value={data?.details?.hours ?? 0}
                suffix="h"
                color="info"
                trend={data?.details?.hoursTrend ?? "(Example) Active this week"}
              />
              <MetricCard
                icon={TrendingUp}
                label="Scheduling Efficiency"
                value={data?.details?.growth ?? 0}
                suffix="%"
                color="success"
                trend={data?.details?.growthTrend ?? "(Example) Growth this month"}
              />
            </>
          )}
        </motion.div>

        <motion.div variants={item} className="card p-6 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-h3 font-semibold" style={{ color: "var(--text)" }}>AI Summary</h2>
            <span className="badge badge-peach text-xs">
              <Activity className="w-3 h-3" /> Live
            </span>
          </div>
          {isLoading ? (
            <SkeletonText lines={4} />
          ) : data?.summary ? (
            <p className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
              {data.summary}
            </p>
          ) : (
            <EmptyState
              icon={Activity}
              title="No analytics data yet"
              description="Start scheduling meetings to see your performance metrics."
            />
          )}
        </motion.div>

        {data?.details?.weeklyBreakdown && (
          <motion.div variants={item} className="card p-6 space-y-4">
            <h2 className="text-h3 font-semibold" style={{ color: "var(--text)" }}>Meetings by Day</h2>
            <BarChart data={data.details.weeklyBreakdown} />
          </motion.div>
        )}

        {data?.details?.categoryBreakdown && (
          <motion.div variants={item} className="card p-6 space-y-4">
            <h2 className="text-h3 font-semibold" style={{ color: "var(--text)" }}>By Category</h2>
            <div className="space-y-3">
              {data.details.categoryBreakdown.map(({ category, count }) => {
                const max = Math.max(...data.details!.categoryBreakdown!.map(c => c.count), 1);
                const pct = Math.round((count / max) * 100);
                return (
                  <div key={category} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="capitalize font-medium" style={{ color: "var(--text)" }}>{category}</span>
                      <span style={{ color: "var(--text-muted)" }}>{count}</span>
                    </div>
                    <div className="h-2 rounded-full overflow-hidden" style={{ background: "var(--bg-hover)" }}>
                      <motion.div
                        className="h-full rounded-full"
                        style={{ background: "var(--peach)", width: `${pct}%` }}
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.6, ease: "easeOut" }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}

        <motion.div variants={item}
          className="flex items-start gap-3 p-4 rounded-xl text-sm"
          style={{ background: "var(--peach-ghost)", border: "1px solid var(--peach-border)" }}>
          <ArrowUpRight className="w-4 h-4 flex-shrink-0" style={{ color: "var(--peach)" }} />
          <p style={{ color: "var(--text-muted)" }}>
            <strong style={{ color: "var(--peach)" }}>Tip:</strong> Ensure {" "}
            <code className="text-xs px-1 py-0.5 rounded" style={{ background: "var(--bg-hover)" }}>NEXT_PUBLIC_API_BASE_URL</code>{" "}
            is set to your deployed backend URL in Vercel environment variables.
          </p>
        </motion.div>
      </motion.div>
    </ErrorBoundary>
  );
}

function MetricCard({
  icon: Icon, label, value, suffix, color, trend,
}: {
  icon: React.ElementType;
  label: string;
  value: number;
  suffix: string;
  color: "peach" | "info" | "success";
  trend: string;
}) {
  const colorMap: Record<string, string> = {
    peach:   "var(--peach)",
    info:    "var(--info)",
    success: "var(--success)",
  };
  const bgMap: Record<string, string> = {
    peach:   "var(--peach-ghost)",
    info:    "rgba(96,165,250,0.1)",
    success: "rgba(52,211,153,0.1)",
  };
  const c = colorMap[color];

  return (
    <div className="card p-5 space-y-3">
      <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: bgMap[color] }}>
        <Icon className="w-5 h-5" style={{ color: c }} />
      </div>
      <div>
        <p className="text-xs font-medium mb-1" style={{ color: "var(--text-muted)" }}>{label}</p>
        <p className="text-3xl font-bold" style={{ color: "var(--text)" }}>
          {value}{suffix}
        </p>
        <p className="text-xs mt-1 flex items-center gap-1" style={{ color: c }}>
          <TrendingUp className="w-3 h-3" /> {trend}
        </p>
      </div>
    </div>
  );
}

function BarChart({ data }: { data: { day: string; count: number }[] }) {
  const max = Math.max(...data.map(d => d.count), 1);
  return (
    <div className="flex items-end gap-2 h-32">
      {data.map(({ day, count }) => {
        const pct = (count / max) * 100;
        return (
          <div key={day} className="flex-1 flex flex-col items-center gap-1">
            <span className="text-[11px] font-medium" style={{ color: "var(--text-muted)" }}>{count}</span>
            <motion.div
              className="w-full rounded-t-md"
              style={{ background: "var(--peach)", opacity: pct > 0 ? 0.7 + (pct / 100) * 0.3 : 0.2 }}
              initial={{ height: 0 }}
              animate={{ height: `${Math.max(pct, 4)}%` }}
              transition={{ duration: 0.5, ease: "easeOut", delay: 0.1 }}
            />
            <span className="text-[10px]" style={{ color: "var(--text-faint)" }}>{day.slice(0, 3)}</span>
          </div>
        );
      })}
    </div>
  );
}
