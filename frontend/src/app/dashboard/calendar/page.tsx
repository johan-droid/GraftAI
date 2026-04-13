"use client";

/**
 * Calendar Page — Production
 * Uses react-big-calendar for Month/Week/Day views.
 * Implements: click-to-create, drag-to-reschedule, optimistic updates,
 * conflict detection, peach dark theme, full mobile support.
 */

import { useState, useEffect, useCallback, useMemo } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import {
  X, Plus, Loader2, Clock, MapPin, Trash2, CheckCircle2,
  ChevronLeft, ChevronRight, Calendar, AlertTriangle,
} from "lucide-react";
import {
  getEvents, createEvent, updateEvent, deleteEvent,
  type CalendarEvent,
} from "@/lib/api";
import { useOptimisticList } from "@/hooks/useQuery";
import { toast } from "@/components/ui/Toast";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { cn } from "@/lib/utils";

import "react-big-calendar/lib/addons/dragAndDrop/styles.css";

let tempIdCounter = -1;

// ── Lazy-load react-big-calendar (heavy) ──────────────────────────
const BigCalendar = dynamic(async () => {
  const [rbc, dnd] = await Promise.all([
    import("react-big-calendar"),
    import("react-big-calendar/lib/addons/dragAndDrop")
  ]);
  const withDragAndDrop = dnd.default || dnd.withDragAndDrop;
  return withDragAndDrop(rbc.Calendar);
}, {
  ssr: false,
  loading: () => (
    <div className="rounded-xl overflow-hidden" style={{ height: 520 }}>
      <Skeleton className="h-full w-full" />
    </div>
  ),
});

import("react-big-calendar/lib/css/react-big-calendar.css");

type RBCView = "month" | "week" | "day" | "agenda";
type CategoryKey = "meeting" | "event" | "birthday" | "task";

const CATEGORIES: Record<CategoryKey, { label: string; color: string }> = {
  meeting:  { label: "Meeting",  color: "var(--primary)" },
  event:    { label: "Event",    color: "var(--secondary)" },
  birthday: { label: "Birthday", color: "var(--accent)" },
  task:     { label: "Task",     color: "var(--text-secondary)" },
};

const FORM_DEFAULTS: Partial<CalendarEvent> = {
  title: "", description: "", category: "meeting",
  is_remote: false, status: "confirmed",
};

function hasConflict(evts: CalendarEvent[], a: Partial<CalendarEvent>): boolean {
  if (!a.start_time || !a.end_time) return false;
  const aStart = new Date(a.start_time).getTime();
  const aEnd   = new Date(a.end_time).getTime();
  return evts.some(e => {
    if (e.id === a.id) return false;
    const eStart = new Date(e.start_time).getTime();
    const eEnd   = new Date(e.end_time).getTime();
    return aStart < eEnd && aEnd > eStart;
  });
}

let localizer: ReturnType<typeof import("react-big-calendar").dateFnsLocalizer> | null = null;
async function getLocalizer() {
  if (localizer) return localizer;
  const { dateFnsLocalizer } = await import("react-big-calendar");
  const { default: format }   = await import("date-fns/format");
  const { default: parse }    = await import("date-fns/parse");
  const { default: startOfWeek } = await import("date-fns/startOfWeek");
  const { default: getDay }   = await import("date-fns/getDay");
  const enUS = (await import("date-fns/locale/en-US")).enUS;
  localizer = dateFnsLocalizer({ format, parse, startOfWeek, getDay, locales: { "en-US": enUS } });
  return localizer;
}

