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
  CheckCircle2,
  Lightbulb,
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
import { useAuthContext } from "@/app/providers/auth-provider";

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
        prompt: `Give me a concise preparation checklist for "${nextEvent.title}" before ${nextEventTime}.`,
      },
    });
    suggestions.push({
      id: "optimize-day-around-event",
      type: "query",
      label: "Optimize my day",
      description: "Protect focus blocks around upcoming meetings",
      data: {
        prompt: `Reorganize the rest of my day around "${nextEvent.title}" at ${nextEventTime}. Suggest focused work blocks and breaks.`,
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
  const { user } = useAuthContext();
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
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const calendarAwareSuggestions = useMemo(() => buildCalendarAwareSuggestions(upcomingEvents), [upcomingEvents]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
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

      let greeting = "Good evening";
      if (hour < 12) greeting = "Good morning";
      else if (hour < 17) greeting = "Good afternoon";

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
      id: Date.now().toString(),
      role: "user",
      content: textToSend,
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
  };

  return (
    <div className="relative flex h-[calc(100dvh-4rem)] flex-col bg-transparent sm:h-[calc(100dvh-2rem)] px-2 sm:px-6 py-4">
      
      {/* Top Header */}
      <div className="flex h-14 shrink-0 items-center justify-between pb-4">
        <div className="flex items-center gap-3">
            {/* Context Dropdown Button */}
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setShowContextDropdown(!showContextDropdown)}
                className="flex items-center gap-2 rounded-lg border border-slate-800 bg-[#2a2723]/30 px-3 py-1.5 text-sm font-medium text-slate-300 transition hover:bg-[#2a2723]/60 focus:outline-none"
              >
                <Calendar className="h-4 w-4" />
                <span className="hidden sm:inline">Context & Events ({upcomingEvents.length})</span>
              </button>
              
              {/* Dropdown Content */}
              <AnimatePresence>
                {showContextDropdown && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute left-0 top-full z-50 mt-2 w-72 origin-top-left rounded-xl border border-slate-800 bg-slate-900/95 p-4 shadow-xl backdrop-blur-xl"
                  >
                    <div className="mb-3 flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Local Context</span>
                      <div className="flex items-center gap-2 text-xs text-slate-300">
                        {environmentalContext.weather.includes("Night") ? <Moon className="h-3 w-3" /> : environmentalContext.weather.includes("Cloud") ? <Cloud className="h-3 w-3" /> : <Sun className="h-3 w-3" />}
                        {environmentalContext.time}
                      </div>
                    </div>
                    <div className="mb-3 border-t border-slate-800 pt-3">
                      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Upcoming</span>
                      <div className="mt-2 space-y-2">
                        {upcomingEvents.length > 0 ? upcomingEvents.map(event => (
                          <div key={event.id} className="flex flex-col text-sm text-slate-200">
                             <span className="font-medium truncate">{event.title}</span>
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

        <div className="flex items-center gap-2">
          <button
            onClick={clearConversation}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-900/50 hover:text-slate-100 transition-colors"
            title="New Chat"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
          <button
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-900/50 hover:text-slate-100 transition-colors"
          >
            <MoreHorizontal className="h-4 w-4" />
          </button>
        </div>
      </div>

      {messages.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center px-4 pb-20">
          <h1 className="mb-8 font-serif text-3xl font-medium tracking-tight text-[#e4e2de] sm:text-[2.5rem]">
            {environmentalContext.greeting}, {displayName}
          </h1>
          
          <div className="w-full max-w-2xl">
            <form onSubmit={handleSubmit} className="relative rounded-2xl border border-slate-700/50 bg-[#2a2723]/30 p-4 transition-colors focus-within:border-slate-500/50 hover:border-slate-600/50 shadow-sm">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type / for skills"
                className="w-full resize-none border-0 bg-transparent text-[#e4e2de] placeholder:text-slate-500 focus:ring-0 sm:text-base outline-none min-h-[44px]"
                rows={1}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = "auto";
                  target.style.height = Math.min(target.scrollHeight, 128) + "px";
                }}
              />
              <div className="mt-2 flex items-center justify-between">
                <button type="button" className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors">
                  <div className="flex items-center gap-1.5">
                     <span className="text-sm font-medium">+</span>
                  </div>
                </button>
                <div className="flex items-center justify-end">
                    <button
                      type="submit"
                      disabled={!input.trim() || isTyping}
                      className="inline-flex items-center justify-center rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-800 disabled:opacity-50"
                    >
                      {isTyping ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                    </button>
                </div>
              </div>
            </form>
          </div>

          <div className="mt-6 flex flex-wrap justify-center gap-2 px-2 max-w-2xl w-full">
            {calendarAwareSuggestions.map((suggestion) => (
              <button
                key={`composer-${suggestion.id}`}
                type="button"
                onClick={() => handleSuggestedAction(suggestion)}
                className="flex items-center gap-2 rounded-full border border-slate-700/50 bg-transparent px-3 py-1.5 text-sm font-medium text-slate-300 transition hover:bg-slate-800 hover:text-slate-200"
              >
                {suggestion.type === "schedule" ? <Calendar className="h-3.5 w-3.5 text-slate-400" /> : <Lightbulb className="h-3.5 w-3.5 text-slate-400" />}
                {suggestion.label}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="flex flex-1 flex-col overflow-hidden w-full">
          <div className="flex-1 overflow-y-auto w-full">
             {/* Chat List */}
             <div className="mx-auto max-w-3xl space-y-6 py-6 h-full px-2">
                <AnimatePresence initial={false}>
                  {messages.map((msg) => (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={cn("flex", msg.role === "user" ? "justify-end" : "justify-start")}
                    >
                      <div className={cn("flex max-w-[85%] gap-4", msg.role === "user" ? "flex-row-reverse" : "flex-row")}>
                         {msg.role === "ai" && (
                            <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                              <Sparkles className="h-4 w-4" />
                            </div>
                         )}
                         <div className={cn("flex flex-col gap-1", msg.role === "user" ? "items-end" : "items-start")}>
                            <div
                              className={cn(
                                "rounded-2xl px-5 py-3 text-[15px] leading-relaxed shadow-sm",
                                msg.role === "user"
                                  ? "bg-[#2a2723] border border-slate-800 text-[#e4e2de]"
                                  : "bg-transparent text-[#e4e2de]"
                              )}
                            >
                                <p className="m-0 whitespace-pre-wrap">{msg.content}</p>
                                
                                {msg.metadata?.eventCreated && (
                                  <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
                                    <CheckCircle2 className="h-4 w-4 text-emerald-400" /> Event scheduled
                                  </div>
                                )}
                            </div>
                            {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                                <div className="mt-2 flex flex-wrap gap-2">
                                  {msg.suggestedActions.map((action) => (
                                    <button
                                      key={action.id}
                                      onClick={() => handleSuggestedAction(action)}
                                      className="rounded-full border border-slate-700 bg-transparent px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-800 transition-colors"
                                    >
                                      {action.label}
                                    </button>
                                  ))}
                                </div>
                            )}
                         </div>
                      </div>
                    </motion.div>
                  ))}
                  {isTyping && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex justify-start">
                      <div className="flex max-w-[85%] gap-4">
                        <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                          <Bot className="h-4 w-4 animate-pulse" />
                        </div>
                        <div className="flex items-center gap-1.5 px-4 py-3">
                          <span className="h-2 w-2 animate-bounce rounded-full bg-slate-500 [animation-delay:-0.3s]" />
                          <span className="h-2 w-2 animate-bounce rounded-full bg-slate-500 [animation-delay:-0.15s]" />
                          <span className="h-2 w-2 animate-bounce rounded-full bg-slate-500" />
                        </div>
                      </div>
                    </motion.div>
                  )}
                  <div ref={messagesEndRef} className="h-4" />
                </AnimatePresence>
             </div>
          </div>
          
          <div className="mx-auto w-full max-w-3xl px-2 pb-6 pt-2">
            <form onSubmit={handleSubmit} className="relative rounded-2xl border border-slate-700/50 bg-[#2a2723]/30 p-3 transition-colors focus-within:border-slate-500/50 hover:border-slate-600/50 shadow-sm">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message..."
                className="w-full resize-none border-0 bg-transparent text-[#e4e2de] placeholder:text-slate-500 focus:ring-0 sm:text-base outline-none min-h-[44px]"
                rows={1}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = "auto";
                  target.style.height = Math.min(target.scrollHeight, 128) + "px";
                }}
              />
              <div className="mt-1 flex items-center justify-between">
                <button type="button" className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors">
                  <div className="flex items-center gap-1.5">
                     <span className="text-sm font-medium">+</span>
                  </div>
                </button>
                <div className="flex items-center justify-end">
                    <button
                      type="submit"
                      disabled={!input.trim() || isTyping}
                      className="inline-flex items-center justify-center rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-800 disabled:opacity-50"
                    >
                      {isTyping ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                    </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
