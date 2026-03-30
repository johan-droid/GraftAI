"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthContext } from "@/app/providers/auth-provider";
import { motion } from "framer-motion";
import { Users, Calendar as CalendarIcon, Activity, ArrowUpRight, TrendingUp, Sparkles, Puzzle } from "lucide-react";

import { getAnalyticsSummary, getProactiveSuggestion, syncUserTimezone } from "@/lib/api";

function getLocalizedGreeting(name: string) {
  const hour = new Date().getHours();
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const city = tz.split("/").pop()?.replace(/_/g, " ") || "Earth";
  
  let greeting = "Good morning";
  if (hour >= 12 && hour < 17) greeting = "Good afternoon";
  else if (hour >= 17 && hour < 21) greeting = "Good evening";
  else if (hour < 5 || hour >= 21) greeting = "Good night";

  return `${greeting} from ${city}, ${name}`;
}

export default function Dashboard() {
  type DashboardUser = { full_name?: string; email?: string } | null;
  const router = useRouter();
  const { user, isAuthenticated, loading, refresh } = useAuthContext();
  const dashboardUser = user as DashboardUser;
  const profileName = dashboardUser?.full_name || dashboardUser?.email?.split("@")[0] || "User";
  const [stats, setStats] = useState<{ meetings: number; hours: number; growth: number; next_event?: any; recent_events?: any[] }>({ meetings: 0, hours: 0, growth: 0 });
  const [summaryMessage, setSummaryMessage] = useState("");
  const [aiSuggestion, setAiSuggestion] = useState("");

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace("/login");
    } else if (isAuthenticated) {
      // Fetch real analytics summary
      getAnalyticsSummary().then(data => {
        setSummaryMessage(data.summary);
        if (data.details) {
            setStats(data.details);
        }
      }).catch(err => {
        console.error("Failed to fetch analytics", err);
        setSummaryMessage("We're having trouble reaching the analytics engine right now. Please try again later.");
      });

      // Fetch proactive AI suggestion
      getProactiveSuggestion("dashboard overview").then(data => {
        setAiSuggestion(data.suggestion);
      }).catch(() => {});

      // Sync timezone to backend
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      syncUserTimezone(tz).catch(() => {});
    }
  }, [isAuthenticated, loading, router]);

  useEffect(() => {
    if (!isAuthenticated) return;
    const intervalId = setInterval(() => {
      refresh();
    }, 45 * 1000);
    return () => clearInterval(intervalId);
  }, [isAuthenticated, refresh]);

  if (loading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
      </div>
    );
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <motion.div 
      variants={containerVariants} 
      initial="hidden" 
      animate="visible"
      className="space-y-4 md:space-y-6"
    >
      <header className="flex flex-col gap-4 mb-2 md:mb-8 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-xl md:text-3xl font-black tracking-tight text-white mb-1.5 bg-gradient-to-r from-white via-white to-primary/50 bg-clip-text leading-tight">
            {getLocalizedGreeting(profileName)}
          </h1>
          <p className="text-xs md:text-sm text-slate-400 font-medium opacity-80">Dashboard / Situational Overview</p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/dashboard/calendar" className="flex-1 md:flex-none inline-flex items-center justify-center rounded-xl bg-primary px-4 py-2 text-xs md:text-sm font-bold text-white transition-all hover:bg-primary/90 shadow-[0_0_15px_rgba(79,70,229,0.3)] gap-2 active:scale-95">
            <CalendarIcon className="w-3.5 h-3.5" />
            New Booking
          </Link>
        </div>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 md:gap-6">
        <motion.div variants={itemVariants} className="bg-slate-950/40 backdrop-blur-xl border border-slate-800/60 rounded-2xl p-4 md:p-6 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-5">
            <CalendarIcon className="w-12 h-12 md:w-16 md:h-16 text-primary" />
          </div>
          <p className="text-slate-500 text-[10px] uppercase tracking-widest font-bold mb-1">Upcoming</p>
          <p className="text-slate-300 text-xs font-medium mb-3">AI Organized Sessions</p>
          <div className="flex items-baseline gap-2">
            <h2 className="text-2xl font-black text-white">{stats.meetings}</h2>
            <span className="text-emerald-400 text-[10px] font-bold flex items-center bg-emerald-500/10 px-1.5 py-0.5 rounded-md border border-emerald-500/20">
              <TrendingUp className="w-2.5 h-2.5 mr-1" /> +2
            </span>
          </div>
          {stats.next_event && (
            <div className="mt-4 p-2.5 rounded-xl bg-primary/5 border border-primary/10">
              <p className="text-[9px] text-primary uppercase font-black tracking-tighter mb-1">Coming Up Next</p>
              <p className="text-xs font-bold text-white truncate">{stats.next_event.title}</p>
            </div>
          )}
        </motion.div>

        <motion.div variants={itemVariants} className="bg-slate-950/40 backdrop-blur-xl border border-slate-800/60 rounded-2xl p-4 md:p-6 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-5">
            <Users className="w-12 h-12 md:w-16 md:h-16 text-fuchsia-400" />
          </div>
          <p className="text-slate-500 text-[10px] uppercase tracking-widest font-bold mb-1">Productivity</p>
          <p className="text-slate-300 text-xs font-medium mb-3">Time Saved by Copilot</p>
          <div className="flex items-baseline gap-2">
            <h2 className="text-2xl font-black text-white">{stats.hours}h</h2>
            <span className="text-emerald-400 text-[10px] font-bold flex items-center bg-emerald-500/10 px-1.5 py-0.5 rounded-md border border-emerald-500/20">
              <TrendingUp className="w-2.5 h-2.5 mr-1" /> {stats.growth > 0 ? `+${stats.growth}%` : "Stable"}
            </span>
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="bg-slate-950/40 backdrop-blur-xl border border-slate-800/60 rounded-2xl p-4 md:p-6 relative overflow-hidden group flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-slate-500 text-[10px] uppercase tracking-widest font-bold mb-1">Integrity</p>
              <h2 className="text-sm font-bold text-emerald-400 flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Operational
              </h2>
            </div>
            <Activity className="w-4 h-4 text-slate-600" />
          </div>
          <Link href="/dashboard/analytics" className="text-primary text-[10px] font-black uppercase tracking-tighter inline-flex items-center hover:text-primary-glow transition-all">
            Detailed Insights <ArrowUpRight className="w-3 h-3 ml-1" />
          </Link>
        </motion.div>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 gap-4 mt-4 md:mt-6 lg:grid-cols-3 lg:gap-6">
        <motion.div variants={itemVariants} className="lg:col-span-2 bg-slate-950/40 backdrop-blur-xl border border-slate-800/60 rounded-2xl overflow-hidden">
          <div className="p-4 md:p-6 border-b border-slate-800/60 flex items-center justify-between">
            <h3 className="text-sm font-bold text-white uppercase tracking-widest">Recent Activity</h3>
            <Sparkles className="w-4 h-4 text-primary animate-pulse" />
          </div>
          <div className="p-0">
            {summaryMessage && (
              <div className="m-4 p-3 rounded-xl border border-primary/20 bg-primary/5">
                <p className="text-[11px] text-slate-300 leading-relaxed font-medium">
                  {summaryMessage}
                </p>
              </div>
            )}
            
            <div className="glass-table-container">
              {stats.recent_events && stats.recent_events.length > 0 ? (
                <table className="glass-table">
                  <thead>
                    <tr>
                      <th>Title</th>
                      <th>Date & Time</th>
                      <th className="hidden sm:table-cell">Category</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.recent_events.map((event: any) => (
                      <tr key={event.id} className="group">
                        <td>
                          <div className="flex items-center gap-3">
                            <div className={`p-1.5 rounded-lg ${event.is_upcoming ? 'bg-primary/20 text-primary' : 'bg-slate-800 text-slate-500'}`}>
                              <CalendarIcon className="w-3.5 h-3.5" />
                            </div>
                            <div>
                                <p className="text-xs font-bold text-white truncate max-w-[120px] sm:max-w-none">{event.title}</p>
                                {event.is_upcoming && <span className="text-[8px] text-emerald-400 font-black uppercase tracking-tighter">Live</span>}
                            </div>
                          </div>
                        </td>
                        <td>
                          <p className="text-[10px] text-slate-300 font-medium">
                            {new Date(event.start_time).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                          </p>
                          <p className="text-[9px] text-slate-500">
                            {new Date(event.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </td>
                        <td className="hidden sm:table-cell">
                          <span className="text-[9px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700 font-bold uppercase tracking-widest">
                            {event.category}
                          </span>
                        </td>
                        <td className="text-right">
                          <ArrowUpRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-primary transition-colors inline" />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="p-8 text-center bg-slate-900/10">
                  <Activity className="w-6 h-6 text-slate-700 mx-auto mb-2 opacity-30" />
                  <p className="text-slate-600 text-[10px] font-bold uppercase">Chronicle Empty</p>
                </div>
              )}
            </div>
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="bg-slate-950/50 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Quick Links</h3>
          <div className="space-y-3">
            <Link href="/dashboard/plugins" className="flex items-center justify-between p-3 rounded-xl border border-slate-800 bg-slate-900/50 hover:bg-slate-800 transition-colors">
              <span className="text-sm font-medium text-slate-300 flex items-center gap-2"><Puzzle className="w-4 h-4 text-primary" /> Plugins</span>
              <ArrowUpRight className="w-4 h-4 text-slate-500" />
            </Link>
            <Link href="/dashboard/settings" className="flex items-center justify-between p-3 rounded-xl border border-slate-800 bg-slate-900/50 hover:bg-slate-800 transition-colors">
              <span className="text-sm font-medium text-slate-300">Settings & Privacy</span>
              <ArrowUpRight className="w-4 h-4 text-slate-500" />
            </Link>
          </div>

          {/* Connect Calendar Prompt */}
          <div className="mt-6 p-4 rounded-2xl border border-primary/20 bg-gradient-to-br from-primary/10 to-transparent relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-3 opacity-20 group-hover:scale-110 transition-transform">
              <CalendarIcon className="w-8 h-8 text-primary" />
            </div>
            <h4 className="text-sm font-bold text-white mb-1 flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-primary" />
              Sync your Calendar
            </h4>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              Connect your calendar to enable AI-powered scheduling and timezone sync.
            </p>
            <Link href="/dashboard/calendar" className="block w-full">
              <button className="w-full py-2.5 rounded-xl bg-primary text-white text-xs font-bold hover:bg-primary/90 transition-all shadow-lg active:scale-95">
                Connect Now
              </button>
            </Link>
          </div>

          {/* Proactive AI Suggestion */}
          {aiSuggestion && (
            <div className="mt-4 p-3 rounded-xl border border-primary/20 bg-primary/5">
              <p className="text-xs text-primary font-medium flex items-center gap-1 mb-1"><Sparkles className="w-3 h-3" /> AI Suggestion</p>
              <p className="text-sm text-slate-300">{aiSuggestion}</p>
            </div>
          )}
        </motion.div>
      </div>
    </motion.div>
  );
}

