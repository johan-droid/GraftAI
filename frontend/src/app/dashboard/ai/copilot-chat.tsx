"use client";

import { useState, useRef, useEffect, FormEvent, KeyboardEvent, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  Sparkles,
  Loader2,
  Calendar,
  CheckCircle2,
  Lightbulb,
  RefreshCw,
  MoreHorizontal,
  Sun,
  Moon,
  Cloud,
  Clock,
  Zap,
  BarChart3,
  ArrowUp,
  CloudOff,
  Wifi,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { sendAiChat, getEvents } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

import { useAuth } from "@/app/providers/auth-provider";

import { useSyncEngine } from "@/hooks/useSyncEngine";
import { db } from "@/lib/db";
import styles from "./copilot-chat.module.css";

interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
  timestamp: Date;
  contextUsed?: string[];
  suggestedActions?: SuggestedAction[];
  metadata?: {
    eventModified?: boolean;
    eventCreated?: boolean;
    eventDeleted?: boolean;
  };
}

interface SuggestedAction {
  id: string;
  type: "schedule" | "update" | "delete" | "query";
  label: string;
  description: string;
  icon?: "calendar" | "lightbulb" | "chart" | "zap" | "clock";
  data?: Record<string, unknown>;
}

interface CalendarEvent {
  id: string | number;
  title: string;
  start_time: string;
  end_time: string;
  category: string;
  status: string;
}

const formatEventTime = (isoDate: string) =>
  new Date(isoDate).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

const normalizeEventTitle = (title?: string) => {
  const normalized = title?.trim();
  return normalized ? normalized : "Untitled event";
};

const getTimeEmoji = (hour: number) => {
  if (hour < 6) return "🌙";
  if (hour < 12) return "☀️";
  if (hour < 17) return "🌤️";
  if (hour < 20) return "🌇";
  return "🌙";
};

const getSuggestionIcon = (iconName?: string) => {
  switch (iconName) {
    case "calendar": return <Calendar className="h-4 w-4" />;
    case "chart": return <BarChart3 className="h-4 w-4" />;
    case "zap": return <Zap className="h-4 w-4" />;
    case "clock": return <Clock className="h-4 w-4" />;
    default: return <Lightbulb className="h-4 w-4" />;
  }
};

const buildCalendarAwareSuggestions = (events: CalendarEvent[]): SuggestedAction[] => {
  const suggestions: SuggestedAction[] = [];
  
  // Sort events by time
  const sorted = [...events].sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());
  
  const now = new Date();
  let lastEnd = now;

  // 1. DASHBOARD INTELLIGENCE: Find gaps in the user's schedule for precision suggestions
  for (const event of sorted) {
    const start = new Date(event.start_time);
    const end = new Date(event.end_time);
    const eventTitle = normalizeEventTitle(event.title);
    
    // Check if there's a gap before this event starting from now (or last event)
    if (start > lastEnd) {
      const diffMs = start.getTime() - lastEnd.getTime();
      const diffMin = Math.floor(diffMs / (1000 * 60));

      if (diffMin >= 30 && diffMin < 240) { // Found a meaningful slot (30m - 4hrs)
        const startTimeStr = lastEnd.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        suggestions.push({
          id: `gap-${start.getTime()}`,
          type: "query",
          label: "Book focus session",
          description: `You're free until ${eventTitle} (${startTimeStr}). Want to block focus time?`,
          icon: "zap",
          data: { 
            prompt: `I have a ${diffMin} minute gap before "${eventTitle}". Help me schedule a focused work session starting at ${startTimeStr}.` 
          },
        });
      }
    }
    // Update lastEnd to the end of the current event if it's later than our current tracking
    if (end > lastEnd) lastEnd = end;
  }

  // 2. Fallback to standard high-value actions if needed
  const nextEvent = sorted.find(e => new Date(e.start_time) > now);
  if (nextEvent) {
    const nextEventTime = formatEventTime(nextEvent.start_time);
    const nextEventTitle = normalizeEventTitle(nextEvent.title);
    suggestions.push({
      id: "prep-next-event",
      type: "query",
      label: `Prep for ${nextEventTitle}`,
      description: `Generate a checklist for your ${nextEventTime} meeting`,
      icon: "zap",
      data: {
        prompt: `Give me a concise prep checklist for "${nextEventTitle}" at ${nextEventTime}.`,
      },
    });
  }

  suggestions.push(
    {
      id: "show-today-plan",
      type: "query",
      label: "Show today's plan",
      description: "Get a structured timeline for today",
      icon: "clock",
      data: { prompt: "Summarize my day in timeline format with recommended priorities." },
    },
    {
      id: "schedule-with-agenda",
      type: "query",
      label: "Schedule with agenda",
      description: "Set up a structured meeting with goal points",
      icon: "calendar",
      data: { prompt: "Schedule a 30m sync on Google Meet for tomorrow at 3pm. Agenda: 1. Goal alignment, 2. Roadmap review." },
    }
  );

  const dedupedByLabel = suggestions.filter(
    (item, index, arr) => arr.findIndex((candidate) => candidate.label === item.label) === index
  );

  return dedupedByLabel.slice(0, 4);
};

