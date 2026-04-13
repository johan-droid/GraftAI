"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Box, Container, Grid, Typography, Paper, Button, Chip, IconButton, Tooltip } from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import {
  Calendar,
  Clock,
  Activity,
  ArrowUpRight,
  Sparkles,
  Zap,
  Settings,
  Bot,
  Users,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Timer,
  Terminal,
} from "lucide-react";
import Link from "next/link";

import { useAuth } from "@/app/providers/auth-provider";
import { useQuery } from "@/hooks/useQuery";
import { useTheme } from "@/contexts/ThemeContext";
import { useDashboardMetrics } from "@/lib/ai-api";
import { MetricCard, MetricCardGrid } from "@/components/ui/MetricCard";
import { DataTable, StatusChip } from "@/components/ui/DataTable";

import { Greeting } from "@/components/dashboard/Greeting";
import { Header } from "@/components/dashboard/Header";
import { StatCard } from "@/components/dashboard/StatCard";
import { MobileSidebar } from "@/components/dashboard/MobileSidebar";
import { BottomNav } from "@/components/dashboard/BottomNav";
import { SkeletonCard, SkeletonText } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { GradientButton } from "@/components/ui/GradientButton";

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const { isDark } = useTheme();

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  // Fetch real analytics data from backend
  const { data: analytics, isLoading: analyticsLoading, error: analyticsError, refetch: refetchAnalytics } = useQuery<{
    summary: string;
    details?: { meetings: number; hours: number; growth: number; previousWeekMeetings: number; upcomingToday: number; suggestions: number };
  }>(isAuthenticated ? "/api/analytics/summary" : null);

  const { data: suggestion, isLoading: suggestionLoading } = useQuery<{
    suggestion: string;
  }>(isAuthenticated ? "/api/proactive" : null);

  const { data: upcomingEvents, isLoading: eventsLoading } = useQuery<{
    id: number; title: string; start_time: string; category: string;
  }[]>(isAuthenticated ? "/api/events/upcoming" : null);

  // AI Automation Metrics
  const { metrics, loading: metricsLoading, refetch: refetchMetrics } = useDashboardMetrics(30000);

  // Global auth errors are handled by AuthProvider. 
  // We only show an error state here instead of a hard redirect.


  // Use real analytics data only - no mock fallbacks
  const displayAnalytics = analytics;

  // AI suggestion - show empty if none available
  const displaySuggestion = suggestion;

  const displayEvents = upcomingEvents || [];

  // Show loading state
  if (authLoading || !isAuthenticated) {
    return (
      <Box
        sx={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "var(--bg-base)",
        }}
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          style={{
            width: 40,
            height: 40,
            borderRadius: "50%",
            border: "3px solid hsla(239, 84%, 67%, 0.2)",
            borderTopColor: "hsl(239, 84%, 67%)",
          }}
        />
      </Box>
    );
  }

  // Calculate stats
  const stats = analytics?.details ?? { meetings: null, hours: null, growth: null, previousWeekMeetings: null };
  const meetingsDelta = stats.meetings != null && stats.previousWeekMeetings != null
    ? stats.meetings - stats.previousWeekMeetings
    : null;

  // Animation variants
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } },
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background: "var(--bg-base)",
        pb: { xs: 10, md: 4 },
      }}
    >
      <MobileSidebar />

      <Container maxWidth="xl" sx={{ px: { xs: 2.5, md: 5 }, py: { xs: 3, md: 6 } }}>
        <motion.div variants={container} initial="hidden" animate="show">
          
          {/* Header & Greeting Layer */}
          <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-8 mb-12">
            <div className="flex-1">
              <motion.div variants={item}>
                <Greeting
                  userName={user?.name}
                  userEmail={user?.email}
                  isLoading={false}
                />
              </motion.div>
            </div>
            <div className="lg:w-auto w-full">
              <motion.div variants={item}>
                <Header
                  userName={user?.name}
                  userEmail={user?.email}
                  userAvatar={user?.avatar}
                  notificationCount={3}
                />
              </motion.div>
            </div>
          </div>

          {/* Primary Stats Matrix */}
          <motion.div variants={item} className="mb-12">
            <div className="flex items-center gap-3 mb-6">
               <Activity size={16} className="text-[var(--primary)]" />
               <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-[var(--text-muted)]">Core_Telemetry_Matrix</h2>
            </div>
            <Grid container spacing={3}>
              {analyticsLoading ? (
                Array(3).fill(0).map((_, i) => (
                  <Grid item xs={12} sm={6} md={4} key={i}>
                    <SkeletonCard />
                  </Grid>
                ))
              ) : (
                <>
                  <Grid item xs={12} sm={6} md={4}>
                    <StatCard
                      title="Total_Meetings"
                      value={stats.meetings ?? "—"}
                      icon={Calendar}
                      trend={meetingsDelta != null ? {
                        value: Math.round((meetingsDelta / (stats.previousWeekMeetings || 1)) * 100),
                        label: "L_WEEK_DELTA",
                      } : undefined}
                      color="primary"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <StatCard
                      title="Copilot_Optimization"
                      value={stats.hours ? `${stats.hours}H` : "—"}
                      icon={Bot}
                      trend={stats.growth != null ? {
                        value: stats.growth,
                        label: "EFFICIENCY_GAIN",
                      } : undefined}
                      color="warning"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <StatCard
                      title="Active_Node_Status"
                      value="STABLE"
                      icon={CheckCircle}
                      color="success"
                    />
                  </Grid>
                </>
              )}
            </Grid>
          </motion.div>

          {/* System Tiles Grid */}
          <Grid container spacing={3} sx={{ mb: 6 }}>
            {/* Left Column: Activity & Logs */}
            <Grid item xs={12} lg={8}>
              <div className="flex flex-col gap-6">
                
                {/* Activity Stream Tile */}
                <motion.div variants={item}>
                  <Box sx={{ background: "var(--bg-base)", border: "1px dashed var(--border-subtle)", p: { xs: 3, md: 4 }, borderRadius: 0 }}>
                    <div className="flex items-center justify-between mb-8 pb-4 border-b border-dashed border-[var(--border-subtle)]">
                      <div className="flex items-center gap-3">
                        <Activity size={18} className="text-[var(--primary)]" />
                        <h3 className="text-[10px] font-black uppercase tracking-widest text-[var(--text-primary)] font-mono">Activity_Flow_Stream</h3>
                      </div>
                      <Link href="/dashboard/analytics" className="text-[10px] font-black text-[var(--primary)] uppercase tracking-widest hover:underline font-mono">
                        EXPLORE_REPORTS →
                      </Link>
                    </div>

                    {analyticsLoading ? (
                      <SkeletonText lines={4} />
                    ) : (
                      <div className="font-mono text-[13px] leading-relaxed text-[var(--text-secondary)] bg-[var(--bg-hover)] p-5 border-l-2 border-[var(--primary)]">
                        {displayAnalytics?.summary || "No synchronization data available in local buffer."}
                      </div>
                    )}
                  </Box>
                </motion.div>

                {/* System Automation Tiles */}
                <motion.div variants={item}>
                   <Box sx={{ background: "var(--bg-elevated)", border: "1px dashed var(--border-subtle)", p: { xs: 3, md: 4 }, borderRadius: 0 }}>
                      <div className="flex items-center gap-3 mb-6">
                         <Zap size={18} className="text-[var(--secondary)]" />
                         <h3 className="text-[10px] font-black uppercase tracking-widest text-[var(--text-primary)] font-mono">Automation_Yield_Matrix</h3>
                      </div>
                      <MetricCardGrid columns={2}>
                        <MetricCard
                          title="Success_Rate"
                          value={metrics?.success_rate ? `${(metrics.success_rate * 100).toFixed(1)}%` : "—"}
                          icon={CheckCircle}
                          status={metrics && metrics.success_rate > 0.8 ? "success" : "warning"}
                          progress={metrics ? { value: Math.round(metrics.success_rate * 100), max: 100, label: "NODE_INTEGRITY" } : undefined}
                          loading={metricsLoading}
                        />
                        <MetricCard
                          title="Latency_Buffer"
                          value={metrics?.avg_execution_time_ms ? `${(metrics.avg_execution_time_ms / 1000).toFixed(1)}S` : "—"}
                          icon={Timer}
                          status="info"
                          loading={metricsLoading}
                        />
                      </MetricCardGrid>
                   </Box>
                </motion.div>
              </div>
            </Grid>

            {/* Right Column: Console & Insights */}
            <Grid item xs={12} lg={4}>
              <div className="flex flex-col gap-6 h-full">
                
                {/* AI Cortex Console Tile */}
                <motion.div variants={item} className="h-full">
                  <Box sx={{ background: "#050505", border: "1px dashed var(--border-subtle)", p: { xs: 3, md: 4 }, borderRadius: 0, height: "100%", display: "flex", flexDirection: "column" }}>
                    <div className="flex items-center gap-3 mb-6">
                       <Sparkles size={18} className="text-[var(--accent)]" />
                       <h3 className="text-[10px] font-black uppercase tracking-widest text-[var(--text-primary)] font-mono">Cortex_Advisory</h3>
                    </div>
                    
                    <div className="flex-1 bg-black/40 border border-[var(--border-subtle)] p-4 font-mono text-[11px] mb-6 overflow-y-auto max-h-[200px] text-[var(--text-muted)] italic">
                       {suggestionLoading ? (
                         <div className="animate-pulse">BOOTING_CORTEX...</div>
                       ) : displaySuggestion?.suggestion ? (
                         `> ${displaySuggestion.suggestion}`
                       ) : (
                         "> WAITING_FOR_INPUT_SIGNAL..."
                       )}
                    </div>

                    <button className="w-full py-3 bg-[var(--primary)] text-black text-[10px] font-black uppercase tracking-widest hover:bg-white transition-all flex items-center justify-center gap-2 font-mono">
                       <Bot size={14} />
                       ACCESS_CO_PILOT
                    </button>
                  </Box>
                </motion.div>

                {/* System Log Tile */}
                <motion.div variants={item}>
                   <Box sx={{ background: "var(--bg-elevated)", border: "1px dashed var(--border-subtle)", p: { xs: 3, md: 4 }, borderRadius: 0 }}>
                      <div className="flex items-center justify-between mb-6">
                         <div className="flex items-center gap-3">
                           <Terminal size={18} className="text-[var(--text-faint)]" />
                           <h3 className="text-[10px] font-black uppercase tracking-widest text-[var(--text-primary)] font-mono">Kernel_Logs</h3>
                         </div>
                         <div className="w-2 h-2 rounded-full bg-[var(--primary)] animate-pulse" />
                      </div>
                      <div className="space-y-3 font-mono text-[9px] text-[var(--text-faint)] uppercase">
                         <div className="flex justify-between border-b border-dashed border-[var(--border-subtle)] pb-1">
                            <span>WS_CONNECTION</span>
                            <span className="text-[var(--primary)]">ESTABLISHED</span>
                         </div>
                         <div className="flex justify-between border-b border-dashed border-[var(--border-subtle)] pb-1">
                            <span>SESSION_KEY</span>
                            <span>{user?.email?.slice(0, 8)}...</span>
                         </div>
                         <div className="flex justify-between border-b border-dashed border-[var(--border-subtle)] pb-1">
                            <span>NODE_SYNC</span>
                            <span className="text-[var(--secondary)]">88%</span>
                         </div>
                      </div>
                   </Box>
                </motion.div>
              </div>
            </Grid>
          </Grid>
          
          {/* Bottom Layer: Secondary Matrices */}
          <motion.div variants={item}>
             <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                  { label: "UPTIME", value: "99.98%", icon: Activity },
                  { label: "MEMORY", value: "256MB", icon: Zap },
                  { label: "NODES", value: "12/12", icon: Users },
                  { label: "SYNC", value: "INSTANT", icon: RefreshCw },
                ].map((m, i) => (
                  <div key={i} className="p-4 border border-dashed border-[var(--border-subtle)] bg-[var(--bg-base)] flex flex-col gap-2">
                     <div className="flex items-center justify-between">
                        <span className="text-[9px] font-black text-[var(--text-faint)] tracking-widest uppercase">{m.label}</span>
                        <m.icon size={12} className="text-[var(--text-faint)]" />
                     </div>
                     <div className="text-xl font-black text-[var(--text-primary)] font-mono">{m.value}</div>
                  </div>
                ))}
             </div>
          </motion.div>

        </motion.div>
      </Container>

      <BottomNav />
    </Box>
  );
}
