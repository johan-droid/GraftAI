"use client";

import { useEffect, useState } from "react";
import { getAnalyticsSummary } from "@/lib/api";
import { Activity, ArrowUpRight, Loader2 } from "lucide-react";
import Link from "next/link";

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<string>("");
  const [details, setDetails] = useState({ meetings: 0, hours: 0, growth: 0 });
  const [status, setStatus] = useState("Loading analytics...");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAnalyticsSummary()
      .then((data) => {
        setSummary(data.summary);
        if (data.details) {
          setDetails(data.details as any);
        }
        setStatus("Analytics loaded successfully.");
      })
      .catch((err) => {
        console.error("Analytics load error:", err);
        setStatus("Could not load analytics right now.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Analytics</h1>
          <p className="text-slate-400">Your activity and AI performance metrics.</p>
        </div>
        <Link href="/dashboard" className="text-primary hover:text-primary/80 inline-flex items-center gap-1 font-medium">
          Back to Dashboard <ArrowUpRight className="w-4 h-4" />
        </Link>
      </div>

      <div className="rounded-2xl border border-slate-800/60 bg-slate-950/60 p-6">
        {loading ? (
          <div className="flex items-center gap-2 text-slate-400">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading analytics
          </div>
        ) : (
          <>
            <p className="text-xs uppercase tracking-wider text-slate-500 mb-3">{status}</p>
            <p className="text-sm text-slate-300 mb-4">{summary || "No analytics data available right now."}</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="rounded-xl border border-slate-800 p-4">
                <p className="text-xs uppercase text-slate-500">Meetings</p>
                <p className="text-2xl font-semibold text-white">{details.meetings}</p>
              </div>
              <div className="rounded-xl border border-slate-800 p-4">
                <p className="text-xs uppercase text-slate-500">Hours</p>
                <p className="text-2xl font-semibold text-white">{details.hours}</p>
              </div>
              <div className="rounded-xl border border-slate-800 p-4">
                <p className="text-xs uppercase text-slate-500">Growth</p>
                <p className="text-2xl font-semibold text-white">{details.growth}%</p>
              </div>
            </div>
          </>
        )}
      </div>

      <div className="rounded-2xl border border-slate-800 p-4 bg-slate-900/50">
        <p className="text-sm text-slate-300">Tip: If you still see 404s, verify frontend and backend URLs in deployment environment variables: NEXT_PUBLIC_API_BASE_URL and APP_BASE_URL / FRONTEND_BASE_URL.</p>
      </div>
    </div>
  );
}