export default function CalendarPage() {
  const [date, setDate]     = useState(new Date());
  const [view, setView]     = useState<RBCView>("month");
  const [localizerReady, setLocalizerReady] = useState<typeof localizer>(null);
  const [loading, setLoading] = useState(true);

  const { items: events, setItems, add, update, remove } = useOptimisticList<CalendarEvent>([]);

  const [selectedSlot, setSelectedSlot]   = useState<{ start: Date; end: Date } | null>(null);
  const [editingEvent, setEditingEvent]   = useState<CalendarEvent | null>(null);
  const [form, setForm]                   = useState<Partial<CalendarEvent>>(FORM_DEFAULTS);
  const [saving, setSaving]               = useState(false);
  const [conflictWarning, setConflict]    = useState(false);

  useEffect(() => {
    getLocalizer().then(l => setLocalizerReady(l));
  }, []);

  const fetchRange = useCallback(async (start: Date, end: Date) => {
    setLoading(true);
    setItems([]);
    try {
      const data = await getEvents(start.toISOString(), end.toISOString());
      data.forEach(evt => add(evt));
    } catch {
      toast.error("Failed to load calendar events.");
    } finally {
      setLoading(false);
    }
  }, [add, setItems]);

  useEffect(() => {
    const start = new Date(date.getFullYear(), date.getMonth(), 1);
    const end   = new Date(date.getFullYear(), date.getMonth() + 1, 0);
    fetchRange(start, end);
  }, [date, fetchRange]);

  const rbcEvents = useMemo(() => events.map(e => ({
    id: e.id,
    title: e.title,
    start: new Date(e.start_time),
    end:   new Date(e.end_time),
    resource: e,
  })), [events]);

  function openCreateModal(slot: { start: Date; end: Date }) {
    const defaultEnd = new Date(slot.start.getTime() + 60 * 60 * 1000);
    setSelectedSlot({ start: slot.start, end: slot.end.getTime() > slot.start.getTime() ? slot.end : defaultEnd });
    setForm({
      ...FORM_DEFAULTS,
      start_time: slot.start.toISOString(),
      end_time:   (slot.end.getTime() > slot.start.getTime() ? slot.end : defaultEnd).toISOString(),
    });
    setConflict(hasConflict(events, { start_time: slot.start.toISOString(), end_time: defaultEnd.toISOString() }));
    setEditingEvent(null);
  }

  function openEditModal(rbcEvt: { resource: CalendarEvent }) {
    const evt = rbcEvt.resource;
    setEditingEvent(evt);
    setForm({ ...evt });
    setConflict(false);
    setSelectedSlot(null);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!form.title?.trim()) { toast.error("Title is required."); return; }
    setSaving(true);
    const optimisticId = --tempIdCounter;
    const optimistic: CalendarEvent = {
      id: optimisticId, user_id: 0, title: form.title!,
      description: form.description ?? "",
      category: form.category as CategoryKey ?? "meeting",
      start_time: form.start_time!, end_time: form.end_time!,
      is_remote: form.is_remote ?? false, status: "confirmed",
    };
    const rollback = add(optimistic);
    setSelectedSlot(null);
    try {
      const created = await createEvent(form);
      remove(optimisticId);
      add(created);
      toast.success("Event created.");
    } catch (err) {
      rollback();
      toast.error((err as Error).message || "Failed to create event.");
    } finally {
      setSaving(false);
    }
  }

  async function handleUpdate(e: React.FormEvent) {
    e.preventDefault();
    if (!editingEvent || !form.title?.trim()) return;
    setSaving(true);
    const rollback = update(editingEvent.id, form);
    setEditingEvent(null);
    try {
      const updated = await updateEvent(editingEvent.id, form);
      update(editingEvent.id, updated);
      toast.success("Event updated.");
    } catch (err) {
      rollback();
      toast.error("Failed to update event.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this event?")) return;
    const rollback = remove(id);
    setEditingEvent(null);
    try {
      await deleteEvent(id);
      toast.success("Event deleted.");
    } catch {
      rollback();
      toast.error("Failed to delete event.");
    }
  }

  async function handleEventDrop({ event, start, end }: { event: { id: number; resource: CalendarEvent }; start: Date; end: Date }) {
    const rollback = update(event.id, { start_time: start.toISOString(), end_time: end.toISOString() });
    try {
      await updateEvent(event.id, { start_time: start.toISOString(), end_time: end.toISOString() });
      toast.success("Event rescheduled.");
    } catch {
      rollback();
      toast.error("Failed to reschedule event.");
    }
  }

  const eventPropGetter = useCallback((event: { resource: CalendarEvent }) => {
    const now = new Date();
    const end = new Date(event.resource.end_time);
    const conflict = hasConflict(events, event.resource);
    const isPast = end < now;
    const catColor = CATEGORIES[event.resource.category as CategoryKey]?.color ?? "var(--primary)";
    
    return {
      className: cn(
        isPast    && "past-event",
        conflict  && "conflict-event font-bold",
        "custom-rbc-event"
      ),
      style: {
        background: conflict ? "var(--accent)"
          : isPast ? "rgba(255, 255, 255, 0.05)"
          : catColor,
        color: conflict ? "#fff" : (isPast ? "var(--text-muted)" : "#000"),
        borderRadius: 0,
        border: conflict ? "1px solid #fff" : "none",
        fontSize: "10px",
        fontWeight: 800,
        textTransform: "uppercase",
        letterSpacing: "0.05em",
        boxShadow: isPast ? "none" : `0 0 10px ${catColor}44`,
      },
    };
  }, [events]);

  return (
    <div className="space-y-8 pb-12 font-mono">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 pb-6 border-b border-dashed border-[var(--border-subtle)]">
        <div>
          <h1 className="text-4xl font-black text-[var(--text-primary)] uppercase tracking-tighter">Calendar</h1>
          <p className="text-xs mt-2 uppercase tracking-[0.2em] text-[var(--text-muted)]">
            // [NODE_STATUS: SYNC_READY] // ANALYZING_TEMPORAL_FLUX...
          </p>
        </div>
        <button 
          className="tech-btn tech-btn-primary px-8" 
          onClick={() => openCreateModal({ start: new Date(), end: new Date(Date.now() + 3600000) })}
        >
          <Plus className="w-4 h-4" /> Initialize Event
        </button>
      </div>

      <ErrorBoundary>
        <div className="tech-card p-4 md:p-6 bg-[var(--bg-base)] border-dashed" style={{ minHeight: 600 }}>
          {!localizerReady || loading ? (
            <Skeleton className="w-full bg-[var(--bg-elevated)]" style={{ height: 560 }} />
          ) : (
            <BigCalendar
              localizer={localizerReady}
              events={rbcEvents}
              view={view}
              onView={v => setView(v as RBCView)}
              date={date}
              onNavigate={setDate}
              selectable
              resizable
              onSelectSlot={openCreateModal}
              onSelectEvent={openEditModal}
              onEventDrop={handleEventDrop}
              eventPropGetter={eventPropGetter}
              style={{ height: 560 }}
              popup
              views={["month", "week", "day", "agenda"]}
              formats={{
                dayHeaderFormat: (d: Date) => d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" }).toUpperCase(),
              }}
            />
          )}
        </div>
      </ErrorBoundary>

      <div className="flex flex-wrap gap-6 p-4 border border-dashed border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
        {Object.entries(CATEGORIES).map(([key, { label, color }]) => (
          <div key={key} className="flex items-center gap-3">
            <div className="w-3 h-3" style={{ background: color }} />
            <span className="text-[10px] font-black uppercase tracking-widest text-[var(--text-secondary)]">{label}</span>
            <span className="text-[10px] font-bold text-[var(--text-faint)]">
              [{events.filter(e => e.category === key).length}]
            </span>
          </div>
        ))}
      </div>

      <EventModal
        isOpen={!!selectedSlot}
        title="Create Event"
        form={form}
        onFormChange={patch => setForm(f => ({ ...f, ...patch }))}
        onClose={() => setSelectedSlot(null)}
        onSubmit={handleCreate}
        saving={saving}
        conflictWarning={conflictWarning}
      />

      <EventModal
        isOpen={!!editingEvent}
        title="Edit Event"
        form={form}
        onFormChange={patch => setForm(f => ({ ...f, ...patch }))}
        onClose={() => setEditingEvent(null)}
        onSubmit={handleUpdate}
        saving={saving}
        conflictWarning={false}
        onDelete={() => editingEvent && handleDelete(editingEvent.id)}
      />
    </div>
  );
}

