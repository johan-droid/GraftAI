"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Calendar, Clock, MapPin, AlignLeft, Save, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface Event {
  id?: string;
  title: string;
  start_time: string;
  end_time: string;
  description?: string;
  location?: string;
  source?: string;
  meeting_url?: string;
  is_meeting?: boolean;
  meeting_provider?: string;
  attendees?: string[];
}

interface EventModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (event: Event) => Promise<void>;
  onDelete?: (eventId: string) => Promise<void>;
  event?: Event | null;
  initialDate?: Date;
  availableProviders: string[];
  integrationLoading: boolean;
}

export function EventModal({ isOpen, onClose, onSave, onDelete, event, initialDate, availableProviders, integrationLoading }: EventModalProps) {
  const [formData, setFormData] = useState<Event>({
    title: "",
    start_time: "",
    end_time: "",
    description: "",
    location: "",
    is_meeting: false,
    meeting_provider: "",
    attendees: []
  });
  const [attendeesText, setAttendeesText] = useState("");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    const defaultProvider = availableProviders[0] || "";
    if (event) {
      setFormData({
        title: event.title,
        start_time: new Date(event.start_time).toISOString().slice(0, 16),
        end_time: new Date(event.end_time).toISOString().slice(0, 16),
        description: event.description || "",
        location: event.location || "",
        is_meeting: !!event.meeting_url,
        meeting_provider: event.source || defaultProvider,
        attendees: event.attendees || []
      });
      setAttendeesText((event.attendees || []).join(", "));
    } else if (initialDate) {
      const start = new Date(initialDate);
      start.setHours(9, 0, 0, 0);
      const end = new Date(start);
      end.setHours(10, 0, 0, 0);
      setFormData({
        title: "",
        start_time: start.toISOString().slice(0, 16),
        end_time: end.toISOString().slice(0, 16),
        description: "",
        location: "",
        is_meeting: false,
        meeting_provider: defaultProvider,
        attendees: []
      });
      setAttendeesText("");
    } else {
      setFormData((current) => ({
        ...current,
        is_meeting: false,
        meeting_provider: defaultProvider,
        attendees: []
      }));
      setAttendeesText("");
    }
  }, [event, initialDate, isOpen, availableProviders]);

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!formData.title.trim()) newErrors.title = "Title is required";
    if (!formData.start_time) newErrors.start_time = "Start time is required";
    if (!formData.end_time) newErrors.end_time = "End time is required";
    if (new Date(formData.end_time) <= new Date(formData.start_time)) {
      newErrors.end_time = "End time must be after start time";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      const payload: Event = {
        ...formData,
        id: event?.id,
        start_time: new Date(formData.start_time).toISOString(),
        end_time: new Date(formData.end_time).toISOString(),
        attendees: attendeesText
          .split(",")
          .map((attendee) => attendee.trim())
          .filter(Boolean),
      };

      if (!payload.is_meeting) {
        delete payload.meeting_provider;
        delete payload.attendees;
      }

      await onSave(payload);
      onClose();
    } catch (error) {
      console.error("Failed to save event:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!event?.id || !onDelete) return;
    if (!confirm("Are you sure you want to delete this event?")) return;

    setLoading(true);
    try {
      await onDelete(event.id);
      onClose();
    } catch (error) {
      console.error("Failed to delete event:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/30 z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.98, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98, y: 12 }}
            className="fixed inset-4 sm:inset-auto sm:left-1/2 sm:top-1/2 sm:-translate-x-1/2 sm:-translate-y-1/2 sm:w-full sm:max-w-lg bg-[var(--bg-card)] rounded-lg shadow-sm z-50 flex flex-col max-h-[90vh]"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-[var(--border-subtle)]">
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                {event ? "Edit Event" : "Create Event"}
              </h2>
              <button
                onClick={onClose}
                className="p-2 hover:bg-transparent rounded-md transition-colors"
                aria-label="Close event modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-4 space-y-4">
              {/* Title */}
              <div>
                <label htmlFor="event-title" className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-2">
                  <Calendar className="w-4 h-4" />
                  Event Title
                </label>
                <input
                  id="event-title"
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className={cn(
                    "w-full px-3 py-2 rounded-md border transition-colors focus:outline-none focus:ring-0",
                    errors.title ? "border-red-300" : "border-gray-200"
                  )}
                  placeholder="Team meeting, Lunch with client..."
                  disabled={loading}
                />
                {errors.title && <p className="text-red-500 text-xs mt-1">{errors.title}</p>}
              </div>

              {/* Start Time */}
              <div>
                <label htmlFor="event-start" className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-2">
                  <Clock className="w-4 h-4" />
                  Start Time
                </label>
                <input
                  id="event-start"
                  type="datetime-local"
                  value={formData.start_time}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                  className={cn(
                    "w-full px-3 py-2 rounded-md border transition-colors focus:outline-none focus:ring-0",
                    errors.start_time ? "border-red-300" : "border-gray-200"
                  )}
                  disabled={loading}
                />
                {errors.start_time && <p className="text-red-500 text-xs mt-1">{errors.start_time}</p>}
              </div>

              {/* End Time */}
              <div>
                <label htmlFor="event-end" className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-2">
                  <Clock className="w-4 h-4" />
                  End Time
                </label>
                <input
                  id="event-end"
                  type="datetime-local"
                  value={formData.end_time}
                  onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                  className={cn(
                    "w-full px-3 py-2 rounded-md border transition-colors focus:outline-none focus:ring-0",
                    errors.end_time ? "border-red-300" : "border-gray-200"
                  )}
                  disabled={loading}
                />
                {errors.end_time && <p className="text-red-500 text-xs mt-1">{errors.end_time}</p>}
              </div>

              {/* Location */}
              <div>
                <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-2">
                  <MapPin className="w-4 h-4" />
                  Location (Optional)
                </label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="w-full px-3 py-2 rounded-md border border-gray-200 transition-colors focus:outline-none focus:ring-0"
                  placeholder="Conference Room A, Zoom link..."
                  disabled={loading}
                />
              </div>

              {/* Meeting Link */}
              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center justify-between gap-3 mb-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-900">Create a meeting link</p>
                    <p className="text-sm text-slate-500">Use a connected calendar provider to generate Google Meet or Teams links.</p>
                  </div>
                  <label className="inline-flex items-center gap-2 text-sm font-medium text-slate-700">
                    <input
                      type="checkbox"
                      checked={formData.is_meeting}
                      onChange={(e) => setFormData({ ...formData, is_meeting: e.target.checked })}
                      disabled={loading || integrationLoading}
                      className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    Enable
                  </label>
                </div>

                {formData.is_meeting && (
                  <div className="space-y-4">
                    {availableProviders.length ? (
                      <div>
                        <div className="text-sm font-semibold text-slate-700 mb-2">Meeting Provider</div>
                        <div className="grid gap-2 sm:grid-cols-2">
                              {availableProviders.map((provider) => (
                                <label key={provider} className="inline-flex items-center gap-3 rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-700 hover:border-slate-300 transition-colors">
                              <input
                                type="radio"
                                name="meeting_provider"
                                value={provider}
                                checked={formData.meeting_provider === provider}
                                onChange={(e) => setFormData({ ...formData, meeting_provider: e.target.value })}
                                disabled={loading}
                                className="h-4 w-4 text-indigo-600 border-gray-300 focus:ring-indigo-500"
                              />
                              <span className="font-medium capitalize">{provider}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                        Connect Google or Microsoft under Settings &gt; Integrations to generate a real meeting link.
                      </div>
                    )}

                    <div>
                      <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-2">
                        <span>Attendees</span>
                      </label>
                      <input
                        type="text"
                        value={attendeesText}
                        onChange={(e) => setAttendeesText(e.target.value)}
                        className="w-full px-3 py-2 rounded-md border border-gray-200 transition-colors focus:outline-none focus:ring-0"
                        placeholder="Attendee emails, separated by commas"
                        disabled={loading}
                      />
                      <p className="text-xs text-slate-500 mt-1">Optional; used only when generating a meeting link.</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Description */}
              <div>
                <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-2">
                  <AlignLeft className="w-4 h-4" />
                  Description (Optional)
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={4}
                  className="w-full px-3 py-2 rounded-md border border-gray-200 transition-colors focus:outline-none focus:ring-0 resize-none"
                  placeholder="Add notes, agenda, or details..."
                  disabled={loading}
                />
              </div>

              {event?.source && event.source !== "local" && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                  <p className="text-sm text-amber-800">
                    <strong>Note:</strong> This event is synced from {event.source}. Changes may be overwritten on next sync.
                  </p>
                </div>
              )}
            </form>

            {/* Footer */}
            <div className="flex items-center justify-between p-4 border-t border-[var(--border-subtle)] gap-3">
              {event && onDelete && event.source === "local" ? (
                <button
                  type="button"
                  onClick={handleDelete}
                  disabled={loading}
                  className="flex items-center gap-2 px-3 py-1 rounded-md font-semibold text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              ) : (
                <div />
              )}
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={loading}
                  className="px-4 py-2 rounded-md font-semibold text-gray-700 hover:bg-gray-100 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className="flex items-center gap-2 bg-[var(--primary)] text-white px-4 py-2 rounded-md font-semibold hover:brightness-95 transition-colors disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  {loading ? "Saving..." : "Save"}
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
