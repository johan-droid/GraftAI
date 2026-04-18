"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, Clock, MapPin, AlignLeft, Edit, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import { googleOverlayStyles } from "@/components/ui/googleOverlayStyles";

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
            className={googleOverlayStyles.backdrop}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className={cn(googleOverlayStyles.panel, "fixed inset-4 z-50 flex max-h-[90vh] flex-col sm:inset-auto sm:left-1/2 sm:top-1/2 sm:w-full sm:max-w-lg sm:-translate-x-1/2 sm:-translate-y-1/2")}
          >
            {/* Header */}
            <div className="flex items-start justify-between border-b border-[#DADCE0] p-6">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">{sourceIcons[event.source as keyof typeof sourceIcons]}</span>
                  <span className={cn(
                    "rounded-lg border px-2 py-1 text-xs font-bold uppercase",
                    sourceColors[event.source as keyof typeof sourceColors] || sourceColors.local
                  )}>
                    {event.source}
                  </span>
                </div>
                <h2 className="text-2xl font-semibold leading-tight text-[#202124]">
                  {eventTitle}
                </h2>
              </div>
              <button
                onClick={onClose}
                aria-label="Close event details"
                title="Close event details"
                className={googleOverlayStyles.iconButton + " p-2"}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Date & Time */}
              <div className="flex items-start gap-4">
                <div className="rounded-xl bg-[#E8F0FE] p-3">
                  <Clock className="w-5 h-5 text-[#1A73E8]" />
                </div>
                <div className="flex-1">
                  <div className="mb-1 text-sm font-semibold text-[#5F6368]">Date & Time</div>
                  <div className="text-base font-semibold text-[#202124]">
                    {new Date(event.start_time).toLocaleDateString("en-US", {
                      weekday: "long",
                      month: "long",
                      day: "numeric",
                      year: "numeric"
                    })}
                  </div>
                  <div className="mt-1 text-sm text-[#5F6368]">
                    {new Date(event.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} -{" "}
                    {new Date(event.end_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </div>
                  <div className="mt-1 text-xs text-[#5F6368]">
                    Duration: {Math.round((new Date(event.end_time).getTime() - new Date(event.start_time).getTime()) / 60000)} minutes
                  </div>
                </div>
              </div>

              {/* Location */}
              {event.location && (
                <div className="flex items-start gap-4">
                  <div className="rounded-xl bg-[#E6F4EA] p-3">
                    <MapPin className="w-5 h-5 text-[#1E8E3E]" />
                  </div>
                  <div className="flex-1">
                    <div className="mb-1 text-sm font-semibold text-[#5F6368]">Location</div>
                    <div className="text-base text-[#202124]">{event.location}</div>
                  </div>
                </div>
              )}

              {/* Description */}
              {event.description && (
                <div className="flex items-start gap-4">
                  <div className="rounded-xl bg-[#F3E8FD] p-3">
                    <AlignLeft className="w-5 h-5 text-[#A142F4]" />
                  </div>
                  <div className="flex-1">
                    <div className="mb-1 text-sm font-semibold text-[#5F6368]">Description</div>
                    <div className="whitespace-pre-wrap text-base text-[#3C4043]">{event.description}</div>
                  </div>
                </div>
              )}

              {event.meeting_url && (
                <div className="rounded-2xl border border-[#DADCE0] bg-[#F8F9FA] p-4">
                  <div className="mb-1 text-xs font-semibold uppercase tracking-[0.2em] text-[#202124]">Meeting Link</div>
                  <a
                    href={event.meeting_url}
                    target="_blank"
                    rel="noreferrer"
                    className="block max-w-full truncate text-sm font-medium text-[#1A73E8] hover:text-[#1558B0]"
                  >
                    {event.meeting_url}
                  </a>
                </div>
              )}

              {/* Sync Info */}
              {event.source !== "local" && (
                <div className="space-y-3 rounded-xl border border-[#D2E3FC] bg-[#F8F9FE] p-4">
                  <div className="flex items-start gap-3">
                    <ExternalLink className="mt-0.5 h-5 w-5 text-[#1A73E8]" />
                    <div>
                      <div className="mb-1 text-sm font-semibold text-[#174EA6]">
                        Synced from {event.source === "google" ? "Google Calendar" : event.source === "microsoft" ? "Microsoft Calendar" : event.source === "zoom" ? "Zoom" : "External Calendar"}
                      </div>
                      <div className="text-xs text-[#1967D2]">
                        This event is automatically synced. Changes should be made in your {event.source} calendar.
                      </div>
                    </div>
                  </div>
                  {event.meeting_url && (
                    <div className="rounded-2xl border border-[#D2E3FC] bg-white p-3">
                      <div className="mb-1 text-xs font-semibold uppercase tracking-[0.2em] text-[#174EA6]">Meeting Link</div>
                      <a
                        href={event.meeting_url}
                        target="_blank"
                        rel="noreferrer"
                        className="block max-w-full truncate text-sm font-medium text-[#1A73E8] hover:text-[#1558B0]"
                      >
                        {event.meeting_url}
                      </a>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 border-t border-[#DADCE0] p-6">
              <button
                onClick={onClose}
                className={googleOverlayStyles.secondaryButton + " px-6 py-2"}
              >
                Close
              </button>
              {event.source === "local" && (
                <button
                  onClick={onEdit}
                  className={googleOverlayStyles.primaryButton + " flex items-center gap-2 px-6 py-2"}
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