interface EventModalProps {
  isOpen: boolean;
  title: string;
  form: Partial<CalendarEvent>;
  onFormChange: (patch: Partial<CalendarEvent>) => void;
  onClose: () => void;
  onSubmit: (e: React.FormEvent) => void;
  saving: boolean;
  conflictWarning: boolean;
  onDelete?: () => void;
}

function EventModal({ isOpen, title, form, onFormChange, onClose, onSubmit, saving, conflictWarning, onDelete }: EventModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="absolute inset-0"
            style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(4px)" }}
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ type: "spring", damping: 28, stiffness: 300 }}
            className="relative w-full sm:max-w-lg p-8 font-mono"
            style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)", zIndex: 10, maxHeight: "90vh", overflowY: "auto" }}
          >
            <div className="flex items-center justify-between mb-8 border-b border-dashed border-[var(--border-subtle)] pb-4">
              <h2 className="text-xl font-black text-[var(--text-primary)] uppercase tracking-tighter">{title}</h2>
              <button className="p-2 border border-transparent hover:border-[var(--border-subtle)] transition-all" onClick={onClose} style={{ color: "var(--text-muted)" }}>
                <X className="w-5 h-5" />
              </button>
            </div>

            {conflictWarning && (
              <div className="flex items-center gap-3 p-4 mb-6 text-xs font-bold uppercase tracking-widest"
                style={{ background: "rgba(255,0,122,0.1)", border: "1px solid var(--accent)", color: "var(--accent)" }}>
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                SYSTEM_ALERT: Temporal Conflict Detected
              </div>
            )}

            <form onSubmit={onSubmit} className="space-y-6">
              <div>
                <label className="text-[10px] font-black uppercase tracking-widest block mb-2 text-[var(--text-muted)]">Target Title *</label>
                <input className="tech-input focus:ring-0" placeholder="ENTER EVENT IDENTIFIER" required
                  value={form.title ?? ""}
                  onChange={e => onFormChange({ title: e.target.value })} />
              </div>
              <div>
                <label className="text-[10px] font-black uppercase tracking-widest block mb-2 text-[var(--text-muted)]">Documentation</label>
                <textarea className="tech-input resize-none h-24 focus:ring-0" placeholder="ADDITIONAL_SPECIFICATIONS..."
                  value={form.description ?? ""}
                  onChange={e => onFormChange({ description: e.target.value })} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-black uppercase tracking-widest block mb-2 text-[var(--text-muted)]">Category_Class</label>
                  <select className="tech-input appearance-none bg-[var(--bg-elevated)]"
                    value={form.category ?? "meeting"}
                    onChange={e => onFormChange({ category: e.target.value as CategoryKey })}>
                    {Object.entries(CATEGORIES).map(([k, v]) => (
                      <option key={k} value={k}>{v.label.toUpperCase()}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-black uppercase tracking-widest block mb-2 text-[var(--text-muted)]">Sync_Status</label>
                  <select className="tech-input appearance-none bg-[var(--bg-elevated)]"
                    value={form.status ?? "confirmed"}
                    onChange={e => onFormChange({ status: e.target.value })}>
                    <option value="confirmed">CONFIRMED</option>
                    <option value="pending">PENDING</option>
                    <option value="canceled">CANCELED</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-black uppercase tracking-widest block mb-2 text-[var(--text-muted)]">Start_Timestamp</label>
                  <input className="tech-input" type="datetime-local"
                    value={form.start_time ? toDatetimeLocal(form.start_time) : ""}
                    onChange={e => onFormChange({ start_time: new Date(e.target.value).toISOString() })} />
                </div>
                <div>
                  <label className="text-[10px] font-black uppercase tracking-widest block mb-2 text-[var(--text-muted)]">End_Timestamp</label>
                  <input className="tech-input" type="datetime-local"
                    value={form.end_time ? toDatetimeLocal(form.end_time) : ""}
                    onChange={e => onFormChange({ end_time: new Date(e.target.value).toISOString() })} />
                </div>
              </div>
              <label className="flex items-center gap-3 cursor-pointer group">
                <input type="checkbox" className="w-4 h-4 bg-transparent border-[var(--border-subtle)] checked:bg-[var(--primary)] text-[var(--primary)] focus:ring-0 cursor-pointer"
                  checked={form.is_remote ?? false}
                  onChange={e => onFormChange({ is_remote: e.target.checked })} />
                <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)] group-hover:text-[var(--text-secondary)]">
                  <MapPin className="w-3 h-3 inline mr-1 text-[var(--primary)]" />REMOTE_PROTOCOL_ENABLED
                </span>
              </label>

              <div className="flex gap-4 pt-4">
                {onDelete && (
                  <button type="button" className="p-3 border border-[var(--accent)] text-[var(--accent)] hover:bg-[var(--accent)] hover:text-white transition-all" onClick={onDelete}>
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
                <button type="button" className="flex-1 px-6 py-3 border border-[var(--border-subtle)] text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:border-[var(--text-muted)] font-bold uppercase text-xs tracking-widest transition-all" onClick={onClose}>Abort</button>
                <button type="submit" className="flex-1 tech-btn tech-btn-primary" disabled={saving}>
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                  {saving ? "EXECUTING..." : "COMMIT_CHANGES"}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

function toDatetimeLocal(iso: string) {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
