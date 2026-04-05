"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthContext } from "@/app/providers/auth-provider";
import { motion } from "framer-motion";
import {
  Calendar,
  ArrowUpRight,
  Clock,
  Video,
  MapPin,
  Users,
  Sparkles,
  TrendingUp,
  MoreHorizontal,
  ChevronRight,
  Globe,
  Activity,
} from "lucide-react";
import { getAnalyticsSummary, getEvents, getProactiveSuggestion, type CalendarEvent } from "@/lib/api";

const STAGGER = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.07 } },
};

const ITEM = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
};

const QUICK_LINKS = [
  { label: "30 Min Meeting", slug: "30min", icon: Clock, color: "from-indigo-500 to-violet-500" },
  { label: "60 Min Call", slug: "60min", icon: Video, color: "from-violet-500 to-fuchsia-500" },
  { label: "Team Sync", slug: "team-sync", icon: Users, color: "from-cyan-500 to-blue-500" },
];

const STAT_COLOR_CLASSES: Record<string, string> = {
  indigo: "bg-indigo-500/10 border-indigo-500/20 text-indigo-300",
  violet: "bg-violet-500/10 border-violet-500/20 text-violet-300",
  emerald: "bg-emerald-500/10 border-emerald-500/20 text-emerald-300",
  cyan: "bg-cyan-500/10 border-cyan-500/20 text-cyan-300",
};

type DashboardActivityItem = {
  id: number;
  title: string;
  start_time: string;
  category?: string;
  is_upcoming?: boolean;
};

