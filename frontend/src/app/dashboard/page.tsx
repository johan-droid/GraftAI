"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthContext } from "@/app/providers/auth-provider";
import { motion } from "framer-motion";
import {
  Calendar,
  Copy,
  Check,
  ArrowUpRight,
  Clock,
  Video,
  MapPin,
  Users,
  Sparkles,
  TrendingUp,
  MoreHorizontal,
  ExternalLink,
  ChevronRight,
  Zap,
  Globe,
  Activity,
} from "lucide-react";
import { getAnalyticsSummary, getProactiveSuggestion } from "@/lib/api";

const STAGGER = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.07 } },
};
const ITEM = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
};

const MOCK_UPCOMING = [
  {
    id: 1,
    title: "Product sync with Alice",
    time: "Today, 2:00 PM",
    duration: "30 min",
    type: "video",
    attendees: 3,
    color: "indigo",
  },
  {
    id: 2,
    title: "Investor call – Series A",
    time: "Today, 4:30 PM",
    duration: "60 min",
    type: "video",
    attendees: 5,
    color: "violet",
  },
  {
    id: 3,
    title: "Design review",
    time: "Tomorrow, 10:00 AM",
    duration: "45 min",
    type: "in-person",
    attendees: 4,
    color: "cyan",
  },
  {
    id: 4,
    title: "Weekly team standup",
    time: "Tomorrow, 12:00 PM",
    duration: "15 min",
    type: "video",
    attendees: 8,
    color: "emerald",
  },
];

const QUICK_LINKS = [
  { label: "30 Min Meeting", slug: "30min", icon: Clock, color: "from-indigo-500 to-violet-500" },
  { label: "60 Min Call", slug: "60min", icon: Video, color: "from-violet-500 to-fuchsia-500" },
  { label: "Team Sync", slug: "team-sync", icon: Users, color: "from-cyan-500 to-blue-500" },
];

const COLOR_MAP: Record<string, string> = {
  indigo: "bg-indigo-500/10 border-indigo-500/20 text-indigo-300",
  violet: "bg-violet-500/10 border-violet-500/20 text-violet-300",
  cyan: "bg-cyan-500/10 border-cyan-500/20 text-cyan-300",
  emerald: "bg-emerald-500/10 border-emerald-500/20 text-emerald-300",
};

const STAT_COLOR_CLASSES: Record<string, string> = {
  indigo: "bg-indigo-500/10 border-indigo-500/20 text-indigo-300",
  violet: "bg-violet-500/10 border-violet-500/20 text-violet-300",
  emerald: "bg-emerald-500/10 border-emerald-500/20 text-emerald-300",
  cyan: "bg-cyan-500/10 border-cyan-500/20 text-cyan-300",
};

