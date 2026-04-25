"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useAuth } from "@/app/providers/auth-provider";
import { toast } from "@/components/ui/Toast";
import { Clock, Copy, MoreVertical, Plus, Video, Phone, Users, Check } from "lucide-react";
import { listEventTypes, updateEventType, EventTypeResponse } from "@/lib/api";
import { ShareEventButton } from "@/components/dashboard/ShareEventButton";
import { TimeRangeEditor, TimeRange } from "@/components/dashboard/availability/TimeRangeEditor";

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: { type: "spring" as const, stiffness: 300, damping: 24 },
  },
};

type EventTypeItem = EventTypeResponse;

export default function EventTypesPage() {
  const [events, setEvents] = useState<EventTypeItem[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [availability, setAvailability] = useState<Record<string, TimeRange[]>>({
    Monday: [{ start: "09:00", end: "17:00" }],
    Tuesday: [{ start: "09:00", end: "17:00" }],
    Wednesday: [{ start: "09:00", end: "17:00" }],
    Thursday: [{ start: "09:00", end: "17:00" }],
    Friday: [{ start: "09:00", end: "17:00" }],
    Saturday: [],
    Sunday: [],
  });

  useEffect(() => {
    void loadEventTypes();
  }, []);

  async function loadEventTypes() {
    setLoading(true);
    setError(null);

    try {
      const data = await listEventTypes();
      setEvents(data || []);

      // Load availability from the first event type if it exists
      if (data && data.length > 0 && data[0].availability) {
        setAvailability(parseAvailabilityFromApi(data[0].availability));
      } else if (data && data.length === 0) {
        // Reset to empty state if no event types exist
        setAvailability({
          Monday: [], Tuesday: [], Wednesday: [], Thursday: [], Friday: [], Saturday: [], Sunday: []
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load event types");
    } finally {
      setLoading(false);
    }
  }

  function normalizeAvailabilityForApi(value: Record<string, TimeRange[]>) {
    return Object.fromEntries(
      Object.entries(value).map(([day, ranges]) => [
        day.toLowerCase(),
        ranges.map((range) => `${range.start}-${range.end}`),
      ])
    );
  }

  function parseAvailabilityFromApi(apiValue: Record<string, string[]>): Record<string, TimeRange[]> {
    const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
    const result: Record<string, TimeRange[]> = {};

    days.forEach((day) => {
      const apiRanges = apiValue[day] || apiValue[day.toLowerCase()] || [];
      result[day] = apiRanges.map((rangeStr) => {
        const [start, end] = rangeStr.split("-");
        return { start: start || "09:00", end: end || "17:00" };
      });
    });

    return result;
  }

  async function saveAvailability(day: string, ranges: TimeRange[]) {
    const currentUsername = user?.username;
    const targetEvent = events[0];

    if (!currentUsername) {
      toast.warning("Unable to save availability before authentication completes.");
      return;
    }

    if (!targetEvent) {
      toast.error("No event type selected to persist availability.");
      return;
    }

    const updatedAvailability = { ...availability, [day]: ranges };
    setAvailability(updatedAvailability);

    try {
      await updateEventType(targetEvent.id, {
        availability: normalizeAvailabilityForApi(updatedAvailability),
      });
      toast.success("Availability saved.");
    } catch (err) {
      console.error("Failed to save availability:", err);
      toast.error("Could not save availability. Please try again.");
    }
  }

  async function toggleEvent(id: string) {
    const event = events.find((e) => e.id === id);
    if (!event) return;

    const nextPublic = !event.is_public;

    try {
      await updateEventType(id, { is_public: nextPublic });
      setEvents((previous) =>
        previous.map((item) =>
          item.id === id ? { ...item, is_public: nextPublic } : item
        )
      );
      toast.success("Event visibility updated");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update event visibility");
    }
  }

  async function copyLink(id: string, slug: string) {
    const origin = typeof window !== "undefined" ? window.location.origin : "https://graftai.com";
    const url = `${origin}/public/${slug}`;

    if (typeof navigator !== "undefined" && navigator.clipboard) {
      try {
        await navigator.clipboard.writeText(url);
        setCopiedId(id);
        toast.success("Link copied to clipboard!");
        setTimeout(() => setCopiedId(null), 2000);
      } catch (err) {
        console.error("Failed to copy event link:", err);
        toast.error("Failed to copy link to clipboard");
      }
    } else {
      toast.error("Clipboard is not available in this environment");
    }
  }

  const getIcon = (meetingProvider?: string) => {
    if (meetingProvider?.toLowerCase().includes("phone")) return <Phone size={18} />;
    if (meetingProvider?.toLowerCase().includes("video") || meetingProvider?.toLowerCase().includes("zoom") || meetingProvider?.toLowerCase().includes("meet")) return <Video size={18} />;
    return <Users size={18} />;
  };

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto w-full">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-10 border-b border-[#DADCE0] pb-6">
        <div>
          <h1 className="text-3xl font-medium text-[#202124] tracking-tight mb-2">Event Types</h1>
          <p className="text-[#5F6368] text-base max-w-xl">
            Create and manage your meeting formats. Share these links to let people book time on your calendar.
          </p>
        </div>
        <button
          type="button"
          className="inline-flex items-center gap-2 rounded-full bg-[#1A73E8] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#1666d7]"
          onClick={loadEventTypes}
          disabled={loading}
        >
          {loading ? "Refreshing…" : "Refresh event types"}
        </button>
      </div>

      {error && (
        <div className="mb-6 rounded-3xl border border-[#E37400] bg-[#FFF4E5] px-5 py-4 text-sm text-[#8A4B00]">
          {error}
        </div>
      )}

      <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <motion.button
          variants={cardVariants}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="group flex flex-col items-center justify-center min-h-[220px] bg-[#F8F9FA] border-2 border-dashed border-[#DADCE0] rounded-3xl hover:border-[#1A73E8] hover:bg-[#E8F0FE] transition-colors cursor-pointer"
          type="button"
          onClick={() => toast.info("Create event flow is available in the full event type editor.")}
        >
          <div className="w-14 h-14 rounded-full bg-white border border-[#DADCE0] flex items-center justify-center text-[#1A73E8] mb-4 group-hover:bg-[#1A73E8] group-hover:text-white transition-all shadow-sm">
            <Plus size={28} />
          </div>
          <span className="text-lg font-medium text-[#202124] group-hover:text-[#1967D2] transition-colors">New Event Type</span>
          <span className="text-sm text-[#5F6368] mt-1">Create a new meeting format</span>
        </motion.button>

        {events.map((event) => {
          const duration = event.duration_minutes ? `${event.duration_minutes} min` : "Custom";
          const active = event.is_public ?? false;
          const displayType = event.meeting_provider || "booking";

          return (
            <motion.div
              key={event.id}
              variants={cardVariants}
              className={`flex flex-col bg-white border border-[#DADCE0] rounded-3xl p-6 shadow-sm hover:shadow-md transition-all ${!active ? "opacity-60 grayscale-[0.5]" : ""}`}
            >
              <div className="flex items-start justify-between mb-6">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center text-white shadow-sm bg-[#1A73E8]`}>
                  {getIcon(event.meeting_provider)}
                </div>
                <button
                  type="button"
                  title={active ? "Disable event" : "Enable event"}
                  onClick={() => toggleEvent(event.id)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${active ? "bg-[#1A73E8]" : "bg-[#DADCE0]"}`}
                >
                  <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm ${active ? "translate-x-6" : "translate-x-1"}`} />
                </button>
              </div>

              <div className="flex-1">
                <h3 className="text-xl font-semibold text-[#202124] mb-2 truncate">{event.name}</h3>
                <div className="flex items-center gap-2 text-[#5F6368] text-sm font-medium">
                  <Clock size={16} />
                  <span>{duration}</span>
                  <span className="w-1 h-1 rounded-full bg-[#DADCE0] mx-1" />
                  <span className="capitalize">{displayType}</span>
                </div>
              </div>

              <div className="pt-6 mt-6 border-t border-[#F1F3F4] flex items-center justify-between">
                <ShareEventButton username={user?.username ?? "current-user"} eventSlug={event.slug} />

                <button type="button" title="More options" className="p-2 text-[#5F6368] hover:bg-[#F1F3F4] rounded-full transition-colors">
                  <MoreVertical size={20} />
                </button>
              </div>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Weekly Availability Section - Only show if events exist */}
      {events.length > 0 && (
        <div className="mt-12">
          <h2 className="text-2xl font-semibold text-[#202124] mb-6">Weekly Availability</h2>
          <div className="bg-white border border-[#DADCE0] rounded-2xl p-6 shadow-sm">
            {Object.keys(availability).map((day) => (
              <TimeRangeEditor
                key={day}
                dayName={day}
                initialRanges={availability[day]}
                onChange={(ranges) => saveAvailability(day, ranges)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
