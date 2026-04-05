"use client";

import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  X,
  Clock,
  MapPin,
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

export default function CalendarPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingEvent, setEditingEvent] = useState<Event | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [syncing, setSyncing] = useState(false);
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

  useEffect(() => {
    setLoading(true);
    getEvents(startDate.toISOString(), endDate.toISOString())
      .then(setEvents)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [startDate, endDate]);

  useEffect(() => {
    getAvailableSlots(currentDate.toISOString(), 60, targetTz)
      .then((d) => setSlots(d.slice(0, 4)))
      .catch(console.error);
  }, [currentDate, targetTz]);

  const getEventsForDay = (d: Date) =>
    events.filter((e) => {
      const ed = new Date(e.start_time);
      return (
        ed.getDate() === d.getDate() &&
        ed.getMonth() === d.getMonth() &&
        ed.getFullYear() === d.getFullYear()
      );
    });

  const handleCreate = async () => {
    if (!selectedDate) return;
    setCreating(true);
    try {
      const created = await createEvent({
        title: "New Meeting",
        description: "Created via GraftAI calendar",
        category: "meeting",
        start_time: selectedDate.toISOString(),
        end_time: new Date(selectedDate.getTime() + 3600000).toISOString(),
        is_remote: true,
        status: "confirmed",
      });
      setEvents((prev) => [...prev, created]);
    } catch (e) {
      console.error(e);
    } finally {
      setCreating(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await manualSync();
      const refreshed = await getEvents(startDate.toISOString(), endDate.toISOString());
      setEvents(refreshed);
    } catch (e) {
      console.error("Calendar sync failed", e);
    } finally {
      setSyncing(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingEvent) return;
    try {
      const updated = await updateEvent(editingEvent.id, editingEvent);
      setEvents((prev) => prev.map((ev) => (ev.id === updated.id ? updated : ev)));
      setEditingEvent(null);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this event?")) return;
    try {
      await deleteEvent(id);
      setEvents((prev) => prev.filter((e) => e.id !== id));
      setEditingEvent(null);
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
        <div className="flex items-center gap-4 px-6 py-4 border-b border-white/[0.06] bg-[#040a18]/40 backdrop-blur-xl shrink-0 z-10">
          <div className="flex items-center gap-1.5 p-1.5 rounded-xl bg-white/5 border border-white/8 backdrop-blur-md">
            <button
              onClick={() => navigate("prev")}
              className="p-2 rounded-lg hover:bg-white/8 text-slate-400 hover:text-white transition-all active:scale-90"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button className="px-4 py-1 text-[15px] font-bold text-white min-w-[200px] tracking-tight">
              {monthLabel}
            </button>
            <button
              onClick={() => navigate("next")}
              className="p-2 rounded-lg hover:bg-white/8 text-slate-400 hover:text-white transition-all active:scale-90"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={() => setCurrentDate(new Date())}
            className="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-slate-300 hover:text-white hover:bg-white/8 text-[13px] font-bold transition-all shadow-sm"
          >
            Today
          </button>

          <div className="ml-auto flex items-center gap-1.5 p-1.5 rounded-xl bg-white/5 border border-white/8 backdrop-blur-md">
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
        <div className="flex-1 overflow-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
            </div>
          ) : (
            <>
              {/* Day headers */}
              <div className="grid grid-cols-7 mb-1">
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => (
                  <div
                    key={d}
                    className="text-center text-[11px] font-bold text-slate-600 uppercase tracking-wider py-2"
                  >
                    {d}
                  </div>
                ))}
              </div>

              {/* Date grid */}
              <div className="grid grid-cols-7 gap-1">
                {days.map((day, idx) => {
                  const dayEvents = getEventsForDay(day);
                  const isSelected = selectedDate?.toDateString() === day.toDateString();
                  const isToday = day.toDateString() === today.toDateString();
                  const isCurrentMonth = day.getMonth() === currentDate.getMonth();

                  return (
                    <motion.div
                      key={idx}
                      whileHover={{ scale: isCurrentMonth ? 1.02 : 1 }}
                      onClick={() => {
                        if (isCurrentMonth) {
                          setSelectedDate(day);
                          setShowModal(true);
                        }
                      }}
                      className={cn(
                        "relative flex flex-col p-2 rounded-xl cursor-pointer min-h-[80px] md:min-h-[100px] transition-all border",
                        isSelected
                          ? "border-indigo-500/60 bg-indigo-600/10"
                          : isCurrentMonth
                          ? "border-white/[0.05] bg-white/[0.02] hover:border-white/10 hover:bg-white/[0.04]"
                          : "border-transparent opacity-30 cursor-default"
                      )}
                    >
                      <div
                        className={cn(
                          "w-7 h-7 rounded-full flex items-center justify-center text-sm font-semibold mb-1 self-center",
                          isToday ? "bg-indigo-600 text-white" : isSelected ? "text-indigo-300" : "text-slate-400"
                        )}
                      >
                        {day.getDate()}
                      </div>

                      <div className="space-y-0.5 flex-1">
                        {dayEvents.slice(0, 2).map((ev) => (
                          <div
                            key={ev.id}
                            className={cn(
                              "text-[10px] font-medium px-1.5 py-0.5 rounded-md truncate border",
                              CATEGORIES[ev.category]?.bg ?? "bg-slate-500/10 border-slate-500/20",
                              CATEGORIES[ev.category]?.text ?? "text-slate-300"
                            )}
                          >
                            {ev.title}
                          </div>
                        ))}
                        {dayEvents.length > 2 && (
                          <div className="text-[10px] text-slate-500 font-medium px-1">
                            +{dayEvents.length - 2} more
                          </div>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
              </div>
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
                  {events.filter((e) => e.category === key).length}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Day Detail Modal */}
      <AnimatePresence>
        {showModal && selectedDate && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setShowModal(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 16 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 16 }}
              transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
              className="relative w-full max-w-lg bg-[#0d1424] border border-white/10 rounded-2xl overflow-hidden shadow-2xl"
            >
              <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.07]">
                <div>
                  <h3 className="text-base font-bold text-white">
                    {selectedDate.toLocaleDateString("en-US", {
                      weekday: "long",
                      month: "long",
                      day: "numeric",
                    })}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">{getEventsForDay(selectedDate).length} events</p>
                </div>
                <button
                  onClick={() => setShowModal(false)}
                  aria-label="Close day details"
                  title="Close day details"
                  className="p-1.5 rounded-lg hover:bg-white/8 text-slate-500 hover:text-white transition-all"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="p-4 max-h-[60vh] overflow-y-auto space-y-2">
                {getEventsForDay(selectedDate).length === 0 ? (
                  <div className="text-center py-10">
                    <Calendar className="w-10 h-10 text-slate-700 mx-auto mb-3" />
                    <p className="text-slate-500 text-sm">No events for this day</p>
                  </div>
                ) : (
                  getEventsForDay(selectedDate).map((ev) => (
                    <div
                      key={ev.id}
                      className="group flex items-start gap-3 p-3 rounded-xl border border-white/[0.06] bg-white/[0.025] hover:border-white/10 transition-all"
                    >
                      <div className={`w-1 h-full min-h-[40px] rounded-full shrink-0 ${CATEGORIES[ev.category]?.dot ?? "bg-slate-400"}`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-white">{ev.title}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="flex items-center gap-1 text-[11px] text-slate-500">
                            <Clock className="w-3 h-3" />
                            {new Date(ev.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </span>
                          <span
                            className={cn(
                              "text-[10px] font-bold px-1.5 py-0.5 rounded border",
                              CATEGORIES[ev.category]?.bg,
                              CATEGORIES[ev.category]?.text
                            )}
                          >
                            {ev.category}
                          </span>
                          {ev.is_remote && <Video className="w-3 h-3 text-slate-500" />}
                        </div>
                      </div>
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => {
                            setEditingEvent(ev);
                            setShowModal(false);
                          }}
                          aria-label="Edit event"
                          title="Edit event"
                          className="p-1.5 rounded-md hover:bg-white/10 text-slate-500 hover:text-white transition-all"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(ev.id)}
                          aria-label="Delete event"
                          title="Delete event"
                          className="p-1.5 rounded-md hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-all"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>

              <div className="px-4 py-3 border-t border-white/[0.07] flex justify-between">
                <button
                  onClick={handleCreate}
                  disabled={creating}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 hover:text-white hover:bg-white/8 text-sm font-medium transition-all disabled:opacity-50"
                >
                  {creating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
                  Add event
                </button>
                <button
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-all"
                >
                  Done
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Edit Event Modal */}
      <AnimatePresence>
        {editingEvent && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/70 backdrop-blur-sm"
              onClick={() => setEditingEvent(null)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="relative w-full max-w-md bg-[#0d1424] border border-white/10 rounded-2xl p-6 shadow-2xl"
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Edit3 className="w-4 h-4 text-indigo-400" /> Edit event
                </h3>
                <button
                  onClick={() => setEditingEvent(null)}
                  aria-label="Close editor"
                  title="Close editor"
                  className="p-1.5 rounded-lg hover:bg-white/8 text-slate-500 hover:text-white transition-all"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleUpdate} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5 block">
                    Title
                  </label>
                  <input
                    type="text"
                    value={editingEvent.title}
                    onChange={(e) => setEditingEvent({ ...editingEvent, title: e.target.value })}
                    title="Event title"
                    placeholder="Event title"
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500/60 transition-colors"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5 block">
                    Description
                  </label>
                  <textarea
                    rows={3}
                    value={editingEvent.description}
                    onChange={(e) => setEditingEvent({ ...editingEvent, description: e.target.value })}
                    title="Event description"
                    placeholder="Event description"
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500/60 transition-colors resize-none"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5 block">
                      Status
                    </label>
                    <select
                      value={editingEvent.status}
                      onChange={(e) => setEditingEvent({ ...editingEvent, status: e.target.value })}
                      aria-label="Event status"
                      title="Event status"
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-3 text-sm text-white focus:outline-none focus:border-indigo-500/60 appearance-none"
                    >
                      <option value="confirmed">Confirmed</option>
                      <option value="pending">Pending</option>
                      <option value="canceled">Canceled</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5 block">
                      Category
                    </label>
                    <select
                      value={editingEvent.category}
                      onChange={(e) => setEditingEvent({ ...editingEvent, category: e.target.value as Cat })}
                      aria-label="Event category"
                      title="Event category"
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-3 text-sm text-white focus:outline-none focus:border-indigo-500/60 appearance-none"
                    >
                      {Object.keys(CATEGORIES).map((c) => (
                        <option key={c} value={c}>
                          {c}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="flex gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => handleDelete(editingEvent.id)}
                    aria-label="Delete event"
                    title="Delete event"
                    className="p-2.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 transition-all"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditingEvent(null)}
                    className="flex-1 py-2.5 rounded-xl bg-white/5 border border-white/10 text-slate-300 hover:text-white text-sm font-medium transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-all flex items-center justify-center gap-2"
                  >
                    <CheckCircle2 className="w-4 h-4" /> Save
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
