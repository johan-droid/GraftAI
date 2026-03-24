"use client";

import Link from "next/link";
import { useState } from "react";

export default function CalendarPage() {
  const [message, setMessage] = useState<string>("Use this page to connect your calendar and create meetings.");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Calendar</h1>
          <p className="text-slate-400">Manage your meeting schedule and availability.</p>
        </div>
        <Link href="/dashboard" className="text-primary hover:text-primary/80 inline-flex items-center gap-1 font-medium">
          Back to Dashboard
        </Link>
      </div>

      <div className="rounded-2xl border border-slate-800/60 bg-slate-950/60 p-6">
        <p className="text-slate-300 mb-2">{message}</p>
        <button
          onClick={() => setMessage("Calendar connection is coming soon. Stay tuned!")}
          className="px-4 py-2 bg-primary rounded-lg text-white hover:bg-primary/90"
        >
          Simulate Calendar Connect
        </button>
      </div>

      <div className="rounded-2xl border border-slate-800 p-4 bg-slate-900/50">
        <p className="text-sm text-slate-300">Future implementation: connect Google/Microsoft calendar and schedule with the AI assistant.</p>
      </div>
    </div>
  );
}
