"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  Calendar,
  Clock,
  Users,
  BarChart3,
  Zap,
  Loader2,
} from "lucide-react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import TimelineLineChart from "@/components/TimelineLineChart";
import { cn } from "@/lib/utils";
import { isMobile } from "react-device-detect";

const STAGGER = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const ITEM = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
};

interface AnalyticsMeetingType {
  label: string;
  pct: number;
}

interface AnalyticsTotals {
  meetings: number;
  hours: number;
  growth: number;
  unique_attendees: number;
  cancellations: number;
}

interface AnalyticsData {
  meeting_types?: AnalyticsMeetingType[];
  summary?: string;
  series?: Array<Record<string, unknown>>;
  totals?: AnalyticsTotals;
}

export default function AnalyticsPage() {
  const [range, setRange] = useState<"7d" | "30d" | "90d">("30d");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AnalyticsData | null>(null);

  const handleRangeChange = (nextRange: "7d" | "30d" | "90d") => {
    setError(null);
    setLoading(true);
    setRange(nextRange);
  };

  useEffect(() => {
    let alive = true;

    getAnalyticsRealtime(range)
      .then((payload) => {
        if (!alive) return;
        setData(payload);
      })
      .catch((err) => {
        if (!alive) return;
        setError(err instanceof Error ? err.message : "Failed to load analytics");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [range]);

  const series = useMemo(() => data?.series ?? [], [data]);
  const totals = data?.totals || {
    meetings: 0,
    hours: 0,
    growth: 0,
    unique_attendees: 0,
    cancellations: 0,
  };

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto">
      <motion.div variants={STAGGER} initial="hidden" animate="visible" className="space-y-5">
        <motion.div variants={ITEM} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">Analytics</h1>
            <p className="text-slate-400 text-sm mt-1">Advanced scheduling intelligence and workspace metrics.</p>
          </div>
          <div className="flex items-center gap-2">
            {(["7d", "30d", "90d"] as const).map((r) => (
              <Button
                key={r}
                variant={range === r ? "default" : "outline"}
                size="sm"
                onClick={() => handleRangeChange(r)}
                className={range === r ? "shadow-lg shadow-indigo-600/20" : ""}
              >
                {r === "7d" ? "7 Days" : r === "30d" ? "30 Days" : "90 Days"}
              </Button>
            ))}
          </div>
        </motion.div>

        {error && (
          <motion.div variants={ITEM} className="rounded-xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-sm text-red-200 backdrop-blur-sm">
            {error}
          </motion.div>
        )}

        <motion.div variants={ITEM} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: "Scheduled Meetings", value: totals.meetings.toString(), icon: Calendar, color: "indigo", sub: "Currently active" },
            { label: "Focus Time", value: `${totals.hours}h`, icon: Clock, color: "violet", sub: "All calendars" },
            { label: "Client Contacts", value: totals.unique_attendees.toString(), icon: Users, color: "cyan", sub: "Network depth" },
            { label: "Success Rate", value: `${Math.max(0, 100 - (totals.cancellations * 5))}%`, icon: Zap, color: "emerald", sub: "Integrity" },
          ].map((kpi) => {
            const Icon = kpi.icon;
            return (
              <Card key={kpi.label} className="relative overflow-hidden group hover:border-white/20 transition-all">
                <CardHeader className="p-4 pb-2 flex flex-row items-center justify-between space-y-0">
                  <div className="p-2 bg-white/5 rounded-lg">
                    <Icon className="h-5 w-5 text-slate-300" />
                  </div>
                  <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20">Live</Badge>
                </CardHeader>
                <CardContent className="p-4 pt-2">
                  {loading ? (
                    <div className="h-8 w-16 bg-white/10 rounded animate-pulse" />
                  ) : (
                    <div className="text-3xl font-bold text-white">{kpi.value}</div>
                  )}
                  <p className="text-sm text-slate-400 mt-1">{kpi.label}</p>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mt-2">{kpi.sub}</p>
                </CardContent>
              </Card>
            );
          })}
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4 items-start">
          <motion.div variants={ITEM} className="col-span-1">
            <Card className="p-6 h-full">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-bold text-white flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-indigo-400" />
                  Meetings timeline
                </h2>
                <Badge variant="outline" className="text-slate-500 uppercase">Live</Badge>
              </div>

              {loading ? (
                <div className="min-h-[8rem] flex items-center justify-center">
                  <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
                </div>
              ) : (
                <div>
                  <TimelineLineChart data={series.slice(-10)} height={240} />

                  <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 items-center border-t border-white/5 pt-4">  
                    {((data?.meeting_types) || []).map((t) => {
                      const colorMap: Record<string, string> = {
                        meeting: "bg-violet-600",
                        event: "bg-cyan-500",
                        birthday: "bg-orange-500",
                        task: "bg-emerald-500",
                        other: "bg-slate-400",
                      };
                      const color = colorMap[t.label] ?? colorMap.other;
                      return (
                        <div key={t.label} className="flex items-center gap-1.5 text-xs text-slate-400">       
                          <span className={cn("w-2.5 h-2.5 rounded-full", color)} />
                          <span className="capitalize">{t.label}</span>
                          <span className="text-slate-500 font-medium">{t.pct}%</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </Card>
          </motion.div>

          {!isMobile && (
            <div className="space-y-4">
              <motion.div variants={ITEM}> 
                <Card className="p-4 bg-white/[0.02]">
                  <h2 className="text-xs font-bold text-white mb-3">Meeting types</h2>
                <div className="space-y-2.5">
                  {(data?.meeting_types || []).slice(0, 4).map((type) => (
                    <div key={type.label}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[11px] text-slate-400 font-medium capitalize">{type.label}</span>
                        <span className="text-[11px] text-slate-500">{type.pct}%</span>
                      </div>
                      <div className="h-1 rounded-full bg-white/5 overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${type.pct}%` }}
                          transition={{ duration: 0.6, ease: "easeOut" }}
                          className="h-full rounded-full bg-violet-500"
                        />
                      </div>
                    </div>
                  ))}
                  </div>
                </Card>
              </motion.div>

              <motion.div variants={ITEM}>
                <Card className="p-4 border-violet-500/20 bg-violet-500/5">
                  <div className="flex items-center gap-2 mb-1.5">
                  <TrendingUp className="w-3 h-3 text-violet-400" />
                  <span className="text-[10px] font-bold text-violet-300 uppercase tracking-wide">Summary</span>
                </div>
                <p className="text-[11px] text-slate-300 leading-relaxed line-clamp-3">{data?.summary || "No analytics summary available yet."}</p>
                </Card>
              </motion.div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
