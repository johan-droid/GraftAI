"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, Clock, MapPin, AlignLeft, Edit, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";

interface Event {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  source: string;
  description?: string;
  location?: string;
  meeting_url?: string;
}

interface EventDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  onEdit: () => void;
  event: Event | null;
}

export function EventDetailModal({ isOpen, onClose, onEdit, event }: EventDetailModalProps) {
  if (!event) return null;

  const eventTitle = event.title?.trim() || "Untitled event";

  const sourceColors = {
    google: "bg-red-500/10 border-red-500/30 text-red-600",
    microsoft: "bg-blue-500/10 border-blue-500/30 text-blue-600",
    local: "bg-emerald-500/10 border-emerald-500/30 text-emerald-600"
  };

  const sourceIcons = {
    google: "🔴",
    microsoft: "🔵",
    local: "🟢"
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
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed inset-4 sm:inset-auto sm:left-1/2 sm:top-1/2 sm:-translate-x-1/2 sm:-translate-y-1/2 sm:w-full sm:max-w-lg bg-white rounded-3xl shadow-2xl z-50 flex flex-col max-h-[90vh]"
          >
            {/* Header */}
            <div className="flex items-start justify-between p-6 border-b border-gray-100">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">{sourceIcons[event.source as keyof typeof sourceIcons]}</span>
                  <span className={cn(
                    "text-xs font-bold uppercase px-2 py-1 rounded-lg border",
                    sourceColors[event.source as keyof typeof sourceColors] || sourceColors.local
                  )}>
                    {event.source}
                  </span>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 leading-tight">
                  {eventTitle}
                </h2>
              </div>
              <button
                onClick={onClose}
                aria-label="Close event details"
                title="Close event details"
                className="p-2 hover:bg-gray-100 rounded-xl transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Date & Time */}
              <div className="flex items-start gap-4">
                <div className="p-3 bg-indigo-50 rounded-xl">
                  <Clock className="w-5 h-5 text-indigo-600" />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-semibold text-gray-500 mb-1">Date & Time</div>
                  <div className="text-base font-semibold text-gray-900">
                    {new Date(event.start_time).toLocaleDateString("en-US", {
                      weekday: "long",
                      month: "long",
                      day: "numeric",
                      year: "numeric"
                    })}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    {new Date(event.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} -{" "}
                    {new Date(event.end_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Duration: {Math.round((new Date(event.end_time).getTime() - new Date(event.start_time).getTime()) / 60000)} minutes
                  </div>
                </div>
              </div>

              {/* Location */}
              {event.location && (
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-emerald-50 rounded-xl">
                    <MapPin className="w-5 h-5 text-emerald-600" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-semibold text-gray-500 mb-1">Location</div>
                    <div className="text-base text-gray-900">{event.location}</div>
                  </div>
                </div>
              )}

              {/* Description */}
              {event.description && (
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-purple-50 rounded-xl">
                    <AlignLeft className="w-5 h-5 text-purple-600" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-semibold text-gray-500 mb-1">Description</div>
                    <div className="text-base text-gray-700 whitespace-pre-wrap">{event.description}</div>
                  </div>
                </div>
              )}

              {event.meeting_url && (
                <div className="rounded-2xl bg-slate-50 border border-slate-200 p-4">
                  <div className="text-xs font-semibold text-slate-900 uppercase tracking-[0.2em] mb-1">Meeting Link</div>
                  <a
                    href={event.meeting_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm font-medium text-slate-700 hover:text-slate-900 truncate block max-w-full"
                  >
                    {event.meeting_url}
                  </a>
                </div>
              )}

              {/* Sync Info */}
              {event.source !== "local" && (
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 space-y-3">
                  <div className="flex items-start gap-3">
                    <ExternalLink className="w-5 h-5 text-blue-600 mt-0.5" />
                    <div>
                      <div className="text-sm font-semibold text-blue-900 mb-1">
                        Synced from {event.source === "google" ? "Google Calendar" : event.source === "microsoft" ? "Microsoft Calendar" : event.source === "zoom" ? "Zoom" : "External Calendar"}
                      </div>
                      <div className="text-xs text-blue-700">
                        This event is automatically synced. Changes should be made in your {event.source} calendar.
                      </div>
                    </div>
                  </div>
                  {event.meeting_url && (
                    <div className="rounded-2xl bg-white/90 border border-blue-100 p-3">
                      <div className="text-xs font-semibold text-blue-900 uppercase tracking-[0.2em] mb-1">Meeting Link</div>
                      <a
                        href={event.meeting_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-sm font-medium text-blue-700 hover:text-blue-900 truncate block max-w-full"
                      >
                        {event.meeting_url}
                      </a>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end p-6 border-t border-gray-100 gap-3">
              <button
                onClick={onClose}
                className="px-6 py-2 rounded-xl font-semibold text-gray-700 hover:bg-gray-100 transition-colors"
              >
                Close
              </button>
              {event.source === "local" && (
                <button
                  onClick={onEdit}
                  className="flex items-center gap-2 bg-indigo-600 text-white px-6 py-2 rounded-xl font-semibold hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-500/20"
                >
                  <Edit className="w-4 h-4" />
                  Edit Event
                </button>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
