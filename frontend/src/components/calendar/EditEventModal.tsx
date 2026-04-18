import React from "react";
import { motion } from "framer-motion";
import { X, Edit3, Trash2, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { googleOverlayStyles } from "@/components/ui/googleOverlayStyles";
import { FormControl, InputLabel, MenuItem, Select } from "@mui/material";

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
        className={googleOverlayStyles.backdrop}
        onClick={onClose}
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className={cn(googleOverlayStyles.panel, "relative z-10 max-w-md p-6")}
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="flex items-center gap-2 text-base font-semibold text-[#202124]">
            <Edit3 className="w-4 h-4 text-[#1A73E8]" /> Edit event
          </h3>
          <button onClick={onClose} aria-label="Close" className={googleOverlayStyles.iconButton + " p-2"}>
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={onUpdate} className="space-y-4">
          <div>
            <label htmlFor="edit-event-title" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-[#5F6368]">Title</label>
            <input
              id="edit-event-title"
              type="text"
              value={event.title}
              onChange={(e) => setEditingEvent({ ...event, title: e.target.value })}
              className={googleOverlayStyles.field}
            />
          </div>
          <div>
            <label htmlFor="edit-event-description" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-[#5F6368]">Description</label>
            <textarea
              id="edit-event-description"
              rows={3}
              value={event.description}
              onChange={(e) => setEditingEvent({ ...event, description: e.target.value })}
              className={googleOverlayStyles.field + " resize-none"}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="edit-event-status" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-[#5F6368]">Status</label>
              <FormControl fullWidth>
                <InputLabel id="edit-event-status-label">Status</InputLabel>
                <Select
                  labelId="edit-event-status-label"
                  id="edit-event-status"
                  value={event.status}
                  label="Status"
                  onChange={(e) => setEditingEvent({ ...event, status: e.target.value })}
                >
                  <MenuItem value="confirmed">Confirmed</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="canceled">Canceled</MenuItem>
                </Select>
              </FormControl>
            </div>
            <div>
              <label htmlFor="edit-event-category" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-[#5F6368]">Category</label>
              <FormControl fullWidth>
                <InputLabel id="edit-event-category-label">Category</InputLabel>
                <Select
                  labelId="edit-event-category-label"
                  id="edit-event-category"
                  value={event.category}
                  label="Category"
                  onChange={(e) => setEditingEvent({ ...event, category: e.target.value })}
                >
                  {Object.keys(categories).map((c) => (
                    <MenuItem key={c} value={c}>{c}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              aria-label="Delete event"
              onClick={() => onDelete(event.id)}
              className={googleOverlayStyles.dangerButton + " p-2.5"}
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={onClose}
              className={googleOverlayStyles.secondaryButton + " flex-1 py-2.5"}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={googleOverlayStyles.primaryButton + " flex-1 py-2.5 gap-2"}
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
