"use client";

import { Terminal } from "lucide-react";

export default function DeveloperCorner() {
  return (
    <div className="space-y-8 pb-12 font-mono">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 pb-6 border-b border-dashed border-[var(--border-subtle)]">
        <div>
          <h1 className="text-4xl font-black text-[var(--text-primary)] uppercase tracking-tighter">Developer_Corner</h1>
          <p className="text-xs mt-2 uppercase tracking-[0.2em] text-[var(--text-muted)]">
            // Awaiting Backend Telemetry Connection
          </p>
        </div>
      </div>

      <div className="p-6 border border-dashed border-[var(--border-subtle)] bg-[var(--bg-base)] text-center">
        <Terminal className="h-8 w-8 text-[var(--text-muted)] mx-auto mb-4" />
        <p className="text-sm text-[var(--text-muted)]">
          System telemetry and API protocols will be displayed here once backend endpoints are integrated.
        </p>
      </div>
    </div>
  );
}
