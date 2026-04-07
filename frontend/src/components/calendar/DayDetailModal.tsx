import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Calendar, Clock, Edit3, Trash2, Video, Plus, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface DayDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedDate: Date | null;
  dayEvents: any[];
  categories: any;
  draftEvent: any;
  setDraftEvent: (draft: any) => void;
  handleCreate: (e?: React.FormEvent) => void;
  handleDelete: (id: string | number) => void;
  setEditingEvent: (event: any) => void;
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
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
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
            <p className="text-xs text-slate-500 mt-0.5">{dayEvents.length} events</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/8 text-slate-500 hover:text-white transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-4 max-h-[60vh] overflow-y-auto space-y-4">
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="space-y-3 rounded-2xl border border-white/10 bg-white/5 p-4">
              <h4 className="text-sm font-semibold text-white">Create event</h4>
              <div className="grid gap-3">
                <input
                  value={draftEvent.title}
                  onChange={(e) => setDraftEvent({ ...draftEvent, title: e.target.value })}
                  placeholder="Event title"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-indigo-500/60"
                />
                <textarea
                  rows={3}
                  value={draftEvent.description}
                  onChange={(e) => setDraftEvent({ ...draftEvent, description: e.target.value })}
                  placeholder="Agenda / description"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-indigo-500/60 resize-none"
                />
                <div className="grid grid-cols-2 gap-3">
                  <label className="space-y-1 text-[11px] text-slate-400">
                    Start
                    <input
                      type="datetime-local"
                      value={draftEvent.start_time_local}
                      onChange={(e) => setDraftEvent({ ...draftEvent, start_time_local: e.target.value })}
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-2 py-2 text-sm text-white"
                    />
                  </label>
                  <label className="space-y-1 text-[11px] text-slate-400">
                    End
                    <input
                      type="datetime-local"
                      value={draftEvent.end_time_local}
                      onChange={(e) => setDraftEvent({ ...draftEvent, end_time_local: e.target.value })}
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-2 py-2 text-sm text-white"
                    />
                  </label>
                </div>
              </div>
            </div>
          </form>

          {dayEvents.length === 0 ? (
            <div className="text-center py-10">
              <Calendar className="w-10 h-10 text-slate-700 mx-auto mb-3" />
              <p className="text-slate-500 text-sm">No events for this day</p>
            </div>
          ) : (
            dayEvents.map((ev) => (
              <div
                key={ev.id}
                className="group flex items-start gap-3 p-3 rounded-xl border border-white/[0.06] bg-white/[0.025] hover:border-white/10 transition-all"
              >
                <div className={`w-1 h-full min-h-[40px] rounded-full shrink-0 ${categories[ev.category]?.dot ?? "bg-slate-400"}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-white">{ev.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="flex items-center gap-1 text-[11px] text-slate-500">
                      <Clock className="w-3 h-3" />
                      {new Date(ev.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                    <span className={cn("text-[10px] font-bold px-1.5 py-0.5 rounded border", categories[ev.category]?.bg, categories[ev.category]?.text)}>
                      {ev.category}
                    </span>
                  </div>
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={() => setEditingEvent(ev)} className="p-1.5 rounded-md hover:bg-white/10 text-slate-500 hover:text-white transition-all">
                    <Edit3 className="w-3.5 h-3.5" />
                  </button>
                  <button onClick={() => handleDelete(ev.id)} className="p-1.5 rounded-md hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-all">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="px-4 py-3 border-t border-white/[0.07] flex justify-between">
          <button
            onClick={() => handleCreate()}
            disabled={creating}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 hover:text-white text-sm font-medium transition-all disabled:opacity-50"
          >
            {creating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
            Add event
          </button>
          <button onClick={onClose} className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-all">
            Done
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default DayDetailModal;
