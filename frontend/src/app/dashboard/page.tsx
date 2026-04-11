"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthContext } from "@/app/providers/auth-provider";
import { motion } from "framer-motion";
import {
  Calendar, Activity, ArrowUpRight, TrendingUp,
  Sparkles, Plus, Clock, Users, Bot,
} from "lucide-react";
import { useQuery } from "@/hooks/useQuery";
import { getAnalyticsSummary, getProactiveSuggestion } from "@/lib/api";
import { StatCardSkeleton, CardSkeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, loading } = useAuthContext();

  useEffect(() => {
    if (!loading && !isAuthenticated) router.replace("/login");
  }, [isAuthenticated, loading, router]);

  const { data: analytics, isLoading: analyticsLoading } = useQuery<{
    summary: string;
    details?: { meetings: number; hours: number; growth: number };
  }>(isAuthenticated ? "/api/analytics" : null);

  const { data: suggestion, isLoading: suggestionLoading } = useQuery<{
    suggestion: string;
  }>(isAuthenticated ? "/api/proactive" : null);

  const { data: upcomingEvents, isLoading: eventsLoading } = useQuery<{
    id: number; title: string; start_time: string; category: string;
  }[]>(isAuthenticated ? "/api/events/upcoming" : null);

  if (loading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-7 h-7 rounded-full border-2 border-t-transparent animate-spin"
          style={{ borderColor: "var(--peach)", borderTopColor: "transparent" }} />
      </div>
    );
  }

  type DashUser = { name?: string; email?: string } | null;
  const displayUser = user as DashUser;
  const firstName = displayUser?.name?.split(" ")[0] ?? displayUser?.email?.split("@")[0] ?? "there";

  const stats = analytics?.details ?? { meetings: null, hours: null, growth: null, previousWeekMeetings: null };
  const meetingsDelta = stats.meetings != null && stats.previousWeekMeetings != null 
    ? stats.meetings - stats.previousWeekMeetings 
    : null;
  const meetingsTrend = meetingsDelta != null 
    ? `${meetingsDelta > 0 ? "+" : ""}${meetingsDelta} from last week` 
    : undefined;

  const item = {
    hidden: { opacity: 0, y: 16 },
    show:   { opacity: 1, y: 0 },
  };
  const container = {
    hidden: {},
    show: { transition: { staggerChildren: 0.07 } },
  };

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">

      {/* ── Header ── */}
      <motion.header variants={item} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-h1" style={{ color: "var(--text)" }}>
            Good {getTimeOfDay()}, {firstName} 👋
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
          </p>
        </div>
        <Link href="/dashboard/calendar"
          className="btn btn-primary self-start sm:self-auto">
          <Plus className="w-4 h-4" /> New Booking
        </Link>
      </motion.header>

      {/* ── Stat Cards ── */}
      <motion.div variants={item} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {analyticsLoading ? (
          Array.from({ length: 3 }).map((_, i) => <StatCardSkeleton key={i} />)
        ) : (
          <>
            <StatCard
              icon={Calendar}
              label="Meetings This Week"
              value={stats.meetings != null ? String(stats.meetings) : "—"}
              trend={meetingsTrend}
              href="/dashboard/calendar"
              color="peach"
            />
            <StatCard
              icon={Bot}
              label="AI Copilot Hours"
              value={stats.hours != null ? `${stats.hours}h` : "—"}
              trend={stats.growth != null ? `${stats.growth}% growth` : undefined}
              href="/dashboard/ai"
              color="info"
            />
            <StatCard
              icon={Activity}
              label="System Status"
              value="Operational"
              badge={{ label: "All systems go", color: "success" }}
              href="/dashboard/analytics"
              color="success"
            />
          </>
        )}
      </motion.div>

      {/* ── Main Grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Recent Activity */}
        <motion.section variants={item} className="lg:col-span-2 card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-h3 font-semibold" style={{ color: "var(--text)" }}>Recent Activity</h2>
            <Link href="/dashboard/analytics" className="text-xs font-medium flex items-center gap-1 hover:underline"
              style={{ color: "var(--peach)" }}>
              View all <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>

          {analyticsLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="flex gap-3">
                  <div className="skeleton h-8 w-8 rounded-lg flex-shrink-0" />
                  <div className="flex-1 space-y-1.5">
                    <div className="skeleton h-3 w-3/4" />
                    <div className="skeleton h-3 w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : analytics?.summary ? (
            <p className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
              {analytics.summary}
            </p>
          ) : (
            <EmptyState
              icon={Activity}
              title="No recent activity"
              description="Your meetings and events will appear here."
            />
          )}
        </motion.section>

        {/* Sidebar Panel */}
        <motion.div variants={item} className="space-y-4">

          {/* Upcoming Events */}
          <div className="card p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold" style={{ color: "var(--text)" }}>Upcoming</h3>
              <Link href="/dashboard/calendar" className="text-xs hover:underline" style={{ color: "var(--peach)" }}>
                Calendar →
              </Link>
            </div>

            {eventsLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="flex gap-3">
                    <div className="skeleton h-8 w-8 rounded-lg" />
                    <div className="flex-1 space-y-1">
                      <div className="skeleton h-3 w-3/4" />
                      <div className="skeleton h-2.5 w-1/2" />
                    </div>
                  </div>
                ))}
              </div>
            ) : upcomingEvents && upcomingEvents.length > 0 ? (
              <div className="space-y-2">
                {upcomingEvents.slice(0, 4).map((evt) => (
                  <div key={evt.id} className="flex items-center gap-3 py-2 border-b last:border-0"
                    style={{ borderColor: "var(--border)" }}>
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                      style={{ background: "var(--peach-ghost)" }}>
                      <Calendar className="w-4 h-4" style={{ color: "var(--peach)" }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate" style={{ color: "var(--text)" }}>{evt.title}</p>
                      <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>
                        <Clock className="w-3 h-3 inline mr-1" />
                        {new Date(evt.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-center py-4" style={{ color: "var(--text-faint)" }}>
                No upcoming events
              </p>
            )}
          </div>

          {/* AI Suggestion */}
          <div className="card-peach p-5 space-y-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4" style={{ color: "var(--peach)" }} />
              <span className="text-xs font-semibold text-label" style={{ color: "var(--peach)" }}>
                AI Insight
              </span>
            </div>
            {suggestionLoading ? (
              <div className="space-y-2">
                <div className="skeleton h-3 w-full" />
                <div className="skeleton h-3 w-3/4" />
              </div>
            ) : suggestion?.suggestion ? (
              <p className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
                {suggestion.suggestion}
              </p>
            ) : (
              <p className="text-xs" style={{ color: "var(--text-faint)" }}>
                Ask the AI Copilot for personalized scheduling insights.
              </p>
            )}
            <Link href="/dashboard/ai" className="btn btn-primary text-xs py-2 px-3 min-h-0">
              <Bot className="w-3.5 h-3.5" /> Open Copilot
            </Link>
          </div>

          {/* Quick Links */}
          <div className="card p-5 space-y-2">
            <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text)" }}>Quick Access</h3>
            {[
              { label: "Plugins & Integrations", href: "/dashboard/plugins", icon: Users },
              { label: "Privacy & Settings",     href: "/dashboard/settings", icon: Activity },
            ].map(({ label, href, icon: Icon }) => (
              <Link key={href} href={href}
                className="flex items-center justify-between py-2.5 px-3 rounded-lg transition-colors"
                style={{ color: "var(--text-muted)" }}
                onMouseEnter={e => (e.currentTarget.style.background = "var(--bg-hover)")}
                onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
              >
                <span className="text-sm flex items-center gap-2">
                  <Icon className="w-4 h-4" /> {label}
                </span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            ))}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}

// ── Helpers ────────────────────────────────────────────────────────
function getTimeOfDay() {
  const h = new Date().getHours();
  if (h < 12) return "morning";
  if (h < 17) return "afternoon";
  return "evening";
}

function StatCard({
  icon: Icon, label, value, trend, badge, href, color,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  trend?: string;
  badge?: { label: string; color: string };
  href: string;
  color: "peach" | "info" | "success";
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
  const bg = bgMap[color];

  return (
    <Link href={href} className="card p-5 group block hover:scale-[1.01] transition-transform">
      <div className="flex items-start justify-between mb-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: bg }}>
          <Icon className="w-5 h-5" style={{ color: c }} />
        </div>
        <ArrowUpRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: c }} />
      </div>
      <p className="text-xs font-medium mb-1" style={{ color: "var(--text-muted)" }}>{label}</p>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold" style={{ color: "var(--text)" }}>{value}</span>
        {trend && (
          <span className="text-xs font-medium flex items-center gap-0.5" style={{ color: "var(--success)" }}>
            <TrendingUp className="w-3 h-3" /> {trend}
          </span>
        )}
        {badge && (
          <span className={`badge badge-${badge.color} text-xs`}>{badge.label}</span>
        )}
      </div>
    </Link>
  );
}