export default function AICopilotChat() {
  const { user } = useAuth();
  const displayUser = user as { name?: string; email?: string } | null;
  const displayName = displayUser?.name?.split(" ")[0] ?? displayUser?.email?.split("@")[0] ?? "there";
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [showContextDropdown, setShowContextDropdown] = useState(false);
  const [upcomingEvents, setUpcomingEvents] = useState<CalendarEvent[]>([]);
  const [environmentalContext, setEnvironmentalContext] = useState({
    time: "",
    greeting: "",
    weather: "Clear",
    timezone: "",
    hour: 12,
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const { isOnline } = useSyncEngine();
  const calendarAwareSuggestions = useMemo(() => buildCalendarAwareSuggestions(upcomingEvents), [upcomingEvents]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowContextDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const updateContext = () => {
      const now = new Date();
      const hour = now.getHours();
      const timeStr = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

      let greeting = "Good night";
      if (hour >= 5 && hour < 12) greeting = "Good morning";
      else if (hour >= 12 && hour < 17) greeting = "Good afternoon";
      else if (hour >= 17 && hour < 22) greeting = "Good evening";

      setEnvironmentalContext({
        time: timeStr,
        greeting,
        weather: hour < 18 ? "Clear" : "Clear Night",
        timezone,
        hour,
      });
    };

    updateContext();
    const timer = setInterval(updateContext, 60000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const loadEvents = async () => {
      try {
        const now = new Date();
        const tomorrow = new Date(now);
        tomorrow.setDate(tomorrow.getDate() + 1);

        const events = await getEvents(now.toISOString(), tomorrow.toISOString());
        setUpcomingEvents(events.slice(0, 5));
      } catch (error) {
        console.error("Failed to load events:", error);
      }
    };

    loadEvents();
    const interval = setInterval(loadEvents, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleSuggestedAction = async (action: SuggestedAction) => {
    const promptFromAction = action.data && typeof action.data["prompt"] === "string"
      ? (action.data["prompt"] as string)
      : "";

    if (promptFromAction) {
      handleDirectPrompt(promptFromAction);
      return;
    }

    let prompt = "";
    switch (action.type) {
      case "schedule":
        prompt = "I need to schedule a new meeting";
        break;
      case "query":
        if (action.label.toLowerCase().includes("week")) {
          prompt = "Show me my schedule for this week";
        } else if (action.label.toLowerCase().includes("free")) {
          prompt = "What are my available time slots today?";
        } else {
          prompt = `Help me with this request: ${action.label}`;
        }
        break;
    }

    if (prompt) {
      handleDirectPrompt(prompt);
    }
  };

  const handleDirectPrompt = (text: string) => {
    setInput(text);
    const fakeEvent = { preventDefault: () => {} } as FormEvent;
    setTimeout(() => {
        handleSubmit(fakeEvent, text);
    }, 50);
  };

  const handleSubmit = async (e: FormEvent, promptText?: string) => {
    e.preventDefault();
    const textToSend = promptText || input;
    if (!textToSend.trim() || isTyping) return;

    const userMessage: Message = {
      id: `user-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      role: "user",
      content: textToSend,
      timestamp: new Date(),
    };

    if (!isOnline) {
       const aiMessage: Message = {
        id: `ai-offline-${Date.now()}`,
        role: "ai",
        content: "I've saved your request locally. It will auto-sync and schedule when your connection is restored.",
        timestamp: new Date()
      };
      
      try {
        await db.chats.add({
          id: userMessage.id,
          role: 'user',
          content: textToSend,
          metadata: { intent: 'offline_schedule', payload: textToSend },
          timestamp: new Date().toISOString()
        });
      } catch (err) {
        console.error("Dexie queue error", err);
      }

      setMessages((prev) => [...prev, userMessage, aiMessage]);
      setInput("");
      return;
    }

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    // Dismiss mobile keyboard on send
    if (inputRef.current) {
      inputRef.current.blur();
    }

    try {
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const contextArray = upcomingEvents.map((event) => `Event: ${normalizeEventTitle(event.title)} at ${new Date(event.start_time).toLocaleString()}`);

      const data = await sendAiChat(userMessage.content, contextArray, timezone);

      const aiMessage: Message = {
        id: `ai-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
        role: "ai",
        content: data.result || "I apologize, but I couldn't process that request.",
        timestamp: new Date(),
        contextUsed: contextArray.length > 0 ? [`${contextArray.length} calendar events`] : undefined,
        metadata: {
          eventModified: data.result?.includes("(Updated)"),
          eventCreated: data.result?.includes("(Scheduled)"),
          eventDeleted: data.result?.includes("(Deleted)"),
        },
      };

      if (aiMessage.metadata?.eventCreated) {
        aiMessage.suggestedActions = [
          {
            id: "view-calendar",
            type: "query",
            label: "View calendar",
            description: "See all your scheduled events",
          },
        ];
      }

      setMessages((prev) => [...prev, aiMessage]);

      if (aiMessage.metadata?.eventCreated || aiMessage.metadata?.eventModified || aiMessage.metadata?.eventDeleted) {
        const now = new Date();
        const tomorrow = new Date(now);
        tomorrow.setDate(tomorrow.getDate() + 1);
        const events = await getEvents(now.toISOString(), tomorrow.toISOString());
        setUpcomingEvents(events.slice(0, 5));
      }
    } catch (error) {
      console.error(error);
      const errorMessage: Message = {
        id: `err-${Date.now()}`,
        role: "ai",
        content: "I'm experiencing difficulty connecting to my reasoning engine. Please try again in a moment.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as FormEvent);
    }
  };

  const clearConversation = () => {
    setMessages([]);
  };

  const hasText = input.trim().length > 0;

  // Contextual greeting subtitle
  const getSubtitle = () => {
    if (upcomingEvents.length > 0) {
      const count = upcomingEvents.length;
      return `You have ${count} meeting${count > 1 ? "s" : ""} today. How can I help you prepare?`;
    }
    return "Your calendar is clear today ✨";
  };

  return (
    <div className={cn("relative flex flex-col bg-transparent", styles.container)}>
      
      {/* Top Header — Minimal on mobile */}
      <div className="flex h-14 shrink-0 items-center justify-between px-3 pb-2 sm:px-6">
        <div className="flex items-center gap-3">
            {isOnline ? (
              <Badge variant="secondary" className="flex items-center gap-1.5 px-2 py-1 text-emerald-400 bg-emerald-400/10 border-emerald-500/20">
                 <Wifi className="h-3 w-3" /> Online
              </Badge>
            ) : (
              <Badge variant="secondary" className="flex items-center gap-1.5 px-2 py-1 text-amber-400 bg-amber-400/10 border-amber-500/20">
                 <CloudOff className="h-3 w-3" /> Offline Mode
              </Badge>
            )}
            {/* Context Dropdown Button */}
            <div className="relative" ref={dropdownRef}>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowContextDropdown(!showContextDropdown)}
                className="flex items-center gap-2"
              >
                <Calendar className="h-4 w-4" />
                <span className="hidden sm:inline">Context & Events ({upcomingEvents.length})</span>
              </Button>
              
              {/* Dropdown Content */}
              <AnimatePresence>
                {showContextDropdown && (
                  <motion.div
                    initial={{ opacity: 0, y: -10, scale: 0.97 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -10, scale: 0.97 }}
                    transition={{ duration: 0.18, ease: [0.32, 0.72, 0, 1] }}
                    className="absolute left-0 top-full z-50 mt-2 w-72 origin-top-left rounded-2xl border border-white/[0.08] bg-[#0d1322]/90 p-4 shadow-xl backdrop-blur-xl"
                  >
                    <div className="mb-3 flex items-center justify-between">
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.14em]">Local Context</span>
                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        {environmentalContext.weather.includes("Night") ? <Moon className="h-3 w-3" /> : environmentalContext.weather.includes("Cloud") ? <Cloud className="h-3 w-3" /> : <Sun className="h-3 w-3" />}
                        {environmentalContext.time}
                      </div>
                    </div>
                    <div className="mb-3 border-t border-white/[0.06] pt-3">
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.14em]">Upcoming</span>
                      <div className="mt-2 space-y-2">
                        {upcomingEvents.length > 0 ? upcomingEvents.map(event => (
                          <div key={event.id} className="flex flex-col text-sm text-slate-200">
                             <span className="font-medium truncate">{normalizeEventTitle(event.title)}</span>
                             <span className="text-xs text-slate-500">{formatEventTime(event.start_time)}</span>
                          </div>
                        )) : (
                          <span className="text-xs text-slate-500">No events found</span>
                        )}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
        </div>

        <div className="flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="icon"
            onClick={clearConversation}
            className="text-muted-foreground hover:text-foreground"
            title="New Chat"
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="text-muted-foreground hover:text-foreground"
          >
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {messages.length === 0 ? (
        /* ═══════════════════════════════════════════════════════
           WELCOME SCREEN — Claude-style
           ═══════════════════════════════════════════════════════ */
        <div className="flex flex-1 flex-col items-center justify-center px-4 pb-24 sm:pb-20">
          
          {/* Sparkle Orb */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, ease: [0.32, 0.72, 0, 1] }}
            className="relative mb-5"
          >
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-indigo-400/20 bg-gradient-to-br from-indigo-500/20 to-violet-500/15">
              <Sparkles className="h-7 w-7 text-indigo-400" />
            </div>
            <div className="absolute inset-0 rounded-2xl bg-indigo-500/10 blur-xl" />
          </motion.div>

          {/* Greeting */}
          <motion.div
            initial={{ y: 12, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.45, delay: 0.1 }}
            className="text-center"
          >
            <h1 className="font-serif text-3xl font-medium leading-tight tracking-tight text-white sm:text-[2.5rem]">
              {getTimeEmoji(environmentalContext.hour)} {environmentalContext.greeting}, {displayName}
            </h1>
            <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-slate-400 sm:text-base">
              {getSubtitle()}
            </p>
          </motion.div>

          {/* Next Upcoming Event Card (if exists) */}
          {upcomingEvents.length > 0 && (
            <motion.div
              initial={{ y: 12, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.4, delay: 0.2 }}
              className="mt-6 w-full max-w-md"
            >
              <Card className="bg-primary/5 border-primary/10 shadow-none">
                <CardContent className="flex items-center gap-3 p-4">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                    <Calendar className="h-4 w-4 text-primary" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate">{normalizeEventTitle(upcomingEvents[0].title)}</p>
                    <p className="text-xs text-muted-foreground">
                      Next up · {formatEventTime(upcomingEvents[0].start_time)}
                    </p>
                  </div>
                  <Badge variant="secondary" className="bg-primary/10 text-primary hover:bg-primary/15">
                    {upcomingEvents[0].category || "General"}
                  </Badge>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Composer (welcome screen) */}
          <motion.div
            initial={{ y: 12, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.25 }}
            className="mt-8 w-full max-w-2xl px-2"
          >
            <form onSubmit={handleSubmit} className="relative rounded-xl border border-white/[0.08] bg-card/90 p-3 shadow-sm transition-all focus-within:border-primary/30 focus-within:ring-1 focus-within:ring-primary/20">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask anything about your schedule..."
                className="w-full resize-none border-0 bg-transparent text-foreground placeholder:text-muted-foreground focus:ring-0 focus:outline-none sm:text-base outline-none min-h-[44px] text-sm"
                rows={1}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = "auto";
                  target.style.height = Math.min(target.scrollHeight, 128) + "px";
                }}
              />
              <div className="mt-2 flex items-center justify-between">
                <div />
                <Button
                  type="submit"
                  size="icon"
                  disabled={!hasText || isTyping}
                  className={cn(
                    "rounded-lg transition-all duration-200",
                    hasText ? "bg-primary text-primary-foreground hover:bg-primary/90" : "bg-muted text-muted-foreground hover:bg-muted"
                  )}
                >
                  {isTyping ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUp className="h-4 w-4" />}
                </Button>
              </div>
            </form>
          </motion.div>

          {/* Suggestion Chips — 2-column grid */}
          <motion.div
            initial={{ y: 12, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.35 }}
            className="mt-5 grid w-full max-w-2xl grid-cols-2 gap-2.5 px-2"
          >
            {calendarAwareSuggestions.map((suggestion) => (
              <button
                key={`composer-${suggestion.id}`}
                type="button"
                onClick={() => handleSuggestedAction(suggestion)}
                className="suggestion-chip group flex items-start gap-3 rounded-2xl border border-white/[0.07] bg-white/[0.02] px-4 py-3.5 text-left transition-all duration-200 hover:-translate-y-0.5 hover:bg-white/[0.05] hover:border-white/[0.12] active:translate-y-0 active:scale-[0.99]"
              >
                <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white/[0.06] text-slate-400 group-hover:text-indigo-400 group-hover:bg-indigo-500/10 transition-colors">
                  {getSuggestionIcon(suggestion.icon)}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-slate-200">{suggestion.label}</p>
                  <p className="mt-0.5 text-xs text-slate-500 leading-relaxed line-clamp-2">{suggestion.description}</p>
                </div>
              </button>
            ))}
          </motion.div>
        </div>
      ) : (
        /* ═══════════════════════════════════════════════════════
           CONVERSATION VIEW
           ═══════════════════════════════════════════════════════ */
        <div className="flex flex-1 flex-col overflow-hidden w-full">
          <div ref={chatContainerRef} className={cn("flex-1 overflow-y-auto w-full", styles.chatScroll)}>
             <div className="mx-auto max-w-3xl py-6 h-full px-3 sm:px-4">
                <AnimatePresence initial={false}>
                  {messages.map((msg, idx) => (
                    <motion.div
                      key={msg.id || `msg-${idx}`}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.25, ease: [0.32, 0.72, 0, 1] }}
                      className={cn(
                        "mb-5",
                        msg.role === "user" ? "flex justify-end" : "flex justify-start"
                      )}
                    >
                      {msg.role === "ai" ? (
                        /* AI Message — Full-width block */
                        <div className="w-full">
                          <div className="flex items-start gap-3">
                            <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/15">
                              <Sparkles className="h-3.5 w-3.5" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="whitespace-pre-wrap text-[15px] leading-[1.75] text-slate-200">
                                {msg.content}
                              </p>
                              
                              {msg.metadata?.eventCreated && (
                                <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
                                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> Event scheduled
                                </div>
                              )}
                              
                              {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                                <div className="mt-3 flex flex-wrap gap-2">
                                  {msg.suggestedActions.map((action, actionIdx) => (
                                    <button
                                      key={action.id || `action-${actionIdx}`}
                                      onClick={() => handleSuggestedAction(action)}
                                      className="suggestion-chip rounded-xl border border-white/[0.08] bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-white/[0.08] hover:border-white/[0.14] transition-all"
                                    >
                                      {action.label}
                                    </button>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ) : (
                        /* User Message — Right-aligned bubble */
                        <div className="max-w-[80%]">
                          <div className="rounded-2xl rounded-br-md border border-indigo-400/20 bg-indigo-500/18 px-4 py-3 shadow-sm shadow-indigo-950/20">
                            <p className="whitespace-pre-wrap text-[15px] leading-relaxed text-slate-100">
                              {msg.content}
                            </p>
                          </div>
                        </div>
                      )}
                    </motion.div>
                  ))}
                  
                  {/* Shimmer Typing Indicator */}
                  {isTyping && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mb-5 flex justify-start"
                    >
                      <div className="w-full">
                        <div className="flex items-start gap-3">
                          <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/15">
                            <Bot className="h-3.5 w-3.5 animate-pulse" />
                          </div>
                          <div className="flex-1 pt-1">
                            <div className="shimmer-bar w-3/4" />
                            <div className="shimmer-bar shimmer-bar-sm" />
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}
                  <div key="scroll-anchor" ref={messagesEndRef} className="h-4" />
                </AnimatePresence>
             </div>
          </div>
          
          {/* Composer (conversation mode) — Frosted glass pinned bottom */}
          <div className="mobile-composer mx-auto w-full max-w-3xl px-3 sm:px-4 py-3">
            <form onSubmit={handleSubmit} className="relative rounded-xl border border-white/[0.08] bg-card/90 p-3 shadow-lg transition-all focus-within:border-primary/30 focus-within:ring-1 focus-within:ring-primary/20">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message..."
                className="w-full resize-none border-0 bg-transparent text-foreground placeholder:text-muted-foreground focus:ring-0 focus:outline-none sm:text-base outline-none min-h-[44px] text-sm"
                rows={1}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = "auto";
                  target.style.height = Math.min(target.scrollHeight, 128) + "px";
                }}
              />
              <div className="mt-1.5 flex items-center justify-between">
                <div />
                <Button
                  type="submit"
                  size="icon"
                  disabled={!hasText || isTyping}
                  className={cn(
                    "rounded-lg transition-all duration-200",
                    hasText ? "bg-primary text-primary-foreground hover:bg-primary/90" : "bg-muted text-muted-foreground hover:bg-muted"
                  )}
                >
                  {isTyping ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUp className="h-4 w-4" />}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