function formatEventTimeLabel(iso: string) {
  const date = new Date(iso);
  return date.toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatRelativeTime(iso: string) {
  const target = new Date(iso).getTime();
  const now = Date.now();
  const diffMs = target - now;
  const future = diffMs >= 0;
  const absMinutes = Math.round(Math.abs(diffMs) / 60000);

  if (absMinutes < 1) return "just now";
  if (absMinutes < 60) return future ? `in ${absMinutes}m` : `${absMinutes}m ago`;

  const absHours = Math.round(absMinutes / 60);
  if (absHours < 24) return future ? `in ${absHours}h` : `${absHours}h ago`;

  const absDays = Math.round(absHours / 24);
  return future ? `in ${absDays}d` : `${absDays}d ago`;
}

function getDurationLabel(startIso: string, endIso: string) {
  const start = new Date(startIso).getTime();
  const end = new Date(endIso).getTime();
  const mins = Math.max(1, Math.round((end - start) / 60000));
  return `${mins} min`;
}

function getAttendeeCount(payload?: Record<string, unknown>) {
  const raw = payload?.attendees_count;
  if (typeof raw === "number" && Number.isFinite(raw)) {
    return raw;
  }
  return null;
}

export default function Dashboard() {
  const router = useRouter();
  const { user, isAuthenticated, loading } = useAuthContext();
  const typedUser = user as { name?: string; email?: string } | null;

  const profileName = typedUser?.name?.split(" ")[0] ?? typedUser?.email?.split("@")[0] ?? "there";

  const [stats, setStats] = useState({ meetings: 0, hours: 0, cancellations: 0 });
  const [upcomingMeetings, setUpcomingMeetings] = useState<CalendarEvent[]>([]);
  const [activityItems, setActivityItems] = useState<DashboardActivityItem[]>([]);
  const [aiSuggestion, setAiSuggestion] = useState("");

  useEffect(() => {
    if (!loading && !isAuthenticated) router.replace("/login");
  }, [loading, isAuthenticated, router]);

  useEffect(() => {
    if (!isAuthenticated) return;

    let alive = true;
    const now = new Date();
    const end = new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000);

    Promise.allSettled([
      getAnalyticsSummary("30d"),
      getProactiveSuggestion("dashboard overview"),
      getEvents(now.toISOString(), end.toISOString()),
    ]).then((results) => {
      if (!alive) return;

      const [analyticsResult, suggestionResult, eventsResult] = results;

      if (analyticsResult.status === "fulfilled") {
        const details = analyticsResult.value.details;
        setStats({
          meetings: Number(details?.meetings || 0),
          hours: Number(details?.hours || 0),
          cancellations: Number(details?.cancellations || 0),
        });
        setActivityItems(details?.recent_events || []);
      }

      if (suggestionResult.status === "fulfilled") {
        setAiSuggestion(suggestionResult.value.suggestion || "");
      }

      if (eventsResult.status === "fulfilled") {
        const sorted = [...eventsResult.value]
          .filter((event) => new Date(event.end_time).getTime() >= Date.now())
          .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());
        setUpcomingMeetings(sorted.slice(0, 6));
      }
    });

    return () => {
      alive = false;
    };
  }, [isAuthenticated]);

  if (loading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-6 h-6 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <div className="p-5 md:p-7 max-w-[1400px] mx-auto">
      <motion.div variants={STAGGER} initial="hidden" animate="visible" className="space-y-6">
        <motion.div variants={ITEM} className="flex flex-col md:flex-row md:items-center gap-4 pb-1">
          <div>
            <p className="text-slate-500 text-sm font-medium mb-0.5">{greeting} 👋</p>
            <h1 className="text-2xl font-bold text-white tracking-tight">{profileName}&apos;s workspace</h1>
          </div>
          <div className="md:ml-auto flex items-center gap-2">
            <Link
              href="/dashboard/calendar"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-all shadow-lg shadow-indigo-600/20"
            >
              <Calendar className="w-4 h-4" />
              New booking
            </Link>
          </div>
        </motion.div>

        <motion.div variants={ITEM} className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Upcoming meetings (30d)", value: stats.meetings, sub: "Current + future only", icon: Calendar, color: "indigo" },
            { label: "Hours scheduled", value: `${stats.hours}h`, sub: "Total booked duration", icon: Clock, color: "violet" },
            { label: "Cancellations (30d)", value: stats.cancellations, sub: "Canceled upcoming events", icon: TrendingUp, color: "emerald" },
            { label: "Upcoming (14 days)", value: upcomingMeetings.length, sub: "Live events window", icon: Activity, color: "cyan" },
          ].map((stat) => (
            <div key={stat.label} className="relative overflow-hidden rounded-xl border border-white/[0.07] bg-white/[0.03] p-4 hover:bg-white/[0.05] transition-colors">
              <div className={`${STAT_COLOR_CLASSES[stat.color]} w-8 h-8 rounded-lg mb-3 flex items-center justify-center`}>
                <stat.icon className="w-4 h-4 text-current" />
              </div>
              <p className="text-2xl font-bold text-white mb-1">{stat.value}</p>
              <p className="text-xs text-slate-500 font-medium">{stat.label}</p>
              <p className="text-xs text-emerald-400 font-medium mt-1">{stat.sub}</p>
            </div>
          ))}
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
          <motion.div variants={ITEM}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-white">Upcoming meetings</h2>
              <Link href="/dashboard/calendar" className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1">
                View calendar <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="space-y-2">
              {upcomingMeetings.length === 0 && (
                <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6 text-center text-sm text-slate-400">
                  No upcoming events found. Create your first booking from the calendar page.
                </div>
              )}

              {upcomingMeetings.map((meeting, i) => {
                const attendees = getAttendeeCount(meeting.metadata_payload);
                return (
                  <motion.div
                    key={meeting.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.06, duration: 0.3 }}
                    className="group flex items-center gap-4 p-4 rounded-xl border border-white/[0.06] bg-white/[0.025] hover:bg-white/[0.05] hover:border-white/10 transition-all"
                  >
                    <div className="w-1 h-10 rounded-full shrink-0 bg-indigo-500/70" />
                    <div className="min-w-0 flex-1">
                      <p className="text-[14px] font-semibold text-white truncate">{meeting.title}</p>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="flex items-center gap-1 text-[12px] text-slate-400">
                          <Clock className="w-3 h-3" /> {formatEventTimeLabel(meeting.start_time)}
                        </span>
                        <span className="text-[11px] px-1.5 py-0.5 rounded-md border font-medium bg-indigo-500/10 border-indigo-500/20 text-indigo-300">
                          {getDurationLabel(meeting.start_time, meeting.end_time)}
                        </span>
                      </div>
                    </div>

                    <div className="hidden sm:flex items-center gap-2 shrink-0">
                      {attendees !== null && (
                        <div className="flex items-center gap-1 text-[12px] text-slate-500">
                          <Users className="w-3 h-3" />
                          <span>{attendees}</span>
                        </div>
                      )}
                      {meeting.is_remote ? (
                        <Video className="w-3.5 h-3.5 text-slate-500" />
                      ) : (
                        <MapPin className="w-3.5 h-3.5 text-slate-500" />
                      )}
                    </div>

                    <button
                      onClick={() => router.push("/dashboard/calendar")}
                      className="p-1.5 rounded-md text-slate-600 hover:text-slate-300 hover:bg-white/8 transition-all opacity-0 group-hover:opacity-100"
                      aria-label="More options"
                    >
                      <MoreHorizontal className="w-4 h-4" />
                    </button>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>

          <div className="space-y-5">
            <motion.div variants={ITEM}>
              <h2 className="text-base font-bold text-white mb-3">Event types</h2>
              <div className="space-y-2">
                {QUICK_LINKS.map((ql) => (
                  <div key={ql.slug} className="group flex items-center gap-3 p-3 rounded-xl border border-white/[0.06] bg-white/[0.025] hover:bg-white/[0.05] hover:border-white/10 transition-all cursor-pointer">
                    <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${ql.color} flex items-center justify-center shrink-0`}>
                      <ql.icon className="w-4 h-4 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-semibold text-slate-200">{ql.label}</p>
                      <p className="text-[11px] text-slate-500 font-mono">Calendar event template</p>
                    </div>
                    <button
                      onClick={() => router.push("/dashboard/calendar")}
                      className="p-1.5 rounded-md text-slate-600 hover:text-slate-300 transition-all opacity-0 group-hover:opacity-100"
                      aria-label="Open event type"
                    >
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
                <Link
                  href="/dashboard/calendar"
                  className="flex items-center justify-center gap-2 p-3 rounded-xl border border-dashed border-white/10 text-slate-500 hover:text-slate-300 hover:border-white/20 text-[13px] font-medium transition-all"
                >
                  + New event type
                </Link>
              </div>
            </motion.div>

            {aiSuggestion && (
              <motion.div variants={ITEM} className="p-4 rounded-xl border border-violet-500/20 bg-violet-500/5">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-3.5 h-3.5 text-violet-400" />
                  <span className="text-[11px] font-bold text-violet-300 uppercase tracking-wide">AI Insight</span>
                </div>
                <p className="text-[13px] text-slate-300 leading-relaxed">{aiSuggestion}</p>
              </motion.div>
            )}

            <motion.div variants={ITEM}>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-base font-bold text-white">Activity</h2>
                <Link href="/dashboard/analytics" className="text-xs text-indigo-400 hover:text-indigo-300">
                  Analytics →
                </Link>
              </div>
              <div className="space-y-3">
                {activityItems.length === 0 && (
                  <div className="text-xs text-slate-500 rounded-lg border border-white/10 bg-white/[0.02] p-3">
                    Activity will appear here after calendar events are created or synced.
                  </div>
                )}

                {activityItems.map((item) => (
                  <div key={item.id} className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-white/5 border border-white/8 flex items-center justify-center shrink-0 mt-0.5">
                      {item.is_upcoming ? (
                        <Calendar className="w-3 h-3 text-slate-400" />
                      ) : (
                        <Globe className="w-3 h-3 text-slate-400" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[12px] font-semibold text-slate-300 truncate">{item.title}</p>
                      <p className="text-[11px] text-slate-500">{formatEventTimeLabel(item.start_time)}</p>
                    </div>
                    <span className="text-[10px] text-slate-600 shrink-0">{formatRelativeTime(item.start_time)}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
