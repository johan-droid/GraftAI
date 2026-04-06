"use client";

import { useState, useRef, useEffect, FormEvent, KeyboardEvent, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  Send,
  Sparkles,
  User as UserIcon,
  Loader2,
  Calendar,
  Clock,
  CheckCircle2,
  Lightbulb,
  Menu,
  RefreshCw,
  MapPin,
  X,
  MoreHorizontal,
  Sun,
  Moon,
  Cloud,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { sendAiChat, getEvents } from "@/lib/api";

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
  data?: Record<string, unknown>;
}

interface CalendarEvent {
  id: number;
  title: string;
  start_time: string;
  end_time: string;
  category: string;
  status: string;
}

const formatEventTime = (isoDate: string) =>
  new Date(isoDate).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

const buildCalendarAwareSuggestions = (events: CalendarEvent[]): SuggestedAction[] => {
  const suggestions: SuggestedAction[] = [];
  const nextEvent = events[0];

  if (nextEvent) {
    const nextEventTime = formatEventTime(nextEvent.start_time);
    suggestions.push({
      id: "prep-next-event",
      type: "query",
      label: `Prep for ${nextEvent.title}`,
      description: `Generate a quick prep checklist before ${nextEventTime}`,
      data: {
        prompt: `Give me a concise preparation checklist for \"${nextEvent.title}\" before ${nextEventTime}.`,
      },
    });
    suggestions.push({
      id: "optimize-day-around-event",
      type: "query",
      label: "Optimize my day",
      description: "Protect focus blocks around upcoming meetings",
      data: {
        prompt: `Reorganize the rest of my day around \"${nextEvent.title}\" at ${nextEventTime}. Suggest focused work blocks and breaks.`,
      },
    });
  }

  suggestions.push(
    {
      id: "show-today-plan",
      type: "query",
      label: "Show today plan",
      description: "Get a structured timeline for today",
      data: { prompt: "Summarize my day in timeline format with recommended priorities." },
    },
    {
      id: "find-free-slots",
      type: "query",
      label: "Find free slots",
      description: "Detect available windows for deep work",
      data: { prompt: "What are my free time slots today for 60-90 minute focus sessions?" },
    },
    {
      id: "schedule-meeting",
      type: "schedule",
      label: "Schedule a meeting",
      description: "Create an event in the best available slot",
      data: { prompt: "I need to schedule a new meeting. Find the best slot and suggest options." },
    }
  );

  const deduped = suggestions.filter(
    (item, index, arr) => arr.findIndex((candidate) => candidate.label === item.label) === index
  );

  return deduped.slice(0, 4);
};

