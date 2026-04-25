"use client";

import { type ElementType, useMemo } from "react";
import { useQuery } from "@/hooks/useQuery";
import { motion, AnimatePresence } from "framer-motion";
import {
  TrendingUp, Calendar, Clock, Activity,
  ArrowUpRight, RefreshCw, Sparkles,
  ChevronRight, ArrowUp, ArrowDown,
  MousePointer2, Zap, Brain, Target
} from "lucide-react";
import { MeetingsLine, MeetingsBar } from "@/components/Analytics/Charts";
import { SkeletonText } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

// --- Animation Variants ---
const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1
    }
  }
};

const item = {
  hidden: { opacity: 0, y: 15, scale: 0.98 },
  show: { 
    opacity: 1, 
    y: 0, 
    scale: 1,
    transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } 
  }
};

const shimmer = {
  initial: { x: "-100%" },
  animate: { 
    x: "100%",
    transition: { 
      repeat: Infinity, 
      duration: 2, 
      ease: "linear" 
    } 
  }
};

// --- Main Page Component ---
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

  const { data: realtime } = useQuery<{
    series?: { bucket: string; meetings: number; hours?: number }[];
  }>("/api/analytics/realtime?range=30d", { revalidateInterval: 60_000 });

  const meetingsData = useMemo(() => {
    return realtime?.series
      ? realtime.series.map((s) => ({ day: s.bucket, count: s.meetings }))
      : data?.details?.weeklyBreakdown ?? [];
  }, [realtime, data]);

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-[#f8f9fa] selection:bg-[#d2e3fc] selection:text-[#1a73e8]">
        <div className="max-w-[1600px] mx-auto p-4 md:p-8 lg:p-12 space-y-10">
          
          {/* --- Premium Header --- */}
          <header className="flex flex-col md:flex-row md:items-center justify-between gap-8">
            <div className="space-y-2">
              <div className="flex items-center gap-2 mb-2">
                <span className="px-3 py-1 rounded-full bg-[#1a73e8]/10 text-[#1a73e8] text-xs font-bold tracking-wider uppercase">
                  Workspace Intelligence
                </span>
              </div>
              <h1 className="text-5xl font-bold tracking-tight text-[#202124] lg:text-6xl">
                Analytics <span className="text-[#1a73e8]">Studio</span>
              </h1>
              <p className="text-xl text-[#5f6368] max-w-2xl font-medium">
                High-fidelity performance metrics and AI-driven growth insights for your scheduling ecosystem.
              </p>
            </div>

            <div className="flex items-center gap-4">
              <motion.button 
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="group flex items-center gap-2 px-6 py-3 rounded-2xl bg-white border border-[#dadce0] text-[#3c4043] font-semibold hover:border-[#1a73e8] hover:text-[#1a73e8] transition-all shadow-sm active:shadow-none"
                onClick={() => refetch()}
              >
                <RefreshCw className={`w-5 h-5 transition-transform duration-500 ${isLoading ? 'animate-spin' : 'group-hover:rotate-180'}`} />
                <span>Sync Data</span>
              </motion.button>
              
              <motion.button 
                whileHover={{ scale: 1.02, y: -2 }}
                whileTap={{ scale: 0.98 }}
                className="flex items-center gap-3 px-8 py-3 rounded-2xl bg-[#202124] text-white font-semibold hover:bg-black transition-all shadow-xl shadow-[#202124]/10"
              >
                <span>Export Reports</span>
                <ArrowUpRight className="w-5 h-5" />
              </motion.button>
            </div>
          </header>

          <AnimatePresence>
            {error && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="flex items-center gap-4 rounded-3xl bg-[#fce8e6] border border-[#f5c2c7] p-6 text-[#c5221f]"
              >
                <div className="p-3 rounded-2xl bg-white/50">
                  <Activity className="w-6 h-6" />
                </div>
                <div>
                  <p className="font-bold text-lg">Communication Breakdown</p>
                  <p className="text-[#d93025] opacity-80 font-medium">{error.message}</p>
                </div>
                <button 
                  className="ml-auto px-6 py-2 rounded-xl bg-white text-[#c5221f] font-bold shadow-sm hover:bg-[#f8f9fa] transition-colors" 
                  onClick={() => refetch()}
                >
                  Re-establish Link
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* --- 12-Column Bento Grid --- */}
          <motion.div 
            variants={container} 
            initial="hidden" 
            animate="show" 
            className="grid grid-cols-1 md:grid-cols-12 gap-6 lg:gap-8"
          >
            {/* 1. Primary AI Intelligence Card (span-8) */}
            <motion.div variants={item} className="md:col-span-8 group relative">
              <div className="absolute inset-0 bg-gradient-to-br from-[#1a73e8]/5 to-transparent rounded-[2.5rem] opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
              <div className="h-full rounded-[2.5rem] bg-white border border-[#dadce0] p-10 shadow-[0_8px_30px_rgb(0,0,0,0.02)] hover:shadow-[0_20px_50px_rgba(26,115,232,0.08)] transition-all duration-500 relative overflow-hidden flex flex-col backdrop-blur-xl">
                
                {/* Background Shimmer Effect */}
                <div className="absolute top-0 right-0 p-12 pointer-events-none opacity-[0.03] group-hover:opacity-[0.07] transition-opacity duration-700">
                  <Brain className="w-64 h-64 text-[#1a73e8]" />
                </div>

                <div className="relative z-10 flex flex-col h-full space-y-8">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="p-4 rounded-2xl bg-[#e8f0fe] text-[#1a73e8] shadow-inner">
                        <Sparkles className="w-7 h-7" />
                      </div>
                      <div>
                        <h2 className="text-3xl font-bold text-[#202124]">GraftAI <span className="text-[#1a73e8]">Insight</span></h2>
                        <p className="text-[#5f6368] font-medium">Neural synthesis of workspace behavior</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 px-4 py-2 rounded-2xl bg-[#e6f4ea] border border-[#ceead6]">
                      <div className="relative flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#1e8e3e] opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-[#1e8e3e]"></span>
                      </div>
                      <span className="text-[#137333] text-sm font-bold tracking-widest uppercase">Live Synthesis</span>
                    </div>
                  </div>

                  <div className="flex-1">
                    {isLoading ? (
                      <div className="space-y-4">
                        <div className="h-6 w-3/4 bg-[#f1f3f4] animate-pulse rounded-lg" />
                        <div className="h-6 w-full bg-[#f1f3f4] animate-pulse rounded-lg" />
                        <div className="h-6 w-5/6 bg-[#f1f3f4] animate-pulse rounded-lg" />
                      </div>
                    ) : data?.summary ? (
                      <div className="relative">
                        <p className="text-2xl leading-relaxed text-[#3c4043] font-medium font-serif italic opacity-90 group-hover:opacity-100 transition-opacity">
                          "{data.summary}"
                        </p>
                        <div className="mt-8 flex flex-wrap gap-3">
                          {["Productivity Peak", "Low Attrition", "Optimal Focus"].map(tag => (
                            <span key={tag} className="px-4 py-1.5 rounded-full bg-[#f8f9fa] border border-[#dadce0] text-[#5f6368] text-xs font-bold tracking-tight">
                              #{tag.replace(/\s/g, "")}
                            </span>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="flex-1 flex items-center justify-center py-12">
                        <EmptyState
                          icon={Sparkles}
                          title="Analyzing Environment"
                          description="Our neural engines are processing your workspace data. Insights will arrive shortly."
                        />
                      </div>
                    )}
                  </div>

                  <div className="pt-6 mt-auto border-t border-[#f1f3f4] flex items-center justify-between">
                    <button className="flex items-center gap-2 text-[#1a73e8] font-bold text-lg hover:gap-4 transition-all">
                      Explore Neural Breakdown <ChevronRight className="w-5 h-5" />
                    </button>
                    <div className="flex -space-x-3 overflow-hidden">
                      {[1, 2, 3].map(i => (
                        <div key={i} className="inline-block h-10 w-10 rounded-full ring-4 ring-white bg-[#e8f0fe] border border-[#dadce0] flex items-center justify-center">
                          <Activity className="w-4 h-4 text-[#1a73e8]" />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* 2. Total Meetings Metric Card (span-4) */}
            <motion.div variants={item} className="md:col-span-4">
              <PremiumMetricCard
                icon={Calendar}
                label="Total Engagement"
                value={data?.details?.meetings ?? 0}
                trend={data?.details?.meetingsTrend ?? "+12.5% increase"}
                trendUp={true}
                color="#1a73e8"
                gradient="from-[#e8f0fe] to-white"
                loading={isLoading}
              />
            </motion.div>

            {/* 3. Efficiency Score Metric Card (span-4) */}
            <motion.div variants={item} className="md:col-span-4">
              <PremiumMetricCard
                icon={Target}
                label="Strategic Velocity"
                value={data?.details?.growth ?? 0}
                suffix="%"
                trend={data?.details?.growthTrend ?? "+5.2% focus time"}
                trendUp={true}
                color="#1e8e3e"
                gradient="from-[#e6f4ea] to-white"
                loading={isLoading}
              />
            </motion.div>

            {/* 4. Scheduling Velocity Chart (span-8) */}
            <motion.div variants={item} className="md:col-span-8">
              <div className="h-full rounded-[2.5rem] bg-white border border-[#dadce0] p-10 shadow-[0_8px_30px_rgb(0,0,0,0.02)] hover:shadow-md transition-all duration-500 overflow-hidden">
                <div className="flex items-center justify-between mb-10">
                  <div className="space-y-1">
                    <h2 className="text-2xl font-bold text-[#202124]">Velocity Dynamics</h2>
                    <p className="text-[#5f6368] font-medium">Volumetric throughput over 30 days</p>
                  </div>
                  <div className="flex bg-[#f1f3f4] p-1.5 rounded-2xl">
                    <button className="px-5 py-2 rounded-xl bg-white text-[#202124] text-sm font-bold shadow-sm">Volumetric</button>
                    <button className="px-5 py-2 rounded-xl text-[#5f6368] text-sm font-bold hover:bg-white/50 transition-colors">Efficiency</button>
                  </div>
                </div>
                <div className="h-[320px] w-full">
                  <MeetingsLine data={meetingsData} />
                </div>
              </div>
            </motion.div>

            {/* 5. Active Time Card (span-4) */}
            <motion.div variants={item} className="md:col-span-4">
              <PremiumMetricCard
                icon={Clock}
                label="Automation Offset"
                value={data?.details?.hours ?? 0}
                suffix="h"
                trend={data?.details?.hoursTrend ?? "-2h manual toil"}
                trendUp={true}
                color="#d93025"
                gradient="from-[#fce8e6] to-white"
                loading={isLoading}
              />
            </motion.div>

            {/* 6. Categories & Distribution (span-8) */}
            <motion.div variants={item} className="md:col-span-8">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 h-full">
                
                {/* Daily Distribution */}
                <div className="rounded-[2.5rem] bg-[#202124] p-10 text-white shadow-xl shadow-[#202124]/10 relative overflow-hidden group">
                  <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
                  <div className="relative z-10 h-full flex flex-col">
                    <div className="flex items-center justify-between mb-8">
                      <h3 className="text-xl font-bold tracking-tight">Temporal Peak</h3>
                      <Activity className="w-5 h-5 text-[#1a73e8]" />
                    </div>
                    <div className="flex-1 min-h-[220px]">
                      <MeetingsBar data={meetingsData} />
                    </div>
                    <p className="mt-6 text-sm text-white/60 font-medium leading-relaxed">
                      Peak activity detected during <span className="text-white font-bold">10:00 AM - 2:00 PM</span> local time.
                    </p>
                  </div>
                </div>

                {/* Categories */}
                <div className="rounded-[2.5rem] bg-white border border-[#dadce0] p-10 shadow-[0_8px_30px_rgb(0,0,0,0.02)]">
                  <h3 className="text-xl font-bold text-[#202124] mb-8">Categorical Flow</h3>
                  <div className="space-y-6">
                    {isLoading ? (
                      <SkeletonText lines={4} />
                    ) : data?.details?.categoryBreakdown ? (
                      data.details.categoryBreakdown.slice(0, 4).map(({ category, count }, i) => {
                        const max = Math.max(...data.details!.categoryBreakdown!.map(c => c.count), 1);
                        const pct = Math.round((count / max) * 100);
                        const colors = ["#1a73e8", "#34a853", "#fbbc04", "#ea4335"];
                        return (
                          <div key={category} className="space-y-2">
                            <div className="flex justify-between items-end">
                              <span className="text-sm font-bold text-[#3c4043] capitalize flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: colors[i % colors.length] }} />
                                {category}
                              </span>
                              <span className="text-xs font-black text-[#5f6368]">{count} units</span>
                            </div>
                            <div className="h-2.5 rounded-full bg-[#f1f3f4] overflow-hidden">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${pct}%` }}
                                transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1], delay: 0.3 + i * 0.1 }}
                                className="h-full rounded-full"
                                style={{ backgroundColor: colors[i % colors.length] }}
                              />
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="h-full flex items-center justify-center text-[#5f6368] text-sm font-medium">
                        Collecting categorical context...
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>

          </motion.div>

          {/* --- Optimization Banner --- */}
          <motion.div
            variants={item}
            initial="hidden"
            animate="show"
            className="group relative"
          >
            <div className="absolute -inset-0.5 bg-gradient-to-r from-[#1a73e8] via-[#34a853] to-[#fbbc04] rounded-[2.5rem] blur opacity-20 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
            <div className="relative flex flex-col md:flex-row items-center gap-8 p-10 rounded-[2.5rem] bg-white border border-[#dadce0] overflow-hidden">
              <div className="p-6 rounded-[2rem] bg-[#1a73e8]/10 text-[#1a73e8] relative overflow-hidden">
                <Zap className="w-10 h-10 relative z-10" />
                <motion.div 
                  variants={shimmer}
                  initial="initial"
                  animate="animate"
                  className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-transparent via-white/40 to-transparent"
                />
              </div>
              <div className="flex-1 text-center md:text-left">
                <h4 className="text-2xl font-bold text-[#202124] mb-1">Growth Catalyst Detected</h4>
                <p className="text-lg text-[#5f6368] font-medium leading-relaxed">
                  Workspace configurations with <span className="text-[#1a73e8] font-bold italic">3+ Neural Agents</span> exhibit 
                  a <span className="px-2 py-0.5 rounded bg-[#e6f4ea] text-[#137333] font-bold">42% reduction</span> in scheduling latency.
                </p>
              </div>
              <motion.button 
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-10 py-4 rounded-2xl bg-[#1a73e8] text-white font-black shadow-lg shadow-[#1a73e8]/20 hover:bg-[#174ea6] transition-all"
              >
                Optimize Now
              </motion.button>
            </div>
          </motion.div>
        </div>
      </div>
    </ErrorBoundary>
  );
}

// --- Sub-components ---

function PremiumMetricCard({
  icon: Icon, label, value, suffix = "", trend, trendUp, color, gradient, loading
}: {
  icon: ElementType;
  label: string;
  value: number;
  suffix?: string;
  trend: string;
  trendUp: boolean;
  color: string;
  gradient: string;
  loading: boolean;
}) {
  return (
    <div className="h-full rounded-[2.5rem] bg-white border border-[#dadce0] p-10 shadow-[0_8px_30px_rgb(0,0,0,0.02)] hover:shadow-xl transition-all duration-500 flex flex-col justify-between group relative overflow-hidden">
      {/* Background soft gradient blob */}
      <div className="absolute -top-12 -right-12 w-32 h-32 bg-current opacity-[0.03] blur-3xl rounded-full" style={{ color }} />
      
      <div className="flex justify-between items-start mb-10 relative z-10">
        <div 
          className={`p-5 rounded-[1.5rem] bg-gradient-to-br ${gradient} shadow-inner group-hover:scale-110 group-hover:-rotate-3 transition-transform duration-500`} 
        >
          <Icon className="w-8 h-8" style={{ color }} />
        </div>
        <button className="p-3 rounded-full hover:bg-[#f8f9fa] text-[#dadce0] hover:text-[#5f6368] transition-colors">
          <MousePointer2 className="w-5 h-5" />
        </button>
      </div>
      
      <div className="space-y-3 relative z-10">
        <p className="text-[#5f6368] font-bold text-sm tracking-[0.1em] uppercase">{label}</p>
        {loading ? (
          <div className="h-16 w-32 bg-[#f1f3f4] animate-pulse rounded-2xl" />
        ) : (
          <div className="flex items-baseline gap-2">
            <span className="text-6xl font-black text-[#202124] tracking-tighter">{value}</span>
            <span className="text-3xl font-bold text-[#5f6368] opacity-50">{suffix}</span>
          </div>
        )}
      </div>

      <div className="mt-10 pt-8 border-t border-[#f1f3f4] relative z-10">
        <div className={`flex items-center gap-2 text-sm font-black ${trendUp ? 'text-[#1e8e3e]' : 'text-[#d93025]'}`}>
          <div className={`p-1 rounded-lg ${trendUp ? 'bg-[#e6f4ea]' : 'bg-[#fce8e6]'}`}>
            {trendUp ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />}
          </div>
          <span className="tracking-tight">{trend}</span>
        </div>
      </div>
    </div>
  );
}
