import React from "react";
import { motion } from "framer-motion";
import { X, Edit3, Trash2, CheckCircle2 } from "lucide-react";

interface EventPayload {
  id: string | number;
  title: string;
  description?: string;
  status: string;
  category: string;
}

interface EditEventModalProps {
  event: EventPayload;
  onClose: () => void;
  onUpdate: (e: React.FormEvent) => void;
  onDelete: (id: string | number) => void;
  setEditingEvent: (event: EventPayload) => void;
  categories: Record<string, string>;
}

const EditEventModal = ({
  event,
  onClose,
  onUpdate,
  onDelete,
  setEditingEvent,
  categories
}: EditEventModalProps) => {
  if (!event) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
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
          <button onClick={onClose} aria-label="Close" className="p-1.5 rounded-lg hover:bg-white/8 text-slate-500 hover:text-white transition-all">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={onUpdate} className="space-y-4">
          <div>
            <label htmlFor="edit-event-title" className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5 block">Title</label>
            <input
              id="edit-event-title"
              type="text"
              value={event.title}
              onChange={(e) => setEditingEvent({ ...event, title: e.target.value })}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:border-indigo-500/60"
            />
          </div>
          <div>
            <label htmlFor="edit-event-description" className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5 block">Description</label>
            <textarea
              id="edit-event-description"
              rows={3}
              value={event.description}
              onChange={(e) => setEditingEvent({ ...event, description: e.target.value })}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:border-indigo-500/60 resize-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="edit-event-status" className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5 block">Status</label>
              <select
                id="edit-event-status"
                value={event.status}
                onChange={(e) => setEditingEvent({ ...event, status: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-3 text-sm text-white"
              >
                <option value="confirmed">Confirmed</option>
                <option value="pending">Pending</option>
                <option value="canceled">Canceled</option>
              </select>
            </div>
            <div>
              <label htmlFor="edit-event-category" className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5 block">Category</label>
              <select
                id="edit-event-category"
                value={event.category}
                onChange={(e) => setEditingEvent({ ...event, category: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-3 text-sm text-white"
              >
                {Object.keys(categories).map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              aria-label="Delete event"
              onClick={() => onDelete(event.id)}
              className="p-2.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 transition-all"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={onClose}
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
  );
};

export default EditEventModal;