export default function AICopilotChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [contextPanel, setContextPanel] = useState(false);
  const [upcomingEvents, setUpcomingEvents] = useState<CalendarEvent[]>([]);
  const [environmentalContext, setEnvironmentalContext] = useState({
    time: "",
    greeting: "",
    weather: "Clear",
    timezone: "",
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const calendarAwareSuggestions = useMemo(() => buildCalendarAwareSuggestions(upcomingEvents), [upcomingEvents]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    const updateContext = () => {
      const now = new Date();
      const hour = now.getHours();
      const timeStr = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

      let greeting = "Good Evening";
      if (hour < 12) greeting = "Good Morning";
      else if (hour < 17) greeting = "Good Afternoon";

      setEnvironmentalContext({
        time: timeStr,
        greeting,
        weather: hour < 18 ? "Clear" : "Clear Night",
        timezone,
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

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.innerWidth >= 1024) {
      setContextPanel(true);
    }
  }, []);

  useEffect(() => {
    if (messages.length === 0) {
      const nextEvent = upcomingEvents[0];
      const nextEventSummary = nextEvent
        ? `Your next event is \"${nextEvent.title}\" at ${formatEventTime(nextEvent.start_time)}.`
        : "Your calendar is clear in the next day window.";

      const welcomeMessage: Message = {
        id: "welcome",
        role: "ai",
        content: `${environmentalContext.greeting}! I'm GraftAI, your calendar-aware orchestration assistant.

${nextEventSummary}

I can help you with scheduling, conflict resolution, and smart daily planning. What should we optimize first?`,
        timestamp: new Date(),
        suggestedActions: calendarAwareSuggestions,
      };
      setMessages([welcomeMessage]);
    }
  }, [calendarAwareSuggestions, environmentalContext.greeting, messages.length, upcomingEvents]);

  const handleSuggestedAction = async (action: SuggestedAction) => {
    const promptFromAction = action.data && typeof action.data["prompt"] === "string"
      ? (action.data["prompt"] as string)
      : "";

    if (promptFromAction) {
      setInput(promptFromAction);
      inputRef.current?.focus();
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
      setInput(prompt);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    try {
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const contextArray = upcomingEvents.map((event) => `Event: ${event.title} at ${new Date(event.start_time).toLocaleString()}`);

      const data = await sendAiChat(userMessage.content, contextArray, timezone);

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
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
        id: (Date.now() + 1).toString(),
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
    setTimeout(() => {
      const welcomeMessage: Message = {
        id: "welcome-" + Date.now(),
        role: "ai",
        content: `Conversation cleared. ${environmentalContext.greeting}! Ready when you are. I can scan your calendar and suggest the best next moves.`,
        timestamp: new Date(),
        suggestedActions: calendarAwareSuggestions,
      };
      setMessages([welcomeMessage]);
    }, 100);
  };

  return (
    <div className="relative flex h-[calc(100dvh-5.4rem)] overflow-hidden rounded-none border border-slate-800/70 bg-slate-950 shadow-2xl sm:h-[calc(100dvh-8rem)] sm:rounded-[28px]">
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-slate-900/40 via-transparent to-slate-950/90" />

      <AnimatePresence>
        {contextPanel && (
          <>
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setContextPanel(false)}
              aria-label="Close context panel overlay"
              className="absolute inset-0 z-20 bg-slate-950/70 backdrop-blur-sm lg:hidden"
            />
            <motion.aside
              initial={{ x: -24, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -24, opacity: 0 }}
              transition={{ type: "spring", damping: 24, stiffness: 240 }}
              className="absolute inset-y-0 left-0 z-30 flex w-[88vw] max-w-[320px] flex-col overflow-hidden border-r border-slate-800/70 bg-slate-950/95 backdrop-blur-xl lg:static lg:z-10 lg:w-[320px] lg:max-w-none"
            >
              <div className="border-b border-slate-800/70 px-4 py-5 sm:px-5 sm:py-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-300">Context</h3>
                  <button
                    onClick={() => setContextPanel(false)}
                    className="min-h-11 min-w-11 rounded-xl border border-slate-800/70 bg-slate-900/70 p-2 text-slate-400 transition-colors hover:text-slate-200"
                    aria-label="Close context panel"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>

                <div className="space-y-3">
                  <div className="rounded-2xl border border-slate-800/70 bg-slate-900/60 p-3">
                    <div className="flex items-center gap-3">
                      {environmentalContext.weather.includes("Night") ? (
                        <Moon className="h-5 w-5 text-indigo-300" />
                      ) : environmentalContext.weather.includes("Cloud") ? (
                        <Cloud className="h-5 w-5 text-slate-300" />
                      ) : (
                        <Sun className="h-5 w-5 text-amber-300" />
                      )}
                      <div>
                        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">Local time</p>
                        <p className="text-sm font-semibold text-slate-100">{environmentalContext.time}</p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-slate-800/70 bg-slate-900/60 p-3">
                    <div className="flex items-center gap-3">
                      <MapPin className="h-5 w-5 text-emerald-300" />
                      <div className="min-w-0">
                        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">Timezone</p>
                        <p className="truncate text-xs font-medium text-slate-200">{environmentalContext.timezone}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto px-4 py-5 sm:px-5 sm:py-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-300">Upcoming</h3>
                  <span className="rounded-full border border-slate-700 bg-slate-900 px-2 py-1 text-[10px] font-semibold text-slate-400">
                    {upcomingEvents.length}
                  </span>
                </div>

                <div className="space-y-2.5">
                  {upcomingEvents.length > 0 ? (
                    upcomingEvents.map((event) => (
                      <motion.button
                        key={event.id}
                        type="button"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        onClick={() =>
                          handleSuggestedAction({
                            id: `event-${event.id}`,
                            type: "query",
                            label: `Plan around ${event.title}`,
                            description: "Create timeline around this event",
                            data: {
                              prompt: `Build a plan around my event \"${event.title}\" at ${formatEventTime(event.start_time)} and propose prep + follow-up blocks.`,
                            },
                          })
                        }
                        className="w-full rounded-2xl border border-slate-800/70 bg-slate-900/70 p-3 text-left transition hover:border-primary/40"
                      >
                        <div className="flex items-start gap-3">
                          <span
                            className={cn(
                              "mt-1.5 h-2 w-2 shrink-0 rounded-full",
                              event.category === "meeting"
                                ? "bg-violet-400"
                                : event.category === "event"
                                ? "bg-yellow-400"
                                : event.category === "task"
                                ? "bg-cyan-400"
                                : "bg-pink-400"
                            )}
                          />
                          <div className="min-w-0 flex-1">
                            <h4 className="mb-0.5 truncate text-sm font-semibold text-slate-100">{event.title}</h4>
                            <div className="flex items-center gap-2 text-[11px] text-slate-400">
                              <Clock className="h-3 w-3" />
                              {formatEventTime(event.start_time)}
                            </div>
                          </div>
                        </div>
                      </motion.button>
                    ))
                  ) : (
                    <div className="py-10 text-center">
                      <Calendar className="mx-auto mb-3 h-7 w-7 text-slate-600" />
                      <p className="text-sm text-slate-500">No upcoming events</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="border-t border-slate-800/70 px-4 py-4 sm:px-5 sm:py-5">
                <button
                  onClick={() => setInput("Review my calendar and suggest the smartest plan for today.")}
                  className="flex min-h-11 w-full items-center justify-center gap-2 rounded-xl border border-primary/30 bg-primary/15 px-4 py-2.5 text-xs font-semibold text-primary transition hover:bg-primary/20"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  Smart daily suggestions
                </button>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      <div className="relative z-10 flex min-w-0 flex-1 flex-col">
        <div className="flex items-center justify-between px-3 pb-3 pt-3 sm:px-6 sm:pb-4 sm:pt-5">
          <div className="flex min-w-0 items-center gap-3 sm:gap-4">
            {!contextPanel && (
              <button
                onClick={() => setContextPanel(true)}
                className="min-h-11 min-w-11 rounded-xl border border-slate-800/70 bg-slate-900/70 p-2 text-slate-300 transition hover:text-white"
                aria-label="Open context panel"
              >
                <Menu className="h-5 w-5" />
              </button>
            )}
            <div className="relative">
              <div className="rounded-2xl border border-primary/40 bg-gradient-to-br from-primary to-violet-600 p-2.5 text-white shadow-lg shadow-primary/25">
                <Bot className="h-5 w-5 sm:h-6 sm:w-6" />
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full border-2 border-slate-950 bg-emerald-500">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-white" />
              </span>
            </div>
            <div className="min-w-0">
              <h2 className="truncate text-lg font-semibold tracking-tight text-white">GraftAI</h2>
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full border border-emerald-400/20 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-300">
                  Calendar-aware
                </span>
                <span className="hidden text-[11px] text-slate-400 sm:inline">{upcomingEvents.length} events in context</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={clearConversation}
              className="min-h-11 min-w-11 rounded-xl border border-slate-800/70 bg-slate-900/70 p-2 text-slate-400 transition hover:text-slate-100"
              aria-label="Clear conversation"
              title="Clear conversation"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
            <button
              className="min-h-11 min-w-11 rounded-xl border border-slate-800/70 bg-slate-900/70 p-2 text-slate-400 transition hover:text-slate-100"
              aria-label="More chatbot actions"
              title="More actions"
            >
              <MoreHorizontal className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="mx-3 h-px bg-gradient-to-r from-transparent via-slate-700/80 to-transparent sm:mx-6" />

        <div className="flex-1 space-y-5 overflow-y-auto px-3 pb-4 pt-4 sm:space-y-6 sm:px-6 sm:pb-6 sm:pt-6" aria-live="polite" aria-label="Chat conversation">
          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 20, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.35, ease: [0.23, 1, 0.32, 1] }}
                className={cn("flex max-w-[94%] sm:max-w-[84%]", msg.role === "user" ? "ml-auto" : "mr-auto")}
              >
                <div className={cn("flex w-full gap-2.5 sm:gap-4", msg.role === "user" ? "flex-row-reverse" : "flex-row")}>
                  <div
                    className={cn(
                      "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border sm:h-10 sm:w-10 sm:rounded-2xl",
                      msg.role === "user"
                        ? "border-slate-700 bg-slate-900 text-slate-300"
                        : "border-primary/40 bg-gradient-to-br from-primary to-violet-600 text-white"
                    )}
                  >
                    {msg.role === "user" ? <UserIcon className="h-4 w-4 sm:h-5 sm:w-5" /> : <Sparkles className="h-4 w-4 sm:h-5 sm:w-5" />}
                  </div>

                  <div className={cn("flex flex-1 flex-col gap-2", msg.role === "user" ? "items-end" : "items-start")}>
                    <div
                      className={cn(
                        "max-w-full rounded-2xl px-4 py-3 shadow-sm sm:px-5 sm:py-4",
                        msg.role === "user"
                          ? "rounded-tr-md border border-primary/35 bg-gradient-to-br from-primary to-violet-600 text-white"
                          : "rounded-tl-md border border-slate-800/80 bg-slate-900/85 text-slate-100"
                      )}
                    >
                      <p className="m-0 whitespace-pre-wrap text-[13px] leading-relaxed text-current sm:text-[14px]">{msg.content}</p>

                      {msg.metadata?.eventCreated && (
                        <div className="mt-3 flex items-center gap-2 border-t border-white/15 pt-3 text-xs">
                          <CheckCircle2 className="h-4 w-4" />
                          <span className="font-medium">Event created successfully</span>
                        </div>
                      )}
                      {msg.metadata?.eventModified && (
                        <div className="mt-3 flex items-center gap-2 border-t border-slate-700/70 pt-3 text-xs text-emerald-300">
                          <CheckCircle2 className="h-4 w-4" />
                          <span className="font-medium">Event updated successfully</span>
                        </div>
                      )}
                      {msg.metadata?.eventDeleted && (
                        <div className="mt-3 flex items-center gap-2 border-t border-slate-700/70 pt-3 text-xs text-amber-300">
                          <CheckCircle2 className="h-4 w-4" />
                          <span className="font-medium">Event deleted successfully</span>
                        </div>
                      )}
                    </div>

                    {msg.contextUsed && msg.contextUsed.length > 0 && (
                      <div className="flex items-center gap-2 rounded-full border border-slate-700/80 bg-slate-900/80 px-3 py-1.5">
                        <Lightbulb className="h-3 w-3 text-amber-300" />
                        <span className="text-xs text-slate-400">Used context: {msg.contextUsed.join(", ")}</span>
                      </div>
                    )}

                    {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                      <div className="mt-1 flex w-full flex-wrap gap-2">
                        {msg.suggestedActions.map((action) => (
                          <button
                            key={action.id}
                            onClick={() => handleSuggestedAction(action)}
                            className="min-h-10 rounded-full border border-slate-700/80 bg-slate-900/70 px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-primary/50 hover:text-white"
                          >
                            <span className="inline-flex items-center gap-1.5">
                              <Sparkles className="h-3.5 w-3.5 text-primary" />
                              {action.label}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}

                    <span className="px-1.5 text-[10px] font-medium text-slate-500">{msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                  </div>
                </div>
              </motion.div>
            ))}

            {isTyping && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mr-auto flex max-w-[85%]">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl border border-primary/40 bg-gradient-to-br from-primary to-violet-600 text-white sm:h-10 sm:w-10 sm:rounded-2xl">
                    <Bot className="h-5 w-5 animate-pulse" />
                  </div>
                  <div className="flex items-center gap-1.5 rounded-2xl border border-slate-800/80 bg-slate-900/85 px-4 py-3">
                    <span className="h-2 w-2 animate-bounce rounded-full bg-slate-500 [animation-delay:-0.3s]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-slate-500 [animation-delay:-0.15s]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-slate-500" />
                  </div>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </AnimatePresence>
        </div>

        <div className="px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-2 sm:px-6 sm:pb-6 sm:pt-3">
          <form onSubmit={handleSubmit} className="mx-auto w-full max-w-4xl">
            <div className="mb-2.5 flex gap-2 overflow-x-auto pb-1 sm:mb-3">
              {calendarAwareSuggestions.map((suggestion) => (
                <button
                  key={`composer-${suggestion.id}`}
                  type="button"
                  onClick={() => handleSuggestedAction(suggestion)}
                  className="whitespace-nowrap rounded-full border border-slate-700/80 bg-slate-900/80 px-3 py-1.5 text-[11px] font-medium text-slate-300 transition hover:border-primary/40 hover:text-white"
                  title={suggestion.description}
                >
                  {suggestion.label}
                </button>
              ))}
            </div>

            <div className="rounded-[24px] border border-slate-700/80 bg-slate-900/85 p-2 shadow-[0_14px_50px_-30px_rgba(59,130,246,0.65)] transition focus-within:border-primary/45">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Message GraftAI about your calendar, schedule, or planning needs..."
                rows={1}
                aria-label="Message GraftAI"
                className="max-h-32 min-h-[44px] w-full resize-none bg-transparent px-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = "auto";
                  target.style.height = Math.min(target.scrollHeight, 128) + "px";
                }}
              />

              <div className="mt-1 flex items-center justify-between gap-3 px-1 pb-1">
                <p className="text-[11px] text-slate-500">Enter to send, Shift + Enter for new line</p>
                <button
                  type="submit"
                  disabled={!input.trim() || isTyping}
                  className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-xl border border-primary/35 bg-gradient-to-br from-primary to-violet-600 px-3 text-white transition hover:from-primary/90 hover:to-violet-600/90 disabled:cursor-not-allowed disabled:opacity-35"
                  aria-label="Send message"
                >
                  {isTyping ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="mt-2 flex flex-wrap items-center justify-center gap-2 sm:mt-3">
              <div className="flex items-center gap-1.5 rounded-full border border-slate-700/80 bg-slate-900/70 px-3 py-1.5 text-[11px] font-medium uppercase tracking-[0.16em] text-slate-400">
                <Sparkles className="h-3 w-3 text-primary" />
                AI orchestration active
              </div>
              <div className="hidden items-center gap-1.5 rounded-full border border-slate-700/80 bg-slate-900/70 px-3 py-1.5 text-[11px] font-medium uppercase tracking-[0.16em] text-slate-500 sm:flex">
                <Calendar className="h-3 w-3 text-violet-300" />
                {upcomingEvents.length} events loaded
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
