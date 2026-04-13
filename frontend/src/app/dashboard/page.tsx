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
          background: isDark ? "hsl(240, 24%, 7%)" : "hsl(220, 14%, 96%)",
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
        background: isDark ? "hsl(240, 24%, 7%)" : "hsl(220, 14%, 96%)",
        pb: { xs: 10, md: 4 }, // Extra padding for bottom nav on mobile
      }}
    >
      <MobileSidebar />

      <Container maxWidth="xl" sx={{ px: { xs: 2, md: 4 }, py: { xs: 2, md: 4 } }}>
        <motion.div variants={container} initial="hidden" animate="show">
          {/* Header */}
          <motion.div variants={item}>
            <Header
              userName={(user as any)?.name}
              userEmail={user?.email}
              userAvatar={(user as any)?.avatar}
              notificationCount={3}
            />
          </motion.div>

          {/* Greeting Section */}
          <motion.div variants={item}>
            <Greeting
              userName={(user as any)?.name}
              userEmail={user?.email}
              isLoading={false}
            />
          </motion.div>

          {/* Stats Grid */}
          <motion.div variants={item}>
            <Grid container spacing={{ xs: 2, md: 3 }} sx={{ mb: { xs: 3, md: 4 } }}>
              {analyticsLoading ? (
                <>
                  <Grid item xs={12} sm={6} md={4}>
                    <SkeletonCard />
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <SkeletonCard />
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <SkeletonCard />
                  </Grid>
                </>
              ) : (
                <>
                  <Grid item xs={12} sm={6} md={4}>
                    <StatCard
                      title="Meetings This Week"
                      value={stats.meetings != null ? stats.meetings.toString() : "—"}
                      icon={Calendar}
                      trend={meetingsDelta != null ? {
                        value: Math.round((meetingsDelta / (stats.previousWeekMeetings || 1)) * 100),
                        label: "vs last week",
                      } : undefined}
                      color="primary"
                      delay={0}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <StatCard
                      title="AI Copilot Hours"
                      value={stats.hours != null ? `${stats.hours}h` : "—"}
                      icon={Bot}
                      trend={stats.growth != null ? {
                        value: stats.growth,
                        label: "efficiency gain",
                      } : undefined}
                      color="success"
                      delay={0.1}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <StatCard
                      title="System Status"
                      value="Operational"
                      icon={Activity}
                      color="success"
                      delay={0.2}
                    />
                  </Grid>
                </>
              )}
            </Grid>
          </motion.div>

          {/* AI Automation Metrics Section */}
          <motion.div variants={item}>
            <Box sx={{ mb: { xs: 3, md: 4 } }}>
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 2 }}>
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 700,
                    color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                    letterSpacing: "-0.01em",
                  }}
                >
                  AI Automation Metrics
                </Typography>
                <Tooltip title="Refresh metrics">
                  <IconButton onClick={refetchMetrics} size="small">
                    <RefreshCw size={18} />
                  </IconButton>
                </Tooltip>
              </Box>
              
              <MetricCardGrid columns={4}>
                <MetricCard
                  title="Total Automations"
                  value={metrics?.total_automations?.toLocaleString() ?? "—"}
                  icon={Zap}
                  status={metrics ? "success" : "neutral"}
                  trend={metrics ? { value: 12, label: "vs last week", direction: "up" } : undefined}
                  loading={metricsLoading}
                />
                <MetricCard
                  title="Success Rate"
                  value={metrics?.success_rate ? `${(metrics.success_rate * 100).toFixed(1)}%` : "—"}
                  icon={CheckCircle}
                  status={metrics && metrics.success_rate > 0.8 ? "success" : metrics && metrics.success_rate > 0.5 ? "warning" : "error"}
                  trend={metrics ? { value: 5, label: "improvement", direction: "up" } : undefined}
                  loading={metricsLoading}
                  progress={metrics ? { value: Math.round(metrics.success_rate * 100), max: 100, label: "Success Rate" } : undefined}
                />
                <MetricCard
                  title="Avg Execution Time"
                  value={metrics?.avg_execution_time_ms ? `${(metrics.avg_execution_time_ms / 1000).toFixed(1)}s` : "—"}
                  icon={Timer}
                  status={metrics && metrics.avg_execution_time_ms < 5000 ? "success" : metrics && metrics.avg_execution_time_ms < 10000 ? "warning" : "error"}
                  loading={metricsLoading}
                />
                <MetricCard
                  title="Pending Automations"
                  value={metrics?.pending_automations?.toString() ?? "—"}
                  icon={Activity}
                  status={metrics && metrics.pending_automations === 0 ? "success" : metrics && metrics.pending_automations < 5 ? "warning" : "info"}
                  loading={metricsLoading}
                />
              </MetricCardGrid>
            </Box>
          </motion.div>

          {/* Main Content Grid */}
          <Grid container spacing={{ xs: 2, md: 3 }}>
            {/* Recent Activity - Takes 2/3 on desktop */}
            <Grid item xs={12} lg={8}>
              <motion.div variants={item}>
                <Paper
                  elevation={0}
                  sx={{
                    p: { xs: 2, md: 3 },
                    background: isDark
                      ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                      : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
                    border: "1px solid hsla(239, 84%, 67%, 0.15)",
                    borderRadius: "16px",
                    height: "100%",
                  }}
                >
                  {/* Section Header */}
                  <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 3 }}>
                    <Typography
                      variant="h6"
                      sx={{
                        fontWeight: 700,
                        color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                        letterSpacing: "-0.01em",
                      }}
                    >
                      Recent Activity
                    </Typography>
                    <Link href="/dashboard/analytics" style={{ textDecoration: "none" }}>
                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          gap: 0.5,
                          fontSize: "0.875rem",
                          color: "hsl(239, 84%, 67%)",
                          fontWeight: 500,
                          "&:hover": { textDecoration: "underline" },
                        }}
                      >
                        View all
                        <ArrowUpRight size={16} />
                      </Box>
                    </Link>
                  </Box>

                  {/* Activity Content */}
                  {analyticsLoading && !analyticsError ? (
                    <SkeletonText lines={3} />
                  ) : analyticsError ? (
                    <Box sx={{ textAlign: "center", py: 3 }}>
                      <Typography color="error" sx={{ mb: 2 }}>
                        Failed to load activity data
                      </Typography>
                      <Button
                        onClick={refetchAnalytics}
                        variant="outlined"
                        size="small"
                        sx={{ textTransform: "none" }}
                      >
                        Retry
                      </Button>
                    </Box>
                  ) : displayAnalytics?.summary ? (
                    <Typography
                      sx={{
                        color: isDark ? "hsl(215, 16%, 70%)" : "hsl(215, 16%, 47%)",
                        lineHeight: 1.6,
                        fontSize: "0.9375rem",
                      }}
                    >
                      {displayAnalytics.summary}
                    </Typography>
                  ) : (
                    <EmptyState
                      icon={Activity}
                      title="No recent activity"
                      description="Your meetings and events will appear here once you start using GraftAI."
                      action={{ label: "Schedule Meeting", href: "/book" }}
                    />
                  )}
                </Paper>
              </motion.div>
            </Grid>

            {/* Sidebar - Takes 1/3 on desktop */}
            <Grid item xs={12} lg={4}>
              <Box sx={{ display: "flex", flexDirection: "column", gap: { xs: 2, md: 3 } }}>
                {/* Upcoming Events */}
                <motion.div variants={item}>
                  <Paper
                    elevation={0}
                    sx={{
                      p: { xs: 2, md: 3 },
                      background: isDark
                        ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                        : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
                      border: "1px solid hsla(239, 84%, 67%, 0.15)",
                      borderRadius: "16px",
                    }}
                  >
                    <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 2 }}>
                      <Typography
                        sx={{
                          fontWeight: 600,
                          color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                        }}
                      >
                        Upcoming
                      </Typography>
                      <Link href="/dashboard/calendar" style={{ textDecoration: "none" }}>
                        <Box
                          sx={{
                            fontSize: "0.8125rem",
                            color: "hsl(239, 84%, 67%)",
                            "&:hover": { textDecoration: "underline" },
                          }}
                        >
                          Calendar →
                        </Box>
                      </Link>
                    </Box>

                    {eventsLoading ? (
                      <SkeletonText lines={3} />
                    ) : displayEvents.length > 0 ? (
                      <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
                        {displayEvents.slice(0, 4).map((evt) => (
                          <Box
                            key={evt.id}
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              gap: 2,
                              p: 1.5,
                              borderRadius: "12px",
                              background: isDark ? "hsla(239, 84%, 67%, 0.05)" : "hsla(239, 84%, 67%, 0.03)",
                              border: "1px solid hsla(239, 84%, 67%, 0.1)",
                              transition: "all 0.2s ease",
                              "&:hover": {
                                background: isDark ? "hsla(239, 84%, 67%, 0.1)" : "hsla(239, 84%, 67%, 0.05)",
                                borderColor: "hsla(239, 84%, 67%, 0.2)",
                              },
                            }}
                          >
                            <Box
                              sx={{
                                width: 36,
                                height: 36,
                                borderRadius: "10px",
                                background: isDark ? "hsla(239, 84%, 67%, 0.15)" : "hsla(239, 84%, 67%, 0.1)",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                flexShrink: 0,
                              }}
                            >
                              <Calendar size={18} style={{ color: "hsl(239, 84%, 67%)" }} />
                            </Box>
                            <Box sx={{ flex: 1, minWidth: 0 }}>
                              <Typography
                                sx={{
                                  fontSize: "0.875rem",
                                  fontWeight: 600,
                                  color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                                  whiteSpace: "nowrap",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                }}
                              >
                                {evt.title}
                              </Typography>
                              <Typography
                                sx={{
                                  fontSize: "0.75rem",
                                  color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)",
                                  display: "flex",
                                  alignItems: "center",
                                  gap: 0.5,
                                }}
                              >
                                <Clock size={12} />
                                {new Date(evt.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                              </Typography>
                            </Box>
                          </Box>
                        ))}
                      </Box>
                    ) : (
                      <Typography
                        sx={{
                          textAlign: "center",
                          color: isDark ? "hsl(215, 16%, 40%)" : "hsl(215, 16%, 60%)",
                          fontSize: "0.875rem",
                          py: 2,
                        }}
                      >
                        No upcoming events
                      </Typography>
                    )}
                  </Paper>
                </motion.div>

                {/* AI Insight */}
                <motion.div variants={item}>
                  <Paper
                    elevation={0}
                    sx={{
                      p: { xs: 2, md: 3 },
                      background: isDark
                        ? "linear-gradient(135deg, hsla(25, 95%, 53%, 0.15) 0%, hsla(25, 95%, 53%, 0.05) 100%)"
                        : "linear-gradient(135deg, hsla(25, 95%, 53%, 0.1) 0%, hsla(25, 95%, 53%, 0.02) 100%)",
                      border: "1px solid hsla(25, 95%, 53%, 0.3)",
                      borderRadius: "16px",
                    }}
                  >
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
                      <Sparkles size={18} style={{ color: "hsl(25, 95%, 53%)" }} />
                      <Typography
                        sx={{
                          fontSize: "0.75rem",
                          fontWeight: 700,
                          textTransform: "uppercase",
                          letterSpacing: "0.05em",
                          color: "hsl(25, 95%, 53%)",
                        }}
                      >
                        AI Insight
                      </Typography>
                    </Box>

                    {suggestionLoading ? (
                      <SkeletonText lines={2} />
                    ) : displaySuggestion?.suggestion ? (
                      <Typography
                        sx={{
                          color: isDark ? "hsl(215, 16%, 70%)" : "hsl(215, 16%, 47%)",
                          fontSize: "0.9375rem",
                          lineHeight: 1.6,
                          mb: 2,
                        }}
                      >
                        {displaySuggestion.suggestion}
                      </Typography>
                    ) : (
                      <Typography
                        sx={{
                          color: isDark ? "hsl(215, 16%, 40%)" : "hsl(215, 16%, 60%)",
                          fontSize: "0.875rem",
                          mb: 2,
                        }}
                      >
                        Ask the AI Copilot for personalized scheduling insights.
                      </Typography>
                    )}

                    <GradientButton
                      component={Link}
                      href="/dashboard/ai"
                      gradientVariant="secondary"
                      size="small"
                      sx={{
                        background: "hsl(25, 95%, 53%)",
                        "&:hover": { background: "hsl(25, 95%, 48%)" },
                      }}
                    >
                      <Bot size={16} style={{ marginRight: 8 }} />
                      Open Copilot
                    </GradientButton>
                  </Paper>
                </motion.div>

                {/* Recent Automations */}
                <motion.div variants={item}>
                  <Paper
                    elevation={0}
                    sx={{
                      p: { xs: 2, md: 3 },
                      background: isDark
                        ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                        : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
                      border: "1px solid hsla(239, 84%, 67%, 0.15)",
                      borderRadius: "16px",
                    }}
                  >
                    <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 2 }}>
                      <Typography
                        sx={{
                          fontWeight: 600,
                          color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                        }}
                      >
                        Recent Automations
                      </Typography>
                      <Link href="/dashboard/automations" style={{ textDecoration: "none" }}>
                        <Typography
                          sx={{
                            fontSize: "0.8125rem",
                            color: "hsl(239, 84%, 67%)",
                            "&:hover": { textDecoration: "underline" },
                          }}
                        >
                          View All →
                        </Typography>
                      </Link>
                    </Box>
                    
                    {metricsLoading ? (
                      <SkeletonText lines={4} />
                    ) : metrics?.recent_activity && metrics.recent_activity.length > 0 ? (
                      <DataTable
                        columns={[
                          {
                            key: "booking_id",
                            header: "Booking",
                            width: "40%",
                            render: (row) => (
                              <Typography
                                variant="body2"
                                sx={{
                                  fontWeight: 500,
                                  color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                                  whiteSpace: "nowrap",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  maxWidth: 150,
                                }}
                              >
                                {row.booking_id.slice(0, 8)}...
                              </Typography>
                            ),
                          },
                          {
                            key: "status",
                            header: "Status",
                            width: "25%",
                            render: (row) => <StatusChip status={row.status} size="small" />,
                          },
                          {
                            key: "decision_score",
                            header: "Score",
                            width: "20%",
                            align: "right",
                            render: (row) => (
                              <Typography
                                variant="body2"
                                sx={{
                                  fontWeight: 600,
                                  color: row.decision_score >= 80 ? "#22c55e" : row.decision_score >= 50 ? "#eab308" : "#ef4444",
                                }}
                              >
                                {row.decision_score}%
                              </Typography>
                            ),
                          },
                          {
                            key: "created_at",
                            header: "Time",
                            width: "15%",
                            align: "right",
                            render: (row) => (
                              <Typography variant="caption" color="text.secondary">
                                {new Date(row.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                              </Typography>
                            ),
                          },
                        ]}
                        data={metrics.recent_activity.slice(0, 5)}
                        keyExtractor={(row) => row.id}
                        pagination={false}
                        maxHeight={250}
                        className="mt-2"
                      />
                    ) : (
                      <EmptyState
                        icon={Zap}
                        title="No recent automations"
                        description="Automations will appear here when the AI agent processes bookings."
                        action={{ label: "Create Booking", href: "/book" }}
                      />
                    )}
                  </Paper>
                </motion.div>

                {/* Quick Access */}
                <motion.div variants={item}>
                  <Paper
                    elevation={0}
                    sx={{
                      p: { xs: 2, md: 3 },
                      background: isDark
                        ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                        : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
                      border: "1px solid hsla(239, 84%, 67%, 0.15)",
                      borderRadius: "16px",
                    }}
                  >
                    <Typography
                      sx={{
                        fontWeight: 600,
                        color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                        mb: 2,
                      }}
                    >
                      Quick Access
                    </Typography>

                    <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                      {[
                        { label: "Plugins & Integrations", href: "/dashboard/plugins", icon: Zap },
                        { label: "Privacy & Settings", href: "/dashboard/settings", icon: Settings },
                      ].map(({ label, href, icon: Icon }) => (
                        <Link key={href} href={href} style={{ textDecoration: "none" }}>
                          <Box
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "space-between",
                              p: 1.5,
                              borderRadius: "10px",
                              color: isDark ? "hsl(215, 16%, 70%)" : "hsl(215, 16%, 47%)",
                              transition: "all 0.2s ease",
                              "&:hover": {
                                background: isDark ? "hsla(239, 84%, 67%, 0.1)" : "hsla(239, 84%, 67%, 0.05)",
                                color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                              },
                            }}
                          >
                            <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                              <Icon size={18} />
                              <Typography sx={{ fontSize: "0.875rem", fontWeight: 500 }}>
                                {label}
                              </Typography>
                            </Box>
                            <ArrowUpRight size={16} />
                          </Box>
                        </Link>
                      ))}
                    </Box>
                  </Paper>
                </motion.div>
              </Box>
            </Grid>
          </Grid>
        </motion.div>
      </Container>

      <BottomNav />
    </Box>
  );
}
