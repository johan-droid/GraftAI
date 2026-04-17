"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Plus } from "lucide-react";
import { createEvent } from "@/lib/api";
import { toast } from "@/components/ui/Toast";

export default function NewCalendarEventPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [duration, setDuration] = useState<number>(60);
  const [loading, setLoading] = useState(false);

  const handleBack = () => router.push("/dashboard/calendar");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !date || !time) {
      toast.error("Please provide title, date and time.");
      return;
    }

    setLoading(true);
    try {
      const startIso = `${date}T${time}:00`;
      const start = new Date(startIso);
      const end = new Date(start.getTime() + duration * 60 * 1000);

      await createEvent({
        title,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        is_remote: false,
      });

      toast.success("Event created");
      router.push("/dashboard/calendar");
    } catch (err) {
      console.error(err);
      toast.error("Failed to create event. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={handleBack}
          aria-label="Back to calendar"
          className="p-2 rounded-md bg-white border shadow-sm"
        >
          <ArrowLeft size={18} />
        </button>
        <h1 className="text-xl font-semibold">Create Event</h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 bg-white p-4 rounded-lg shadow-sm border">
        <div>
          <label htmlFor="event-title" className="block text-sm font-medium mb-1">Title</label>
          <input
            id="event-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full rounded-md border px-3 py-2"
            placeholder="Meeting with..."
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="event-date" className="block text-sm font-medium mb-1">Date</label>
            <input id="event-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} className="w-full rounded-md border px-3 py-2" />
          </div>
          <div>
            <label htmlFor="event-time" className="block text-sm font-medium mb-1">Time</label>
            <input id="event-time" type="time" value={time} onChange={(e) => setTime(e.target.value)} className="w-full rounded-md border px-3 py-2" />
          </div>
        </div>

        <div>
          <label htmlFor="event-duration" className="block text-sm font-medium mb-1">Duration (minutes)</label>
          <input id="event-duration" type="number" value={duration} onChange={(e) => setDuration(Number(e.target.value))} className="w-40 rounded-md border px-3 py-2" />
        </div>

        <div className="pt-2">
          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-[#1A73E8] text-white px-4 py-3 rounded-md font-medium"
          >
            <Plus size={16} />
            {loading ? "Creating…" : "Create Event"}
          </button>
        </div>
      </form>
    </div>
  );
}
