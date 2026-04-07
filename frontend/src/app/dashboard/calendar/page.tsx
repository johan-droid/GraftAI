"use client";

import { useState, useEffect, useMemo, useDeferredValue } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  X,
  Clock,
  Trash2,
  Edit3,
  CheckCircle2,
  Loader2,
  Calendar,
  Video,
  LayoutGrid,
  List,
  Globe,
  Zap,
  RefreshCw,
} from "lucide-react";
import {
  getEvents,
  createEvent,
  updateEvent,
  deleteEvent,
  getAvailableSlots,
  manualSync,
  CalendarEvent as Event,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { useSyncStatus } from "@/hooks/use-sync-status";
import { useOfflineSync } from "@/hooks/use-offline-sync";
import { db, LocalEvent } from "@/lib/db";
import { useToast } from "@/hooks/use-toast";
import { DayCell } from "@/components/calendar/DayCell";
import dynamic from "next/dynamic";
import CalendarSkeleton from "@/components/calendar/CalendarSkeleton";

const DayDetailModal = dynamic(() => import("@/components/calendar/DayDetailModal"), {
  loading: () => null,
});

const EditEventModal = dynamic(() => import("@/components/calendar/EditEventModal"), {
  loading: () => null,
});

const CATEGORIES = {
  meeting: {
    label: "Meeting",
    dot: "bg-indigo-400",
    ring: "ring-indigo-400/20",
    text: "text-indigo-300",
    bg: "bg-indigo-400/10 border-indigo-400/20",
  },
  event: {
    label: "Event",
    dot: "bg-amber-400",
    ring: "ring-amber-400/20",
    text: "text-amber-300",
    bg: "bg-amber-400/10 border-amber-400/20",
  },
  birthday: {
    label: "Birthday",
    dot: "bg-pink-400",
    ring: "ring-pink-400/20",
    text: "text-pink-300",
    bg: "bg-pink-400/10 border-pink-400/20",
  },
  task: {
    label: "Task",
    dot: "bg-cyan-400",
    ring: "ring-cyan-400/20",
    text: "text-cyan-300",
    bg: "bg-cyan-400/10 border-cyan-400/20",
  },
} as const;

type Cat = keyof typeof CATEGORIES;

type ViewMode = "month" | "week" | "list";
const CALENDAR_SYNC_COOLDOWN_MS = 10 * 60 * 1000;
const CALENDAR_LAST_SYNC_KEY = "graftai_calendar_last_sync_at";

export default function CalendarPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [editingEvent, setEditingEvent] = useState<Event | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [draftEvent, setDraftEvent] = useState({
    title: "",
    description: "",
    category: "meeting" as Cat,
    start_time_local: "",
    end_time_local: "",
    is_remote: false,
    status: "confirmed",
    meeting_platform: "",
    attendees: "",
  });
  const [slots, setSlots] = useState<{
    start: string;
    end: string;
    local_label?: string;
    guest_label?: string;
  }[]>([]);
  const [targetTz, setTargetTz] = useState("UTC");
  const [viewMode, setViewMode] = useState<ViewMode>("month");

  const { days, startDate, endDate } = useMemo(() => {
    const ms = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const me = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
    const sd = new Date(ms);
    sd.setDate(sd.getDate() - ms.getDay());
    const ed = new Date(me);
    ed.setDate(ed.getDate() + (6 - me.getDay()));
    const list: Date[] = [];
    const cur = new Date(sd);
    while (cur <= ed) {
      list.push(new Date(cur));
      cur.setDate(cur.getDate() + 1);
    }
    return { days: list, startDate: sd, endDate: ed };
  }, [currentDate]);

  const { isSyncing: sseSyncing, status: sseStatus, message: sseMessage, lastSyncAt } = useSyncStatus();
  const { isOnline, getEvents: getOfflineEvents } = useOfflineSync(startDate, endDate);
  const deferredEvents = useDeferredValue(events);
  const { toast } = useToast();

  useEffect(() => {
    if (lastSyncAt) {
      getOfflineEvents(startDate.toISOString(), endDate.toISOString())
        .then(setEvents)
        .catch(console.error);
        
      if (isOnline) toast.success(sseMessage || "Your calendar is up to date.");
    }
  }, [lastSyncAt, startDate, endDate, toast, sseMessage, getOfflineEvents, isOnline]);

  const runCalendarSync = async (force: boolean = false) => {
    if (isSyncing || sseSyncing) return;

    if (!force && typeof window !== "undefined") {
      const raw = window.localStorage.getItem(CALENDAR_LAST_SYNC_KEY);
      const lastSyncAtVal = raw ? Number(raw) : 0;
      if (Number.isFinite(lastSyncAtVal) && Date.now() - lastSyncAtVal < CALENDAR_SYNC_COOLDOWN_MS) {
        return;
      }
    }

    setIsSyncing(true);
    try {
      await manualSync();
      if (typeof window !== "undefined") {
        window.localStorage.setItem(CALENDAR_LAST_SYNC_KEY, String(Date.now()));
      }
      const syncedEvents = await getEvents(startDate.toISOString(), endDate.toISOString());
      setEvents(syncedEvents);
    } catch (error) {
      console.error("Calendar sync failed:", error);
    } finally {
      setIsSyncing(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    getOfflineEvents(startDate.toISOString(), endDate.toISOString())
      .then(setEvents)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [startDate, endDate, getOfflineEvents]);

  useEffect(() => {
    void runCalendarSync(false);
    // Intentional one-time mount sync; rate-limited via localStorage cooldown.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    getAvailableSlots(currentDate.toISOString(), 60, targetTz)
      .then((d) => setSlots(d.slice(0, 4)))
      .catch(console.error);
  }, [currentDate, targetTz]);

  useEffect(() => {
    if (!showModal || !selectedDate) return;

    const pad = (value: number) => String(value).padStart(2, "0");
    const formatLocal = (date: Date) =>
      `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;

    const defaultStart = new Date(selectedDate);
    defaultStart.setHours(9, 0, 0, 0);
    const defaultEnd = new Date(defaultStart.getTime() + 60 * 60 * 1000);

    setDraftEvent((prev) => ({
      ...prev,
      title: "",
      description: "",
      category: "meeting",
      start_time_local: formatLocal(defaultStart),
      end_time_local: formatLocal(defaultEnd),
      is_remote: false,
      status: "confirmed",
      meeting_platform: "",
      attendees: "",
    }));
  }, [showModal, selectedDate]);

  // High-Efficiency Memoized Indexing (Big Brand Methodology)
  const eventsByDate = useMemo(() => {
    const map: Record<string, Event[]> = {};
    deferredEvents.forEach((event: Event) => {
      const dateKey = new Date(event.start_time).toDateString();
      if (!map[dateKey]) map[dateKey] = [];
      map[dateKey].push(event);
    });
    return map;
  }, [deferredEvents]);

  const getEventsForDay = (d: Date) => eventsByDate[d.toDateString()] || [];

  // High-Efficiency Category Counting (O(N) One-Pass)
  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = { meeting: 0, task: 0, birthday: 0, event: 0 };
    events.forEach((ev) => {
      if (counts[ev.category] !== undefined) counts[ev.category]++;
    });
    return counts;
  }, [events]);

  // Derived views/helpers for week and list modes
  const weekDays = useMemo(() => {
    const start = new Date(currentDate);
    start.setDate(currentDate.getDate() - start.getDay());
    return Array.from({ length: 7 }).map((_, i) => {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      return d;
    });
  }, [currentDate]);

  const eventsInRange = useMemo(() => {
    return events
      .filter((ev) => {
        const t = new Date(ev.start_time);
        return t >= startDate && t <= endDate;
      })
      .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());
  }, [events, startDate, endDate]);

  const handleCreate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!selectedDate) return;

    // 1. Prepare data
    const start = new Date(draftEvent.start_time_local);
    const end = new Date(draftEvent.end_time_local);
    const attendees = draftEvent.attendees
      .split(",")
      .map((email) => email.trim())
      .filter((email) => email.length > 0);

    const eventPayload = {
      title: draftEvent.title || "New Event",
      description: draftEvent.description,
      category: draftEvent.category,
      start_time: start.toISOString(),
      end_time: end.toISOString(),
      is_remote: draftEvent.is_remote,
      status: draftEvent.status,
      meeting_platform: draftEvent.meeting_platform || undefined,
      attendees,
    };

    // 2. OPTIMISTIC UPDATE (Offline-First)
    const tempId = `temp_${Date.now()}`;
    const optimisticEvent: any = { 
      id: tempId, 
      ...eventPayload, 
      sync_status: 'pending' 
    };

    setEvents((prev) => [...prev, optimisticEvent]);
    setShowModal(false);
    setSelectedDate(null);

    // 3. Save to local DB
    await db.events.add({
      ...(optimisticEvent as LocalEvent),
      user_id: 'me', // placeholder
      last_modified: new Date().toISOString()
    });

    if (!isOnline) {
      toast.success("Event saved locally. Will sync when online.");
      return;
    }

    // 4. Background Server Call
    setCreating(true);
    try {
      const created = await createEvent(eventPayload);
      
      // Update local state and DB with the real ID from server
      setEvents((prev) => prev.map(ev => ev.id === tempId ? created : ev));
      await db.events.delete(tempId);
      await db.events.add({
        ...created,
        sync_status: 'synced',
        last_modified: new Date().toISOString()
      });
      
      toast.success("Event synced successfully.");
    } catch (e) {
      console.error("Sync failed, event remains in local queue:", e);
      // We keep the pending event in the local list
      toast.error("Cloud sync failed. Event is kept locally.");
    } finally {
      setCreating(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingEvent) return;
    try {
      const updated = await updateEvent(editingEvent.id, editingEvent);
      setEvents((prev) => prev.map((ev) => (ev.id.toString() === updated.id.toString() ? updated : ev)));
      setEditingEvent(null);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id: number | string) => {
    if (!confirm("Delete this event?")) return;
    try {
      await deleteEvent(id);
      setEvents((prev) => prev.filter((e) => e.id.toString() !== id.toString()));
      setEditingEvent(null);
      await db.events.delete(id);
    } catch (e) {
      console.error(e);
    }
  };

  const navigate = (dir: "prev" | "next") =>
    setCurrentDate(
      new Date(
        currentDate.getFullYear(),
        currentDate.getMonth() + (dir === "next" ? 1 : -1),
        1
      )
    );

  const today = new Date();
  const monthLabel = currentDate.toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });

  return (
    <div className="flex h-[calc(100vh-53px)] overflow-hidden bg-[#030712]/50">
      {/* Main Calendar Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-indigo-500/5 blur-[120px] rounded-full" />
        </div>

        {/* Calendar Toolbar */}
        <div className="flex flex-wrap items-center gap-3 px-4 py-4 border-b border-white/[0.06] bg-[#040a18]/40 backdrop-blur-xl shrink-0 z-10 overflow-x-auto">
          <div className="flex flex-wrap items-center gap-1.5 p-1.5 rounded-xl bg-white/5 border border-white/8 backdrop-blur-md min-w-0">
            <button
              onClick={() => navigate("prev")}
              aria-label="Previous month"
              title="Previous month"
              className="p-2 rounded-lg hover:bg-white/8 text-slate-400 hover:text-white transition-all active:scale-90"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button className="px-3 py-1 text-[15px] font-bold text-white min-w-[120px] max-w-full truncate tracking-tight">
              {monthLabel}
            </button>
            <button
              onClick={() => navigate("next")}
              aria-label="Next month"
              title="Next month"
              className="p-2 rounded-lg hover:bg-white/8 text-slate-400 hover:text-white transition-all active:scale-90"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={() => setCurrentDate(new Date())}
            className="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-slate-300 hover:text-white hover:bg-white/8 text-[13px] font-bold transition-all shadow-sm flex-shrink-0"
          >
            Today
          </button>

          <button
            onClick={() => void runCalendarSync(true)}
            disabled={isSyncing}
            className="px-4 py-2 rounded-xl border border-indigo-500/30 bg-indigo-500/10 text-indigo-200 hover:text-white hover:bg-indigo-500/20 text-[13px] font-bold transition-all shadow-sm disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2 flex-shrink-0"
          >
            {isSyncing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            Sync now
          </button>

          <div className="ml-auto flex flex-wrap items-center gap-2 p-1.5 rounded-xl bg-white/5 border border-white/8 backdrop-blur-md">
            {!isOnline && (
              <div className="flex items-center gap-2 px-3 animate-pulse">
                <div className="w-2 h-2 rounded-full bg-amber-500" />
                <span className="text-[11px] font-bold text-amber-500 uppercase tracking-tight">Offline Mode</span>
              </div>
            )}
            {(isSyncing || sseSyncing) ? (
              <div className="flex items-center gap-2 px-3">
                <Loader2 className="w-3 h-3 animate-spin text-indigo-400" />
                <span className="text-[11px] font-medium text-slate-300">
                  {sseMessage || (isSyncing ? "Syncing..." : "Updating...")}
                </span>
              </div>
            ) : null}
            {(["month", "week", "list"] as ViewMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-bold transition-all capitalize",
                  viewMode === mode ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20" : "text-slate-400 hover:text-slate-200"
                )}
              >
                {mode === "month" ? (
                  <LayoutGrid className="w-4 h-4" />
                ) : mode === "list" ? (
                  <List className="w-4 h-4" />
                ) : (
                  <Calendar className="w-4 h-4" />
                )}
                <span className="hidden lg:inline">{mode}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Calendar Grid */}
        <div className="flex-1 flex flex-col p-4 overflow-hidden">
          {loading ? (
            <CalendarSkeleton />
          ) : (
            <>
              {viewMode === "month" ? (
                <>
                  {/* Day headers */}
                  <div className="overflow-x-auto">
                    <div className="min-w-[560px] grid grid-cols-7 gap-1 mb-1">
                      {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => (
                        <div
                          key={d}
                          className="text-center text-[11px] font-bold text-slate-600 uppercase tracking-wider py-2"
                        >
                          {d}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Date grid (month) */}
                  <div className="flex-1 min-h-0 overflow-x-auto overflow-y-auto">
                    <div
                      className="min-w-[560px] grid grid-cols-7 grid-rows-6 gap-1 min-h-[500px]"
                      style={{ gridAutoRows: '1fr' }}
                    >
                      {days.map((day, idx) => {
                        const dayEvents = getEventsForDay(day);
                        return (
                          <DayCell
                            key={idx}
                            day={day}
                            today={today}
                            currentDate={currentDate}
                            selectedDate={selectedDate}
                            dayEvents={dayEvents}
                            categories={CATEGORIES}
                            onSelect={(d) => {
                              setSelectedDate(d);
                              setShowModal(true);
                            }}
                          />
                        );
                      })}
                    </div>
                  </div>
                </>
              ) : viewMode === "week" ? (
                <>
                  {/* Week headers */}
                  <div className="overflow-x-auto">
                    <div className="min-w-[560px] grid grid-cols-7 gap-1 mb-1">
                      {weekDays.map((d) => (
                        <div
                          key={d.toDateString()}
                          className="text-center text-[11px] font-bold text-slate-600 uppercase tracking-wider py-2"
                        >
                          {d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Week grid */}
                  <div className="flex-1 min-h-0 overflow-x-auto overflow-y-auto w-full">
                    <div className="min-w-[560px] grid grid-cols-7 gap-1 min-h-[150px] h-full">
                      {weekDays.map((day, idx) => (
                        <DayCell
                          key={idx}
                          day={day}
                          today={today}
                          currentDate={currentDate}
                          selectedDate={selectedDate}
                          dayEvents={getEventsForDay(day)}
                          categories={CATEGORIES}
                          onSelect={(d) => {
                            setSelectedDate(d);
                            setShowModal(true);
                          }}
                        />
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <>
                  {/* List view */}
                  <div className="space-y-3">
                    {eventsInRange.length > 0 ? (
                      (() => {
                        // Group by date
                        const groups: Record<string, any[]> = {};
                        eventsInRange.forEach((ev) => {
                          const key = new Date(ev.start_time).toDateString();
                          groups[key] = groups[key] || [];
                          groups[key].push(ev);
                        });

                        return Object.entries(groups).map(([date, evs]) => (
                          <div key={date} className="p-3 bg-white/3 rounded-xl border border-white/[0.04]">
                            <div className="text-sm font-bold text-white mb-2">{date}</div>
                            <div className="space-y-2">
                              {evs.map((ev) => (
                                <div key={ev.id} className="flex items-center justify-between">
                                  <div>
                                    <div className="text-sm font-semibold text-white">{ev.title}</div>
                                    <div className="text-xs text-slate-400">{new Date(ev.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} — {ev.category}</div>
                                  </div>
                                  <div className="text-xs text-slate-500">{ev.is_remote ? 'Remote' : ''}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        ));
                      })()
                    ) : (
                      <div className="text-center py-8 text-slate-500">No events in this range</div>
                    )}
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>

      {/* Right Sidebar */}
      <div className="hidden xl:flex w-[280px] shrink-0 flex-col border-l border-white/[0.06] bg-[#040a18]/50">
        <div className="p-4 border-b border-white/[0.06]">
          <h3 className="text-sm font-bold text-white mb-1">AI-Suggested Slots</h3>
          <p className="text-xs text-slate-500">Optimal times for your next meeting</p>
        </div>

        {/* Timezone selector */}
        <div className="px-4 py-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-2 mb-2">
            <Globe className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Guest timezone</span>
          </div>
          <select
            value={targetTz}
            onChange={(e) => setTargetTz(e.target.value)}
            aria-label="Target timezone"
            title="Target timezone"
            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-indigo-500/50 appearance-none"
          >
            <option value="UTC">UTC</option>
            <option value="America/New_York">New York (EST)</option>
            <option value="America/Los_Angeles">Los Angeles (PST)</option>
            <option value="Europe/London">London (GMT)</option>
            <option value="Asia/Tokyo">Tokyo (JST)</option>
            <option value="Australia/Sydney">Sydney (AEST)</option>
            <option value="Asia/Dubai">Dubai (GST)</option>
            <option value="Asia/Kolkata">Mumbai (IST)</option>
          </select>
        </div>

        {/* Slots */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {slots.length > 0 ? (
            slots.map((s, i) => (
              <button
                key={i}
                className="w-full text-left p-3 rounded-xl border border-white/[0.06] bg-white/[0.02] hover:border-indigo-500/30 hover:bg-indigo-500/5 transition-all group"
              >
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-3.5 h-3.5 text-indigo-400" />
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wide">Optimal overlap</span>
                </div>
                <p className="text-sm font-semibold text-white">
                  {s.local_label ?? new Date(s.start).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </p>
                {s.guest_label && <p className="text-xs text-indigo-300 mt-1">Guest: {s.guest_label}</p>}
                <div className="mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <span className="text-[11px] text-indigo-400 font-semibold">Book this slot →</span>
                </div>
              </button>
            ))
          ) : (
            <div className="text-center py-8">
              <Calendar className="w-8 h-8 text-slate-700 mx-auto mb-2" />
              <p className="text-xs text-slate-600">No slots available</p>
            </div>
          )}
        </div>

        {/* Categories */}
        <div className="p-4 border-t border-white/[0.06]">
          <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-3">Categories</p>
          <div className="space-y-1.5">
            {Object.entries(CATEGORIES).map(([key, val]) => (
              <div key={key} className="flex items-center justify-between py-1">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${val.dot}`} />
                  <span className="text-[12px] text-slate-400 font-medium">{val.label}</span>
                </div>
                <span className="text-[11px] text-slate-600 font-mono">
                  {categoryCounts[key] ?? 0}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Day Detail Modal */}
      <AnimatePresence>
        {showModal && (
          <DayDetailModal
            isOpen={showModal}
            onClose={() => setShowModal(false)}
            selectedDate={selectedDate}
            dayEvents={getEventsForDay(selectedDate!)}
            categories={CATEGORIES}
            draftEvent={draftEvent}
            setDraftEvent={setDraftEvent}
            handleCreate={handleCreate}
            handleDelete={handleDelete}
            setEditingEvent={setEditingEvent}
            creating={creating}
          />
        )}
      </AnimatePresence>

      {/* Edit Event Modal */}
      <AnimatePresence>
        {editingEvent && (
          <EditEventModal
            event={editingEvent}
            onClose={() => setEditingEvent(null)}
            onUpdate={handleUpdate}
            onDelete={handleDelete}
            setEditingEvent={setEditingEvent}
            categories={CATEGORIES}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
