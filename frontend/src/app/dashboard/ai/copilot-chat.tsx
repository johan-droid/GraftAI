"use client";

import { useState, useRef, useEffect, FormEvent, KeyboardEvent, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot, Sparkles, Loader2, Calendar,
  Lightbulb, RefreshCw, Sun, Moon,
  Clock, Zap, BarChart3, ArrowUp, CloudOff, Wifi,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { sendAiChat, getEvents } from "@/lib/api";
import { useAuth } from "@/app/providers/auth-provider";
import { useSyncEngine } from "@/hooks/useSyncEngine";

// --- Types ---
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

// --- Helpers ---
const formatEventTime = (isoDate: string) =>
  new Date(isoDate).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

const normalizeEventTitle = (title?: string) => title?.trim() || "Untitled event";

const getSuggestionIcon = (iconName?: string) => {
  switch (iconName) {
    case "calendar": return <Calendar className="h-5 w-5" />;
    case "chart": return <BarChart3 className="h-5 w-5" />;
    case "zap": return <Zap className="h-5 w-5" />;
    case "clock": return <Clock className="h-5 w-5" />;
    default: return <Lightbulb className="h-5 w-5" />;
  }
};

const buildCalendarAwareSuggestions = (events: CalendarEvent[]): SuggestedAction[] => {
  const suggestions: SuggestedAction[] = [];
  const sorted = [...events].sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());
  const now = new Date();
  
  const nextEvent = sorted.find(e => new Date(e.start_time) > now);
  if (nextEvent) {
    const nextEventTime = formatEventTime(nextEvent.start_time);
    suggestions.push({
      id: "prep-next-event",
      type: "query",
      label: `Prep for ${normalizeEventTitle(nextEvent.title)}`,
      description: `Generate a checklist for your ${nextEventTime} meeting`,
      icon: "zap",
      data: { prompt: `Give me a concise prep checklist for "${normalizeEventTitle(nextEvent.title)}" at ${nextEventTime}.` },
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
      label: "Schedule a meeting",
      description: "Set up a structured meeting with goal points",
      icon: "calendar",
      data: { prompt: "Schedule a 30m sync on Google Meet for tomorrow at 3pm." },
    }
  );

  return suggestions.filter((item, index, arr) => arr.findIndex((c) => c.label === item.label) === index).slice(0, 4);
};

export default function AICopilotChat() {
  const { user } = useAuth();
  const displayName =
    typeof user === "object" && user !== null && "name" in user && typeof (user as { name?: unknown }).name === "string"
      ? (user as { name: string }).name.split(" ")[0]
      : "there";
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [showContextDropdown, setShowContextDropdown] = useState(false);
  const [upcomingEvents, setUpcomingEvents] = useState<CalendarEvent[]>([]);
  const [environmentalContext, setEnvironmentalContext] = useState({
    time: "", greeting: "", weather: "Clear", hour: 12,
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { isOnline } = useSyncEngine();
  
  const calendarAwareSuggestions = useMemo(() => buildCalendarAwareSuggestions(upcomingEvents), [upcomingEvents]);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  useEffect(() => scrollToBottom(), [messages, isTyping]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) setShowContextDropdown(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Load upcoming events for calendar-aware suggestions
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const now = new Date();
        const start = now.toISOString().slice(0, 10);
        const end = new Date(now.getFullYear(), now.getMonth() + 1, now.getDate()).toISOString().slice(0, 10);
        const events = await getEvents(start, end);
        if (!mounted) return;
        if (Array.isArray(events)) setUpcomingEvents(events as CalendarEvent[]);
      } catch (err) {
        console.error("[AICopilotChat] failed to load events:", err);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    const updateContext = () => {
      const now = new Date();
      const hour = now.getHours();
      let greeting = "Good evening";
      if (hour < 12) greeting = "Good morning";
      else if (hour < 17) greeting = "Good afternoon";

      setEnvironmentalContext({
        time: now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        greeting,
        weather: hour < 18 ? "Clear" : "Clear Night",
        hour,
      });
    };
    updateContext();
    const timer = setInterval(updateContext, 60000);
    return () => clearInterval(timer);
  }, []);

  const handleSuggestedAction = (action: SuggestedAction) => {
    const promptText = action.data?.prompt as string || `Help me with: ${action.label}`;
    setInput(promptText);
    setTimeout(() => handleSubmit({ preventDefault: () => {} } as FormEvent, promptText), 50);
  };

  const handleSubmit = async (e: FormEvent, promptText?: string) => {
    e.preventDefault();
    const textToSend = promptText || input;
    if (!textToSend.trim() || isTyping) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: textToSend,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);
    inputRef.current?.blur();

    try {
      const contextArray = upcomingEvents.map((ev) => `Event: ${normalizeEventTitle(ev.title)} at ${new Date(ev.start_time).toLocaleString()}`);
      const data = await sendAiChat(userMessage.content, contextArray, Intl.DateTimeFormat().resolvedOptions().timeZone);

      const aiMessage: Message = {
        id: `ai-${Date.now()}`,
        role: "ai",
        content: data.result || "I couldn't process that request.",
        timestamp: new Date(),
        metadata: {
          eventCreated: data.result?.includes("(Scheduled)"),
        },
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch {
      setMessages((prev) => [...prev, {
        id: `err-${Date.now()}`, role: "ai", content: "I'm experiencing difficulty connecting right now.", timestamp: new Date(),
      }]);
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

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-[#F8F9FA] relative selection:bg-[#D2E3FC]">
      
      {/* HEADER */}
      <div className="flex h-16 shrink-0 items-center justify-between px-6 border-b border-[#DADCE0] bg-white sticky top-0 z-10">
        <div className="flex items-center gap-4">
            {isOnline ? (
              <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider text-[#137333] bg-[#E6F4EA]">
                 <Wifi className="h-3 w-3" /> Online
              </span>
            ) : (
              <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider text-[#B3261E] bg-[#F9DEDC]">
                 <CloudOff className="h-3 w-3" /> Offline
              </span>
            )}

            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setShowContextDropdown(!showContextDropdown)}
                className="flex items-center gap-2 text-sm font-medium text-[#5F6368] hover:text-[#202124] hover:bg-[#F1F3F4] px-3 py-1.5 rounded-full transition-colors"
              >
                <Calendar className="h-4 w-4" />
                <span>Context & Events ({upcomingEvents.length})</span>
              </button>
               
              <AnimatePresence>
                {showContextDropdown && (
                  <motion.div
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 5 }}
                    className="absolute left-0 top-full mt-2 w-72 rounded-2xl border border-[#DADCE0] bg-white p-4 shadow-lg z-50"
                  >
                    <div className="mb-3 flex items-center justify-between text-[#5F6368]">
                      <span className="text-[10px] font-bold uppercase tracking-wider">Local Context</span>
                      <div className="flex items-center gap-2 text-xs font-medium">
                        {environmentalContext.hour > 18 ? <Moon className="h-3 w-3" /> : <Sun className="h-3 w-3" />}
                        {environmentalContext.time}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
        </div>

        <button
          onClick={() => setMessages([])}
          className="p-2 text-[#5F6368] hover:bg-[#F1F3F4] rounded-full transition-colors"
          title="New Chat"
        >
          <RefreshCw className="h-5 w-5" />
        </button>
      </div>

      {messages.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center px-4 overflow-y-auto pb-20">
          <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="mb-6">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#E8F0FE] text-[#1A73E8]">
              <Sparkles className="h-8 w-8" />
            </div>
          </motion.div>

          <motion.div initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }} className="text-center">
            <h1 className="text-3xl sm:text-4xl font-normal text-[#202124] tracking-tight">
              {environmentalContext.greeting}, {displayName}
            </h1>
            <p className="mt-2 text-[#5F6368] text-base">
              {upcomingEvents.length > 0 ? `You have ${upcomingEvents.length} upcoming meetings. How can I help you prepare?` : "Your calendar is clear today."}
            </p>
          </motion.div>

          <motion.div initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }} className="mt-10 grid w-full max-w-3xl grid-cols-1 sm:grid-cols-2 gap-4">
            {calendarAwareSuggestions.map((suggestion) => (
              <button
                key={suggestion.id}
                onClick={() => handleSuggestedAction(suggestion)}
                className="flex items-start gap-4 p-5 rounded-2xl border border-[#DADCE0] bg-white hover:border-[#1A73E8] hover:shadow-sm transition-all text-left group"
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#F1F3F4] text-[#5F6368] group-hover:bg-[#E8F0FE] group-hover:text-[#1A73E8] transition-colors">
                  {getSuggestionIcon(suggestion.icon)}
                </div>
                <div>
                  <p className="text-base font-medium text-[#202124]">{suggestion.label}</p>
                  <p className="text-sm text-[#5F6368] mt-1 line-clamp-2">{suggestion.description}</p>
                </div>
              </button>
            ))}
          </motion.div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto px-4 sm:px-0">
          <div className="mx-auto max-w-3xl py-8 space-y-8">
            <AnimatePresence initial={false}>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn("flex", msg.role === "user" ? "justify-end" : "justify-start")}
                >
                  {msg.role === "ai" ? (
                    <div className="flex items-start gap-4 max-w-[85%] sm:max-w-[75%]">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#E8F0FE] text-[#1A73E8]">
                        <Sparkles className="h-4 w-4" />
                      </div>
                      <div className="bg-white border border-[#DADCE0] rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm text-[#202124] text-[15px] leading-relaxed">
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-[#1A73E8] text-white rounded-2xl rounded-tr-sm px-5 py-4 shadow-sm max-w-[85%] sm:max-w-[75%] text-[15px] leading-relaxed">
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  )}
                </motion.div>
              ))}
              
              {isTyping && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                  <div className="flex items-start gap-4">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#E8F0FE] text-[#1A73E8]">
                      <Bot className="h-4 w-4 animate-pulse" />
                    </div>
                    <div className="bg-white border border-[#DADCE0] rounded-2xl rounded-tl-sm px-5 py-4 flex items-center gap-1.5 h-[52px]">
                       <span className="w-2 h-2 rounded-full bg-[#DADCE0] animate-bounce dot-delay-0" />
                       <span className="w-2 h-2 rounded-full bg-[#DADCE0] animate-bounce dot-delay-150" />
                       <span className="w-2 h-2 rounded-full bg-[#DADCE0] animate-bounce dot-delay-300" />
                    </div>
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} className="h-4" />
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* COMPOSER WIDGET */}
      <div className="px-4 pb-6 pt-2 bg-gradient-to-t from-[#F8F9FA] via-[#F8F9FA] to-transparent shrink-0">
        <div className="mx-auto max-w-3xl">
          <form 
            onSubmit={handleSubmit} 
            className="relative flex items-end gap-2 rounded-[28px] border border-[#DADCE0] bg-white pl-6 pr-2 py-2 shadow-sm focus-within:border-[#1A73E8] focus-within:ring-1 focus-within:ring-[#1A73E8]/20 transition-all"
          >
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about your schedule..."
              className="flex-1 max-h-32 min-h-[40px] resize-none border-0 bg-transparent py-2.5 text-[#202124] placeholder:text-[#5F6368] focus:ring-0 focus:outline-none text-base"
              rows={1}
              onInput={(e) => {
                const t = e.target as HTMLTextAreaElement;
                t.style.height = "auto";
                t.style.height = Math.min(t.scrollHeight, 128) + "px";
              }}
            />
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className="mb-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#1A73E8] text-white transition-colors hover:bg-[#1557B0] disabled:bg-[#F1F3F4] disabled:text-[#9AA0A6]"
            >
              {isTyping ? <Loader2 className="h-5 w-5 animate-spin" /> : <ArrowUp className="h-5 w-5" />}
            </button>
          </form>
          <div className="text-center mt-3 text-xs text-[#5F6368]">
            AI can make mistakes. Verify important scheduling details.
          </div>
        </div>
      </div>
    </div>
  );
}

