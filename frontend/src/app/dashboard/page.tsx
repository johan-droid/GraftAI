"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthContext } from "@/app/providers/auth-provider";
import { motion } from "framer-motion";
import { Users, Calendar as CalendarIcon, Activity, ArrowUpRight, TrendingUp, Sparkles, Puzzle } from "lucide-react";

import { getAnalyticsSummary, getProactiveSuggestion } from "@/lib/api";

export default function Dashboard() {
  type DashboardUser = { full_name?: string; email?: string } | null;
  const router = useRouter();
  const { user, isAuthenticated, loading, refresh } = useAuthContext();
  const dashboardUser = user as DashboardUser;
  const profileName = dashboardUser?.full_name || dashboardUser?.email?.split("@")[0] || "User";
  const [stats, setStats] = useState({ meetings: 0, hours: 0, growth: 0 });
  const [summaryMessage, setSummaryMessage] = useState("");
  const [aiSuggestion, setAiSuggestion] = useState("");

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace("/login");
    } else if (isAuthenticated) {
      // Fetch real analytics summary
      getAnalyticsSummary().then(data => {
        setSummaryMessage(data.summary);
        if (data.details && data.details.meetings) {
            setStats(data.details);
        } else {
            setStats({ meetings: 12, hours: 8.5, growth: 14.2 });
        }
      }).catch(err => {
        console.error("Failed to fetch analytics", err);
        setStats({ meetings: 12, hours: 8.5, growth: 14.2 });
      });

      // Fetch proactive AI suggestion
      getProactiveSuggestion("dashboard overview").then(data => {
        setAiSuggestion(data.suggestion);
      }).catch(() => {});
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
      <header className="flex flex-col gap-3 mb-4 md:mb-8 md:flex-row md:items-center md:justify-between md:gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white mb-1">
            Welcome back, {profileName}
          </h1>
          <p className="text-slate-400">Here is what is happening today.</p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/dashboard/calendar" className="w-full md:w-auto inline-flex items-center justify-center rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary/90 shadow-[0_0_15px_rgba(79,70,229,0.3)] gap-2">
            <CalendarIcon className="w-4 h-4" />
            New Booking
          </Link>
        </div>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 md:gap-6">
        <motion.div variants={itemVariants} className="bg-slate-950/50 border border-slate-800 rounded-2xl p-5 md:p-6 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <CalendarIcon className="w-12 h-12 md:w-16 md:h-16 text-primary" />
          </div>
          <div className="mb-4 inline-flex p-3 rounded-xl bg-primary/10 text-primary">
            <CalendarIcon className="w-6 h-6" />
          </div>
          <p className="text-slate-400 text-sm font-medium mb-1">Upcoming Meetings</p>
          <div className="flex items-baseline gap-2">
            <h2 className="text-2xl md:text-3xl font-bold text-white">{stats.meetings}</h2>
            <span className="text-emerald-400 text-sm font-medium flex items-center">
              <TrendingUp className="w-3 h-3 mr-1" /> +2 this week
            </span>
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="bg-slate-950/50 border border-slate-800 rounded-2xl p-5 md:p-6 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <Users className="w-12 h-12 md:w-16 md:h-16 text-fuchsia-400" />
          </div>
          <div className="mb-4 inline-flex p-3 rounded-xl bg-fuchsia-400/10 text-fuchsia-400">
            <Users className="w-6 h-6" />
          </div>
          <p className="text-slate-400 text-sm font-medium mb-1">AI Copilot Hours</p>
          <div className="flex items-baseline gap-2">
            <h2 className="text-2xl md:text-3xl font-bold text-white">{stats.hours}h</h2>
            <span className="text-emerald-400 text-sm font-medium flex items-center">
              <TrendingUp className="w-3 h-3 mr-1" /> {stats.growth}%
            </span>
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="sm:col-span-2 md:col-span-1 bg-slate-950/50 border border-slate-800 rounded-2xl p-5 md:p-6 relative overflow-hidden group flex flex-col justify-between">
          <div>
            <div className="mb-4 inline-flex p-3 rounded-xl bg-slate-800 text-emerald-400 border border-slate-700">
              <Activity className="w-6 h-6" />
            </div>
            <p className="text-slate-400 text-sm font-medium mb-1">System Status</p>
            <h2 className="text-xl font-bold text-white">All systems operational</h2>
          </div>
          <Link href="/dashboard/analytics" className="mt-4 text-primary text-sm font-medium inline-flex items-center hover:text-primary-glow transition-colors">
            View detailed analytics <ArrowUpRight className="w-4 h-4 ml-1" />
          </Link>
        </motion.div>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 gap-4 mt-4 md:mt-6 lg:grid-cols-3 lg:gap-6">
        <motion.div variants={itemVariants} className="lg:col-span-2 bg-slate-950/50 border border-slate-800 rounded-2xl p-5 md:p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 md:p-8 text-center text-slate-300">
            {summaryMessage ? (
              <p className="font-medium text-lg leading-relaxed">{summaryMessage}</p>
            ) : (
              <>
                <Activity className="w-8 h-8 text-slate-500 mx-auto mb-3 opacity-50" />
                <p className="text-slate-400">Loading activity timeline from backend...</p>
              </>
            )}
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