export default function Dashboard() {
  const router = useRouter();
  const { user, isAuthenticated, loading } = useAuthContext();
  const typedUser = user as { name?: string; email?: string } | null;
  const profileName = typedUser?.name?.split(" ")[0] ?? typedUser?.email?.split("@")[0] ?? "there";
  const bookingSlug = typedUser?.email?.split("@")[0] ?? "you";

  const [stats, setStats] = useState({ meetings: 24, hours: 18.5, growth: 14.2 });
  const [aiSuggestion, setAiSuggestion] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!loading && !isAuthenticated) router.replace("/login");
  }, [loading, isAuthenticated, router]);

  useEffect(() => {
    if (!isAuthenticated) return;
    getAnalyticsSummary()
      .then((d) => {
        if (d.details?.meetings) setStats(d.details as typeof stats);
      })
      .catch(() => {});
    getProactiveSuggestion("dashboard overview")
      .then((d) => setAiSuggestion(d.suggestion))
      .catch(() => {});
  }, [isAuthenticated]);

  const copyBookingLink = async () => {
    await navigator.clipboard.writeText(`https://graftai.app/${bookingSlug}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

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

        {/* Header */}
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

        {/* Booking Link Card */}
        <motion.div variants={ITEM} className="relative overflow-hidden rounded-2xl border border-indigo-500/20 bg-gradient-to-r from-indigo-600/10 via-violet-600/5 to-transparent p-5">
          <div className="absolute right-0 top-0 w-64 h-full bg-gradient-to-l from-indigo-500/5 to-transparent pointer-events-none" />
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center">
                <Zap className="w-5 h-5 text-indigo-300" />
              </div>
              <div>
                <p className="text-xs font-semibold text-indigo-300 mb-0.5">Your booking page</p>
                <p className="text-white font-mono text-sm font-medium">graftai.app/{bookingSlug}</p>
              </div>
            </div>
            <div className="sm:ml-auto flex items-center gap-2">
              <button
                onClick={copyBookingLink}
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/8 border border-white/10 text-slate-300 hover:text-white hover:bg-white/12 text-[13px] font-medium transition-all"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? "Copied!" : "Copy link"}
              </button>
              <a
                href={`https://graftai.app/${bookingSlug}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-600/30 text-[13px] font-medium transition-all"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                View page
              </a>
            </div>
          </div>
        </motion.div>

        {/* Stats Row */}
        <motion.div variants={ITEM} className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Meetings this month", value: stats.meetings, sub: "+3 vs last month", icon: Calendar, color: "indigo" },
            { label: "Hours scheduled", value: `${stats.hours}h`, sub: `+${stats.growth}% growth`, icon: Clock, color: "violet" },
            { label: "Avg. response time", value: "< 2m", sub: "Great performance", icon: Zap, color: "emerald" },
            { label: "Booking rate", value: "87%", sub: "Last 30 days", icon: TrendingUp, color: "cyan" },
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
          {/* Upcoming meetings */}
          <motion.div variants={ITEM}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-white">Upcoming meetings</h2>
              <Link href="/dashboard/calendar" className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1">
                View calendar <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
            <div className="space-y-2">
              {MOCK_UPCOMING.map((meeting, i) => (
                <motion.div
                  key={meeting.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.06, duration: 0.3 }}
                  className="group flex items-center gap-4 p-4 rounded-xl border border-white/[0.06] bg-white/[0.025] hover:bg-white/[0.05] hover:border-white/10 transition-all cursor-pointer"
                >
                  <div className={`w-1 h-10 rounded-full shrink-0 ${COLOR_MAP[meeting.color].split(" ")[0]}`} />
                  <div className="min-w-0 flex-1">
                    <p className="text-[14px] font-semibold text-white truncate">{meeting.title}</p>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="flex items-center gap-1 text-[12px] text-slate-400">
                        <Clock className="w-3 h-3" /> {meeting.time}
                      </span>
                      <span className={`text-[11px] px-1.5 py-0.5 rounded-md border font-medium ${COLOR_MAP[meeting.color]}`}>
                        {meeting.duration}
                      </span>
                    </div>
                  </div>

                  <div className="hidden sm:flex items-center gap-2 shrink-0">
                    <div className="flex items-center gap-1 text-[12px] text-slate-500">
                      <Users className="w-3 h-3" />
                      <span>{meeting.attendees}</span>
                    </div>
                    {meeting.type === "video" ? (
                      <Video className="w-3.5 h-3.5 text-slate-500" />
                    ) : (
                      <MapPin className="w-3.5 h-3.5 text-slate-500" />
                    )}
                  </div>

                  <button className="p-1.5 rounded-md text-slate-600 hover:text-slate-300 hover:bg-white/8 transition-all opacity-0 group-hover:opacity-100" aria-label="More options">
                    <MoreHorizontal className="w-4 h-4" />
                  </button>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Right column */}
          <div className="space-y-5">
            {/* Quick links */}
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
                      <p className="text-[11px] text-slate-500 font-mono">/{bookingSlug}/{ql.slug}</p>
                    </div>
                    <button className="p-1.5 rounded-md text-slate-600 hover:text-slate-300 transition-all opacity-0 group-hover:opacity-100" aria-label="Open event type">
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

            {/* AI Suggestion */}
            {aiSuggestion && (
              <motion.div variants={ITEM} className="p-4 rounded-xl border border-violet-500/20 bg-violet-500/5">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-3.5 h-3.5 text-violet-400" />
                  <span className="text-[11px] font-bold text-violet-300 uppercase tracking-wide">AI Insight</span>
                </div>
                <p className="text-[13px] text-slate-300 leading-relaxed">{aiSuggestion}</p>
              </motion.div>
            )}

            {/* Activity feed */}
            <motion.div variants={ITEM}>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-base font-bold text-white">Activity</h2>
                <Link href="/dashboard/analytics" className="text-xs text-indigo-400 hover:text-indigo-300">
                  Analytics →
                </Link>
              </div>
              <div className="space-y-3">
                {[
                  { action: "New booking", detail: "Alice booked a 30-min call", time: "2 min ago", icon: Calendar },
                  { action: "Rescheduled", detail: "Bob moved his meeting", time: "1h ago", icon: Clock },
                  { action: "Cancelled", detail: "Team sync was cancelled", time: "3h ago", icon: Activity },
                  { action: "New signup", detail: "Carol joined via your link", time: "5h ago", icon: Globe },
                ].map((item, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-white/5 border border-white/8 flex items-center justify-center shrink-0 mt-0.5">
                      <item.icon className="w-3 h-3 text-slate-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[12px] font-semibold text-slate-300">{item.action}</p>
                      <p className="text-[11px] text-slate-500">{item.detail}</p>
                    </div>
                    <span className="text-[10px] text-slate-600 shrink-0">{item.time}</span>
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
