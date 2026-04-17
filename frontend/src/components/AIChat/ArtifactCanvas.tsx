"use client";

import React from "react";
import MarkdownRenderer from "./MarkdownRenderer";
import type { CalendarEvent } from "@/lib/api";

export default function ArtifactCanvas({
  upcomingEvents = [],
  latestMessage = "",
}: {
  upcomingEvents?: CalendarEvent[];
  latestMessage?: string;
}) {
  return (
    <aside className="hidden md:flex flex-col w-96 gap-4">
      <div className="p-4 border rounded-2xl bg-[var(--bg-card)] border-[var(--border)]">
        <h3 className="text-sm font-semibold text-[var(--text)]">Artifacts</h3>
        <div className="mt-3">
          <h4 className="text-xs text-[var(--text-faint)]">Latest AI Output</h4>
          <div className="mt-2 text-sm text-[var(--text)]">
            {latestMessage ? (
              <MarkdownRenderer content={latestMessage} />
            ) : (
              <div className="text-[var(--text-muted)]">No AI output yet.</div>
            )}
          </div>
        </div>
      </div>

      <div className="p-4 border rounded-2xl bg-[var(--bg-card)] border-[var(--border)]">
        <h4 className="text-sm font-semibold text-[var(--text)]">Upcoming Events</h4>
        <div className="mt-3 text-sm text-[var(--text)]">
          {upcomingEvents.length > 0 ? (
            <ul className="space-y-3">
              {upcomingEvents.map((ev) => (
                <li key={String(ev.id)} className="rounded-md p-2 bg-[var(--bg-surface)] border border-[var(--border)]">
                  <div className="font-medium">{ev.title}</div>
                  <div className="text-[11px] text-[var(--text-faint)]">{new Date(ev.start_time).toLocaleString()}</div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-[var(--text-muted)]">No upcoming events in the selected window.</div>
          )}
        </div>
      </div>
    </aside>
  );
}
