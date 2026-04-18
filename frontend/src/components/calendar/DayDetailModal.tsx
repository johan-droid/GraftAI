import React from "react";
import { motion } from "framer-motion";
import { X, Calendar, Clock, Edit3, Trash2, Plus, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { googleOverlayStyles } from "@/components/ui/googleOverlayStyles";

interface CalendarEventSummary {
  id: string | number;
  title: string;
  start_time: string;
  end_time: string;
  description?: string;
  location?: string;
  category?: string;
}

interface DayDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedDate: Date | null;
  dayEvents: CalendarEventSummary[];
  categories: Record<string, { bg?: string; text?: string; dot?: string }>;
  draftEvent: {
    title: string;
    description?: string;
    start_time_local?: string;
    end_time_local?: string;
  };
  setDraftEvent: (draft: {
    title: string;
    description?: string;
    start_time_local?: string;
    end_time_local?: string;
  }) => void;
  handleCreate: (e?: React.FormEvent) => void;
  handleDelete: (id: string | number) => void;
  setEditingEvent: (event: {
    id: string | number;
    title: string;
    description?: string;
    status?: string;
    category?: string;
  }) => void;
  creating: boolean;
}

const DayDetailModal = ({
  isOpen,
  onClose,
  selectedDate,
  dayEvents,
  categories,
  draftEvent,
  setDraftEvent,
  handleCreate,
  handleDelete,
  setEditingEvent,
  creating
}: DayDetailModalProps) => {
  if (!isOpen || !selectedDate) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className={googleOverlayStyles.backdrop}
        onClick={onClose}
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 16 }}
        transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
        className={cn(googleOverlayStyles.panel, "relative z-10 max-w-lg overflow-hidden")}
      >
        <div className="flex items-center justify-between border-b border-[#DADCE0] px-6 py-4">
          <div>
            <h3 className="text-base font-semibold text-[#202124]">
              {selectedDate.toLocaleDateString("en-US", {
                weekday: "long",
                month: "long",
                day: "numeric",
              })}
            </h3>
            <p className="mt-0.5 text-xs text-[#5F6368]">{dayEvents.length} events</p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close day details"
            title="Close day details"
            className={googleOverlayStyles.iconButton + " p-2"}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="max-h-[60vh] space-y-4 overflow-y-auto p-4">
          <form onSubmit={handleCreate} className="space-y-4">
            <div className={googleOverlayStyles.section + " space-y-3"}>
              <h4 className={googleOverlayStyles.sectionTitle}>Create event</h4>
              <div className="grid gap-3">
                <input
                  value={draftEvent.title}
                  onChange={(e) => setDraftEvent({ ...draftEvent, title: e.target.value })}
                  placeholder="Event title"
                  className={googleOverlayStyles.field}
                />
                <textarea
                  rows={3}
                  value={draftEvent.description}
                  onChange={(e) => setDraftEvent({ ...draftEvent, description: e.target.value })}
                  placeholder="Agenda / description"
                  className={googleOverlayStyles.field + " resize-none"}
                />
                <div className="grid grid-cols-2 gap-3">
                  <label className="space-y-1 text-[11px] text-[#5F6368]">
                    Start
                    <input
                      type="datetime-local"
                      value={draftEvent.start_time_local}
                      onChange={(e) => setDraftEvent({ ...draftEvent, start_time_local: e.target.value })}
                      className={googleOverlayStyles.fieldMuted}
                    />
                  </label>
                  <label className="space-y-1 text-[11px] text-[#5F6368]">
                    End
                    <input
                      type="datetime-local"
                      value={draftEvent.end_time_local}
                      onChange={(e) => setDraftEvent({ ...draftEvent, end_time_local: e.target.value })}
                      className={googleOverlayStyles.fieldMuted}
                    />
                  </label>
                </div>
              </div>
            </div>
          </form>

          {dayEvents.length === 0 ? (
            <div className="text-center py-10">
              <Calendar className="mx-auto mb-3 h-10 w-10 text-[#BDC1C6]" />
              <p className="text-sm text-[#5F6368]">No events for this day</p>
            </div>
          ) : (
            dayEvents.map((ev) => (
              <div
                key={ev.id}
                className="group flex items-start gap-3 rounded-2xl border border-[#DADCE0] bg-white p-3 transition-all hover:border-[#BDC1C6]"
              >
                <div className={`w-1 h-full min-h-[40px] rounded-full shrink-0 ${categories[ev.category ?? "event"]?.dot ?? "bg-slate-400"}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-[#202124]">{ev.title?.trim() || "Untitled event"}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="flex items-center gap-1 text-[11px] text-[#5F6368]">
                      <Clock className="w-3 h-3" />
                      {new Date(ev.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                    <span className={cn("rounded border px-1.5 py-0.5 text-[10px] font-bold", categories[ev.category ?? "event"]?.bg, categories[ev.category ?? "event"]?.text)}>
                      {ev.category || "general"}
                    </span>
                  </div>
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => setEditingEvent(ev)}
                    aria-label={`Edit ${ev.title?.trim() || "event"}`}
                    title="Edit event"
                    className={googleOverlayStyles.iconButton + " p-1.5"}
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => handleDelete(ev.id)}
                    aria-label={`Delete ${ev.title?.trim() || "event"}`}
                    title="Delete event"
                    className="rounded-md p-1.5 text-[#5F6368] transition-all hover:bg-[#FDE7E9] hover:text-[#D93025]"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="flex justify-between border-t border-[#DADCE0] px-4 py-3">
          <button
            onClick={() => handleCreate()}
            disabled={creating}
            className={googleOverlayStyles.secondaryButton + " flex items-center gap-2 px-4 py-2"}
          >
            {creating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
            Add event
          </button>
          <button onClick={onClose} className={googleOverlayStyles.primaryButton + " px-4 py-2"}>
            Done
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default DayDetailModal;
