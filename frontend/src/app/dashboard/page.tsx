"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { Calendar, Clock3, ExternalLink, Sparkles, Users } from "lucide-react";
import { getAnalyticsRealtime, getEvents, type AnalyticsRealtimeResponse, type CalendarEvent } from "@/lib/api";
import { useAuth } from "@/providers/auth-provider";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const EVENT_LIST_LIMIT = 6;

export default function DashboardPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<AnalyticsRealtimeResponse | null>(null);
  const [events, setEvents] = useState<CalendarEvent[]>([]);

  useEffect(() => {
    let alive = true;

    const start = new Date();
    const end = new Date();
    end.setDate(end.getDate() + 14);

    Promise.all([
      getAnalyticsRealtime("30d"),
      getEvents(start.toISOString(), end.toISOString()),
    ])
      .then(([analytics, calendar]) => {
        if (!alive) return;
        setMetrics(analytics);
        setEvents(calendar || []);
      })
      .catch((err) => {
        if (!alive) return;
        setError(err instanceof Error ? err.message : "Unable to load dashboard data.");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, []);

  const upcomingEvents = useMemo(
    () =>
      [...events]
        .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
        .slice(0, EVENT_LIST_LIMIT),
    [events]
  );

  const firstName =
    user?.full_name?.split(" ").find(Boolean) ||
    user?.email?.split("@")[0] ||
    "there";

  return (
    <motion.div
      className="space-y-6 p-4 md:p-6"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100 md:text-3xl">Welcome back, {firstName}</h1>
          <p className="mt-1 text-sm text-slate-400">
            Your next two weeks at a glance, synced from your connected calendars.
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link href="/dashboard/calendar">Open calendar</Link>
          </Button>
          <Button asChild>
            <Link href="/dashboard/event-types">Share booking link</Link>
          </Button>
        </div>
      </div>

      {error && (
        <Card className="border-red-500/30 bg-red-500/10">
          <CardContent className="p-4 text-sm text-red-200">{error}</CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          icon={<Calendar className="h-4 w-4" />}
          label="Meetings (30d)"
          value={loading ? "..." : String(metrics?.totals.meetings ?? 0)}
        />
        <MetricCard
          icon={<Clock3 className="h-4 w-4" />}
          label="Focus hours"
          value={loading ? "..." : `${metrics?.totals.hours ?? 0}h`}
        />
        <MetricCard
          icon={<Users className="h-4 w-4" />}
          label="Unique attendees"
          value={loading ? "..." : String(metrics?.totals.unique_attendees ?? 0)}
        />
        <MetricCard
          icon={<Sparkles className="h-4 w-4" />}
          label="Growth"
          value={loading ? "..." : `${metrics?.totals.growth ?? 0}%`}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.5fr_1fr]">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between p-5 pb-2">
            <h2 className="text-sm font-semibold text-slate-100">Upcoming events</h2>
            <Button asChild size="sm" variant="ghost" className="text-slate-400 hover:text-slate-200">
              <Link href="/dashboard/calendar">
                View all <ExternalLink className="ml-1 h-3.5 w-3.5" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="p-5 pt-2">
            {loading ? (
              <p className="py-10 text-sm text-slate-500">Loading upcoming events...</p>
            ) : upcomingEvents.length === 0 ? (
              <p className="py-10 text-sm text-slate-500">No upcoming events yet. Create one from Calendar.</p>
            ) : (
              <div className="space-y-3">
                {upcomingEvents.map((event) => (
                  <div key={String(event.id)} className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
                    <p className="font-medium text-slate-100">{event.title}</p>
                    <p className="mt-1 text-xs text-slate-400">
                      {new Date(event.start_time).toLocaleString([], {
                        weekday: "short",
                        month: "short",
                        day: "numeric",
                        hour: "numeric",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="p-5 pb-2">
            <h2 className="text-sm font-semibold text-slate-100">Workspace pulse</h2>
          </CardHeader>
          <CardContent className="space-y-3 p-5 pt-2">
            <div className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
              <p className="text-xs uppercase tracking-wide text-slate-400">Cancellations</p>
              <p className="mt-1 text-xl font-semibold text-slate-100">{loading ? "..." : metrics?.totals.cancellations ?? 0}</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
              <p className="text-xs uppercase tracking-wide text-slate-400">Last generated summary</p>
              <p className="mt-1 text-sm text-slate-300">{loading ? "Loading..." : metrics?.summary || "No summary available yet."}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary" className="bg-white/10 text-slate-300 hover:bg-white/15">
                Live API data
              </Badge>
              <Badge variant="outline" className="border-white/20 text-slate-400">
                No mock content
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </motion.div>
  );
}

function MetricCard({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-400">{label}</p>
          <div className="text-slate-300">{icon}</div>
        </div>
        <p className="mt-2 text-2xl font-semibold text-slate-100">{value}</p>
      </CardContent>
    </Card>
  );
}
