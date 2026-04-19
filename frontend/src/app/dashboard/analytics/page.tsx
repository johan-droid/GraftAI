"use client";

import { type ElementType } from "react";
import { useQuery } from "@/hooks/useQuery";
import { motion } from "framer-motion";
import {
  TrendingUp, Calendar, Clock, Activity,
  ArrowUpRight, RefreshCw,
} from "lucide-react";
import { MeetingsLine, MeetingsBar } from "@/components/Analytics/Charts";
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

  // Realtime series from backend proxy. Preferred for charts when available.
  const { data: realtime, isLoading: realtimeLoading } = useQuery<{
    series?: { bucket: string; meetings: number; hours?: number }[];
  }>("/api/analytics/realtime?range=30d", { revalidateInterval: 60_000 });

  const item = { hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0 } };
  const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
  const meetingsData = realtime?.series
    ? realtime.series.map((s) => ({ day: s.bucket, count: s.meetings }))
    : data?.details?.weeklyBreakdown ?? [];

  return (
    <ErrorBoundary>
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">

        <motion.div variants={item} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-h1 text-[var(--text)]">Analytics</h1>
            <p className="mt-1 text-sm text-[var(--text-muted)]">
              Your scheduling performance and AI usage metrics
            </p>
          </div>
          <button className="btn btn-ghost self-start" onClick={() => refetch()}>
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </motion.div>

        {error && (
          <motion.div
            variants={item}
            className="flex items-center gap-3 rounded-xl border border-[rgba(248,113,113,0.2)] bg-[rgba(248,113,113,0.08)] p-4 text-sm text-[var(--error)]"
          >
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
                trend={data?.details?.meetingsTrend ?? "No trend data yet"}
              />
              <MetricCard
                icon={Clock}
                label="AI Copilot Hours"
                value={data?.details?.hours ?? 0}
                suffix="h"
                color="info"
                trend={data?.details?.hoursTrend ?? "No trend data yet"}
              />
              <MetricCard
                icon={TrendingUp}
                label="Scheduling Efficiency"
                value={data?.details?.growth ?? 0}
                suffix="%"
                color="success"
                trend={data?.details?.growthTrend ?? "No trend data yet"}
              />
            </>
          )}
        </motion.div>

        <motion.div variants={item} className="card p-6 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-h3 font-semibold text-[var(--text)]">AI Summary</h2>
            <span className="badge badge-peach text-xs">
              <Activity className="w-3 h-3" /> Live
            </span>
          </div>
          {isLoading ? (
            <SkeletonText lines={4} />
          ) : data?.summary ? (
            <p className="text-sm leading-relaxed text-[var(--text-muted)]">
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

        { (realtime?.series || data?.details?.weeklyBreakdown) && (
          <motion.div variants={item} className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="card p-6">
              <h2 className="text-h3 font-semibold text-[var(--text)]">Meetings Over Time</h2>
              {/* prefer realtime.series if available */}
              <MeetingsLine data={meetingsData} />
            </div>
            <div className="card p-6">
              <h2 className="text-h3 font-semibold text-[var(--text)]">Meetings by Day</h2>
              <MeetingsBar data={meetingsData} />
            </div>
          </motion.div>
        )}

        {data?.details?.categoryBreakdown && (
          <motion.div variants={item} className="card p-6 space-y-4">
            <h2 className="text-h3 font-semibold text-[var(--text)]">By Category</h2>
            <div className="space-y-3">
              {data.details.categoryBreakdown.map(({ category, count }) => {
                const max = Math.max(...data.details!.categoryBreakdown!.map(c => c.count), 1);
                const pct = Math.round((count / max) * 100);
                return (
                  <div key={category} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="capitalize font-medium text-[var(--text)]">{category}</span>
                      <span className="text-[var(--text-muted)]">{count}</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-[var(--bg-hover)]">
                      <motion.div
                        className="h-full w-full origin-left rounded-full bg-[var(--peach)]"
                        initial={{ scaleX: 0 }}
                        animate={{ scaleX: pct / 100 }}
                        transition={{ duration: 0.6, ease: "easeOut" }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}

        <motion.div
          variants={item}
          className="flex items-start gap-3 rounded-xl border border-[var(--peach-border)] bg-[var(--peach-ghost)] p-4 text-sm"
        >
          <ArrowUpRight className="w-4 h-4 flex-shrink-0 text-[var(--peach)]" />
          <p className="text-[var(--text-muted)]">
            <strong className="text-[var(--peach)]">Tip:</strong> Ensure {" "}
            <code className="rounded bg-[var(--bg-hover)] px-1 py-0.5 text-xs">NEXT_PUBLIC_API_BASE_URL</code>{" "}
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
  icon: ElementType;
  label: string;
  value: number;
  suffix: string;
  color: "peach" | "info" | "success";
  trend: string;
}) {
  const variantMap: Record<typeof color, { iconWrap: string; icon: string; trend: string }> = {
    peach: {
      iconWrap: "bg-[var(--peach-ghost)]",
      icon: "text-[var(--peach)]",
      trend: "text-[var(--peach)]",
    },
    info: {
      iconWrap: "bg-[rgba(96,165,250,0.1)]",
      icon: "text-[var(--info)]",
      trend: "text-[var(--info)]",
    },
    success: {
      iconWrap: "bg-[rgba(52,211,153,0.1)]",
      icon: "text-[var(--success)]",
      trend: "text-[var(--success)]",
    },
  };
  const variant = variantMap[color];

  return (
    <div className="card p-5 space-y-3">
      <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${variant.iconWrap}`}>
        <Icon className={`w-5 h-5 ${variant.icon}`} />
      </div>
      <div>
        <p className="mb-1 text-xs font-medium text-[var(--text-muted)]">{label}</p>
        <p className="text-3xl font-bold text-[var(--text)]">
          {value}{suffix}
        </p>
        <p className={`mt-1 flex items-center gap-1 text-xs ${variant.trend}`}>
          <TrendingUp className="w-3 h-3" /> {trend}
        </p>
      </div>
    </div>
  );
}

// Replaced with Recharts-based visualizations in '@/components/Analytics/Charts'
