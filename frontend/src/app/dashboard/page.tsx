"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { 
  getAnalyticsSummary, 
  getEvents, 
  getProactiveSuggestion,
  ProactiveSuggestionResponse
} from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent, CardFooter, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { SmartActions } from "@/components/dashboard/SmartActions";
import type { SmartAction } from "@/components/dashboard/SmartActions";
import { 
  Calendar as CalendarIcon, 
  Clock, 
  Sparkles, 
  TrendingUp, 
  Users, 
  Video, 
  ChevronRight,
  Activity
} from "lucide-react";

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
};

type DashboardSuggestion = { suggestion?: string };
type DashboardAnalyticsDetails = {
  meetings?: number;
  hours?: number;
  growth?: number;
  cancellations?: number;
  recent_events?: { id: number; title: string; start_time: string; category?: string; is_upcoming?: boolean }[];
  next_event?: { id: number; title: string; start_time: string; category?: string; is_upcoming?: boolean } | null;
};

type DashboardSummary = {
  summary: string;
  details?: DashboardAnalyticsDetails;
};

type DashboardStats = {
  totalMeetings?: number;
  focusHours?: number;
  collaborators?: number;
};

type DashboardData = { stats: DashboardStats; events: any[]; suggestion: ProactiveSuggestionResponse };

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  const handleExecuteSmartAction = async (action: SmartAction) => {
    // In a real integration, we'd trigger backend execute endpoints.
    console.log("Triggered Smart Action:", action);
    // You could put a toast here or call the actual endpoint
  };

  useEffect(() => {
    async function loadDashboard() {
      try {
        const todayStart = new Date();
        todayStart.setHours(0, 0, 0, 0);
        const todayEnd = new Date();
        todayEnd.setHours(23, 59, 59, 999);

        const [stats, events, suggestion] = await Promise.all<[
          DashboardSummary,
          any[],
          ProactiveSuggestionResponse
        ]>([
          getAnalyticsSummary(),
          getEvents(todayStart.toISOString(), todayEnd.toISOString()),
          getProactiveSuggestion("User is viewing the main dashboard.")
        ]);
        setData({
          stats: {
            totalMeetings: stats.details?.meetings,
            focusHours: stats.details?.hours,
            collaborators: stats.details?.recent_events?.length,
          },
          events,
          suggestion,
        });
      } catch (error) {
        console.error("Failed to load dashboard data:", error);
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <motion.div 
      className="max-w-7xl mx-auto p-6 space-y-8"
      variants={containerVariants}
      initial="hidden"
      animate="show"
    >
      {/* Hero Section & Quick Actions */}
      <motion.div variants={itemVariants} className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Good morning, Alex.</h1>
          <p className="text-muted-foreground mt-1">Here is your schedule and AI insights for today.</p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline">
            <Clock className="mr-2 h-4 w-4" />
            Review Schedule
          </Button>
          <Button>
            <Video className="mr-2 h-4 w-4" />
            Join Next Meeting
          </Button>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Meetings</CardTitle>
            <CalendarIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.stats?.totalMeetings ?? 0}</div>
            <p className="text-xs text-muted-foreground mt-1 flex items-center">
              Active period total
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Focus Time</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.stats?.focusHours ? data.stats.focusHours.toFixed(1) : '0'} hrs</div>
            <p className="text-xs text-muted-foreground mt-1">Based on free calendar space</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Engagement</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.stats?.collaborators ?? 0}</div>
            <p className="text-xs text-muted-foreground mt-1">Recent significant interactions</p>
          </CardContent>
        </Card>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Timeline Section */}
        <motion.div variants={itemVariants} className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Today&apos;s Timeline</h2>
            <Button variant="ghost" size="sm">
              View Calendar <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
          
          <Card>
            <CardContent className="p-0">
            <div className="divide-y relative">
                {data?.events && data.events.length > 0 ? (
                  data.events.map((event: any, i: number) => {
                    const startTime = new Date(event.start_time);
                    const endTime = new Date(event.end_time);
                    const durationMins = Math.round((endTime.getTime() - startTime.getTime()) / 60000);
                    const formattedTime = startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    const formattedDuration = durationMins >= 60 ? `${Math.floor(durationMins / 60)}h ${durationMins % 60}m` : `${durationMins}m`;
                    const now = new Date();
                    const active = now >= startTime && now <= endTime;

                    return (
                      <div key={i} className={`p-6 flex items-start gap-4 transition-colors ${active ? 'bg-primary/5' : ''}`}>
                        <div className="w-24 flex-shrink-0 text-sm font-medium text-muted-foreground">
                          {formattedTime}
                        </div>
                        <div className="relative">
                          {active && (
                            <span className="absolute -left-7 top-1 flex h-3 w-3">
                              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                              <span className="relative inline-flex rounded-full h-3 w-3 bg-primary"></span>
                            </span>
                          )}
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className={`font-semibold ${active ? 'text-primary' : ''}`}>
                              {event.title}
                            </h4>
                            {active && <Badge variant="secondary">In Progress</Badge>}
                          </div>
                          <div className="text-sm text-muted-foreground flex items-center gap-3">
                            <span className="flex items-center"><Clock className="mr-1 h-3 w-3" /> {formattedDuration}</span>
                            <span>• {event.category || "General"}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="p-6 text-center text-muted-foreground">
                    No events scheduled for today. Take a break!
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* AI Suggestion Panel */}
        <motion.div variants={itemVariants} className="space-y-4">
          <h2 className="text-xl font-semibold flex items-center">
            <Sparkles className="mr-2 h-5 w-5 text-primary" />
            AI Suggestions
          </h2>
          <Card className="border-primary/20 bg-primary/5 shadow-none">
            <CardHeader>
              <CardTitle className="text-base">Schedule Optimization</CardTitle>
              <CardDescription>
                Identified an opportunity based on your schedule.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm">
                {data?.suggestion?.suggestion || "You have back-to-back meetings from 1:00 PM to 4:00 PM tomorrow. Consider moving the 'Weekly Standup' to Friday morning to protect your focus time."}
              </p>
              
              {data?.suggestion?.smart_actions && data.suggestion.smart_actions.length > 0 && (
                <div className="mt-4">
                  <SmartActions 
                    actions={data.suggestion.smart_actions} 
                    onExecute={handleExecuteSmartAction} 
                  />
                </div>
              )}
            </CardContent>
            {(!data?.suggestion?.smart_actions || data.suggestion.smart_actions.length === 0) && (
              <CardFooter className="flex gap-2">
                <Button className="w-full" size="sm">
                  Apply Change
                </Button>
                <Button className="w-full" variant="outline" size="sm">
                  Dismiss
                </Button>
              </CardFooter>
            )}
          </Card>
        </motion.div>
      </div>
    </motion.div>
  );
}

