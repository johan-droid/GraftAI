"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import { manualSync, getProactiveSuggestion, ProactiveSuggestionResponse } from "@/lib/api";
import { useAuth } from "@/providers/auth-provider";
import { RefreshCcw, CheckCircle2, AlertCircle, Calendar, Sparkles } from "lucide-react";
import { CalendarView } from "@/components/calendar/CalendarView";
import { EventModal } from "@/components/calendar/EventModal";
import { EventDetailModal } from "@/components/calendar/EventDetailModal";
import { SmartActions } from "@/components/dashboard/SmartActions";
import type { SmartAction } from "@/components/dashboard/SmartActions";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent } from "@/components/ui/Card";

interface Event {
  id?: string;
  title: string;
  start_time: string;
  end_time: string;
  source?: string;
  description?: string;
  location?: string;
  meeting_url?: string;
  is_meeting?: boolean;
  meeting_provider?: string;
  attendees?: string[];
}

export default function CalendarPage() {
  useAuth();
  const [events, setEvents] = useState<Event[]>([]);
  const [activeProviders, setActiveProviders] = useState<string[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [integrationLoading, setIntegrationLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [isEventModalOpen, setIsEventModalOpen] = useState(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [syncStatus, setSyncStatus] = useState<"idle" | "success" | "error">("idle");
  const [suggestion, setSuggestion] = useState<ProactiveSuggestionResponse | null>(null);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const start = new Date();
      start.setMonth(start.getMonth() - 1);
      const end = new Date();
      end.setMonth(end.getMonth() + 2);

      const [eventsData, suggestionData] = await Promise.all([
        apiClient.fetch(`/calendar/events?start=${start.toISOString()}&end=${end.toISOString()}`),
        getProactiveSuggestion("User is looking at their calendar. Provide daily and weekly schedule optimization suggestions.")
      ]);
      setEvents(eventsData);
      setSuggestion(suggestionData);
    } catch (error) {
      console.error("Failed to load events", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
    fetchIntegrations();
  }, []);

  const handleSync = async () => {
    setIsSyncing(true);
    setSyncMessage(null);
    setSyncStatus("idle");
    try {
      const result = await manualSync();
      await fetchEvents();
      setSyncStatus("success");
      setSyncMessage(result.message || "Calendar sync completed.");
    } catch (error) {
      console.error("Sync failed", error);
      setSyncStatus("error");
      setSyncMessage(error instanceof Error ? error.message : "Sync failed.");
    } finally {
      setIsSyncing(false);
      window.setTimeout(() => {
        setSyncStatus("idle");
        setSyncMessage(null);
      }, 6000);
    }
  };

  const fetchIntegrations = async () => {
    setIntegrationLoading(true);
    try {
      const data = await apiClient.fetch("/users/me/integrations");
      setActiveProviders(data.active_providers || []);
    } catch (error) {
      console.error("Failed to load integration status", error);
    } finally {
      setIntegrationLoading(false);
    }
  };

  const handleCreateEvent = async (eventData: Event) => {
    try {
      if (eventData.id) {
        await apiClient.patch(`/calendar/events/${eventData.id}`, eventData);
      } else {
        await apiClient.post("/calendar/events", eventData);
      }
      await fetchEvents();
    } catch (error) {
      console.error("Failed to save event", error);
      throw error;
    }
  };

  const handleDeleteEvent = async (eventId: string) => {
    try {
      await apiClient.delete(`/calendar/events/${eventId}`);
      await fetchEvents();
    } catch (error) {
      console.error("Failed to delete event", error);
      throw error;
    }
  };

  const handleEventClick = (event: Event) => {
    setSelectedEvent(event);
    setIsDetailModalOpen(true);
  };

  const handleDateClick = (date: Date) => {
    setSelectedDate(date);
    setSelectedEvent(null);
    setIsEventModalOpen(true);
  };

  const handleEditFromDetail = () => {
    setIsDetailModalOpen(false);
    setIsEventModalOpen(true);
  };

  const handleExecuteSmartAction = async (action: SmartAction) => {
    // Perform AI action for daily/weekly optimization
    console.log("Triggered Smart Action on Calendar:", action);
  };

  return (
    <motion.div
      className="p-6 max-w-[1600px] mx-auto space-y-6"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-6 mb-2">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Calendar</h1>
          <div className="flex flex-wrap items-center gap-3 mt-3">
            <Badge variant="outline" className="text-muted-foreground"><span className="text-foreground font-medium mr-1.5">{events.length}</span> Total</Badge>
            <Badge variant="secondary" className="bg-red-500/10 text-red-500 hover:bg-red-500/20"><span className="font-medium mr-1.5">{events.filter(e => e.source === "google").length}</span> Google</Badge>
            <Badge variant="secondary" className="bg-blue-500/10 text-blue-500 hover:bg-blue-500/20"><span className="font-medium mr-1.5">{events.filter(e => e.source === "microsoft").length}</span> Microsoft</Badge>
            <Badge variant="secondary" className="bg-violet-500/10 text-violet-500 hover:bg-violet-500/20"><span className="font-medium mr-1.5">{events.filter(e => e.source === "zoom").length}</span> Zoom</Badge>
            <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20"><span className="font-medium mr-1.5">{events.filter(e => e.source === "local").length}</span> Local</Badge>
          </div>
        </div>

        <div className="flex items-center gap-4 w-full sm:w-auto">
          <AnimatePresence mode="wait">
            {syncStatus === "success" && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="flex items-center gap-2 text-emerald-500 text-sm font-medium bg-emerald-500/10 px-3 py-1.5 rounded-md"
              >
                <CheckCircle2 className="w-4 h-4" />
                Synced!
              </motion.div>
            )}
            {syncStatus === "error" && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="flex items-center gap-2 text-red-500 text-sm font-medium bg-red-500/10 px-3 py-1.5 rounded-md"
              >
                <AlertCircle className="w-4 h-4" />
                Sync failed
              </motion.div>
            )}
          </AnimatePresence>

          <Button
            onClick={handleSync}
            disabled={isSyncing}
            variant="outline"
          >
            <RefreshCcw className={`mr-2 h-4 w-4 ${isSyncing ? 'animate-spin text-primary' : ''}`} />
            {isSyncing ? "Syncing..." : "Sync"}
          </Button>
        </div>
      </div>

      {suggestion?.smart_actions && suggestion.smart_actions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full"
        >
          <Card className="border-indigo-500/20 bg-indigo-500/5">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2 text-indigo-500 font-medium text-sm">
                <Sparkles className="w-4 h-4" />
                AI Schedule Optimization
              </div>
              <p className="text-sm text-muted-foreground mb-4">{suggestion.suggestion}</p>
              <SmartActions 
                actions={suggestion.smart_actions} 
                onExecute={handleExecuteSmartAction} 
              />
            </CardContent>
          </Card>
        </motion.div>
      )}

      {syncMessage && (
        <Card className="bg-muted/50 border-primary/20">
          <CardContent className="p-4 text-sm text-muted-foreground flex items-center gap-2">
            <Calendar className="h-4 w-4 text-primary" />
            {syncMessage}
          </CardContent>
        </Card>
      )}

      {/* Calendar */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-32 rounded-xl border border-dashed bg-card/50">
          <div className="w-8 h-8 border-2 border-primary/20 border-t-primary rounded-full animate-spin mb-4" />
          <p className="font-medium text-sm text-muted-foreground">Loading Calendar View...</p>
        </div>
      ) : (
        <motion.div 
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
          className="rounded-xl overflow-hidden shadow-sm ring-1 ring-border/50"
        >
          <CalendarView
            events={events}
            onEventClick={handleEventClick}
            onDateClick={handleDateClick}
            onCreateEvent={() => {
              setSelectedEvent(null);
              setSelectedDate(null);
              setIsEventModalOpen(true);
            }}
          />
        </motion.div>
      )}

      {/* Modals */}
      <EventModal
        isOpen={isEventModalOpen}
        onClose={() => {
          setIsEventModalOpen(false);
          setSelectedEvent(null);
          setSelectedDate(null);
        }}
        onSave={handleCreateEvent}
        onDelete={handleDeleteEvent}
        event={selectedEvent}
        initialDate={selectedDate || undefined}
        availableProviders={activeProviders}
        integrationLoading={integrationLoading}
      />

      <EventDetailModal
        isOpen={isDetailModalOpen}
        onClose={() => {
          setIsDetailModalOpen(false);
          setSelectedEvent(null);
        }}
        onEdit={handleEditFromDetail}
        event={selectedEvent}
      />
    </motion.div>
  );
}
