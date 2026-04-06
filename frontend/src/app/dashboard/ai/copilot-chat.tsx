"use client";

import { useState, useRef, useEffect, FormEvent, KeyboardEvent } from "react";
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
  ChevronDown,
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

export default function AICopilotChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [contextPanel, setContextPanel] = useState(true);
  const [upcomingEvents, setUpcomingEvents] = useState<CalendarEvent[]>([]);
  const [environmentalContext, setEnvironmentalContext] = useState({
    time: "",
    greeting: "",
    weather: "Clear",
    timezone: "",
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

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
    if (messages.length === 0) {
      const welcomeMessage: Message = {
        id: "welcome",
        role: "ai",
        content: `${environmentalContext.greeting}! I'm your GraftAI Copilot, ready to help you orchestrate your schedule with precision and intelligence. I have full context of your calendar, timezone, and preferences.

I can help you:
• Schedule meetings and events intelligently
• Find optimal time slots across timezones
• Reschedule conflicts automatically
• Analyze your calendar patterns
• Coordinate with multiple participants

What would you like to accomplish today?`,
        timestamp: new Date(),
        suggestedActions: [
          {
            id: "1",
            type: "schedule",
            label: "Schedule a meeting",
            description: "Find the best time for your next meeting",
          },
          {
            id: "2",
            type: "query",
            label: "Show my week",
            description: "Get an overview of your upcoming schedule",
          },
          {
            id: "3",
            type: "query",
            label: "Find free slots",
            description: "Discover available time windows",
          },
        ],
      };
      setMessages([welcomeMessage]);
    }
  }, [environmentalContext.greeting, messages.length]);

  const handleSuggestedAction = async (action: SuggestedAction) => {
    let prompt = "";
    switch (action.type) {
      case "schedule":
        prompt = "I need to schedule a new meeting";
        break;
      case "query":
        if (action.label.includes("week")) {
          prompt = "Show me my schedule for this week";
        } else if (action.label.includes("free")) {
          prompt = "What are my available time slots today?";
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
        content: `Conversation cleared. ${environmentalContext.greeting}! How can I help you orchestrate your schedule today?`,
        timestamp: new Date(),
      };
      setMessages([welcomeMessage]);
    }, 100);
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] bg-white dark:bg-slate-950 rounded-3xl border border-slate-200/60 dark:border-slate-800/60 shadow-2xl overflow-hidden">
      <AnimatePresence>
        {contextPanel && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 320, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="border-r border-slate-200/60 dark:border-slate-800/60 bg-slate-50/50 dark:bg-slate-900/20 flex flex-col overflow-hidden"
          >
            <div className="p-6 border-b border-slate-200/60 dark:border-slate-800/60">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">Context</h3>
                <button
                  onClick={() => setContextPanel(false)}
                  className="p-1.5 rounded-lg hover:bg-slate-200/50 dark:hover:bg-slate-800/50 transition-colors"
                  aria-label="Close context panel"
                >
                  <X className="w-4 h-4 text-slate-400" />
                </button>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 rounded-2xl bg-white dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-800/50">
                  {environmentalContext.weather.includes("Night") ? (
                    <Moon className="w-5 h-5 text-indigo-400" />
                  ) : environmentalContext.weather.includes("Cloud") ? (
                    <Cloud className="w-5 h-5 text-slate-400" />
                  ) : (
                    <Sun className="w-5 h-5 text-amber-400" />
                  )}
                  <div className="flex-1">
                    <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Time</p>
                    <p className="text-sm font-semibold text-slate-900 dark:text-white">{environmentalContext.time}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 rounded-2xl bg-white dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-800/50">
                  <MapPin className="w-5 h-5 text-emerald-400" />
                  <div className="flex-1">
                    <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Timezone</p>
                    <p className="text-xs font-semibold text-slate-900 dark:text-white truncate">{environmentalContext.timezone}</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">Upcoming</h3>
                <span className="text-xs font-bold text-slate-500 dark:text-slate-400 bg-slate-200/50 dark:bg-slate-800/50 px-2 py-1 rounded-full">
                  {upcomingEvents.length}
                </span>
              </div>

              <div className="space-y-3">
                {upcomingEvents.length > 0 ? (
                  upcomingEvents.map((event) => (
                    <motion.div
                      key={event.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="p-4 rounded-2xl bg-white dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-800/50 hover:shadow-md transition-all group"
                    >
                      <div className="flex items-start gap-3">
                        <div
                          className={cn(
                            "w-2 h-2 rounded-full mt-2 shrink-0",
                            event.category === "meeting"
                              ? "bg-violet-500"
                              : event.category === "event"
                              ? "bg-yellow-500"
                              : event.category === "task"
                              ? "bg-cyan-500"
                              : "bg-pink-500"
                          )}
                        />
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-semibold text-slate-900 dark:text-white truncate mb-1">{event.title}</h4>
                          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                            <Clock className="w-3 h-3" />
                            {new Date(event.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))
                ) : (
                  <div className="py-12 text-center">
                    <Calendar className="w-8 h-8 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
                    <p className="text-sm text-slate-400 dark:text-slate-500 font-medium">No upcoming events</p>
                  </div>
                )}
              </div>
            </div>

            <div className="p-6 border-t border-slate-200/60 dark:border-slate-800/60">
              <button
                onClick={() => setInput("What's my schedule like today?")}
                className="w-full py-2.5 px-4 rounded-xl text-xs font-bold text-primary bg-primary/10 hover:bg-primary/20 border border-primary/20 transition-all flex items-center justify-center gap-2"
              >
                <Sparkles className="w-3.5 h-3.5" />
                Ask about schedule
              </button>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-between p-6 border-b border-slate-200/60 dark:border-slate-800/60 bg-white/80 dark:bg-slate-900/40 backdrop-blur-xl">
          <div className="flex items-center gap-4">
            {!contextPanel && (
              <button
                onClick={() => setContextPanel(true)}
                className="p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800/50 transition-colors"
                aria-label="Open context panel"
              >
                <ChevronDown className="w-5 h-5 text-slate-400 rotate-90" />
              </button>
            )}
            <div className="relative">
              <div className="p-2.5 rounded-2xl bg-gradient-to-br from-primary to-violet-600 text-white shadow-lg shadow-primary/20">
                <Bot className="w-6 h-6" />
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full bg-emerald-500 border-2 border-white dark:border-slate-900 flex items-center justify-center">
                <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
              </span>
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">GraftAI Copilot</h2>
              <div className="flex items-center gap-2">
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold uppercase tracking-wider">Calendar-Aware</span>
                <span className="text-xs text-slate-400 dark:text-slate-500 font-medium">Context: {upcomingEvents.length} events</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={clearConversation}
              className="p-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800/50 transition-colors group"
              title="Clear conversation"
            >
              <RefreshCw className="w-4 h-4 text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300" />
            </button>
            <button className="p-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800/50 transition-colors group" title="More actions">
              <MoreHorizontal className="w-4 h-4 text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 20, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
                className={cn("flex max-w-[85%]", msg.role === "user" ? "ml-auto" : "mr-auto")}
              >
                <div className={cn("flex gap-4 w-full", msg.role === "user" ? "flex-row-reverse" : "flex-row")}>
                  <div className={cn(
                    "w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 shadow-sm",
                    msg.role === "user"
                      ? "bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                      : "bg-gradient-to-br from-primary to-violet-600 border border-primary/20"
                  )}>
                    {msg.role === "user" ? (
                      <UserIcon className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                    ) : (
                      <Sparkles className="w-5 h-5 text-white" />
                    )}
                  </div>

                  <div className={cn("flex flex-col gap-2 flex-1", msg.role === "user" ? "items-end" : "items-start")}> 
                    <div className={cn(
                      "px-5 py-4 rounded-2xl shadow-sm transition-all max-w-full",
                      msg.role === "user"
                        ? "bg-gradient-to-br from-primary to-violet-600 text-white rounded-tr-none"
                        : "bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 text-slate-700 dark:text-slate-300 rounded-tl-none"
                    )}>
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        <p className="text-[14px] leading-relaxed whitespace-pre-wrap m-0">{msg.content}</p>
                      </div>

                      {msg.metadata?.eventCreated && (
                        <div className="mt-3 pt-3 border-t border-white/10 flex items-center gap-2 text-xs">
                          <CheckCircle2 className="w-4 h-4" />
                          <span className="font-medium">Event created successfully</span>
                        </div>
                      )}
                      {msg.metadata?.eventModified && (
                        <div className="mt-3 pt-3 border-t border-slate-200/50 dark:border-slate-700/50 flex items-center gap-2 text-xs">
                          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                          <span className="font-medium text-emerald-600 dark:text-emerald-400">Event updated successfully</span>
                        </div>
                      )}
                      {msg.metadata?.eventDeleted && (
                        <div className="mt-3 pt-3 border-t border-slate-200/50 dark:border-slate-700/50 flex items-center gap-2 text-xs">
                          <CheckCircle2 className="w-4 h-4 text-amber-500" />
                          <span className="font-medium text-amber-600 dark:text-amber-400">Event deleted successfully</span>
                        </div>
                      )}
                    </div>

                    {msg.contextUsed && msg.contextUsed.length > 0 && (
                      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
                        <Lightbulb className="w-3 h-3 text-amber-500" />
                        <span className="text-xs font-medium text-slate-600 dark:text-slate-400">Used context: {msg.contextUsed.join(", ")}</span>
                      </div>
                    )}

                    {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-1">
                        {msg.suggestedActions.map((action) => (
                          <button
                            key={action.id}
                            onClick={() => handleSuggestedAction(action)}
                            className="group px-4 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-primary/50 dark:hover:border-primary/50 transition-all shadow-sm hover:shadow-md"
                          >
                            <div className="flex items-center gap-2">
                              <Sparkles className="w-3.5 h-3.5 text-primary opacity-60 group-hover:opacity-100 transition-opacity" />
                              <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 group-hover:text-primary transition-colors">{action.label}</span>
                            </div>
                          </button>
                        ))}
                      </div>
                    )}

                    <span className="text-[10px] text-slate-400 dark:text-slate-500 px-2 font-medium">{msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                  </div>
                </div>
              </motion.div>
            ))}

            {isTyping && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex mr-auto max-w-[85%]"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 bg-gradient-to-br from-primary to-violet-600 shadow-lg">
                    <Bot className="w-5 h-5 text-white animate-pulse" />
                  </div>
                  <div className="flex gap-2 px-5 py-4 bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 rounded-2xl rounded-tl-none shadow-sm">
                    <span className="w-2 h-2 rounded-full bg-primary/40 animate-bounce [animation-delay:-0.3s]" />
                    <span className="w-2 h-2 rounded-full bg-primary/40 animate-bounce [animation-delay:-0.15s]" />
                    <span className="w-2 h-2 rounded-full bg-primary/40 animate-bounce" />
                  </div>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </AnimatePresence>
        </div>

        <div className="p-6 border-t border-slate-200/60 dark:border-slate-800/60 bg-white/80 dark:bg-slate-950/60 backdrop-blur-xl">
          <form onSubmit={handleSubmit} className="relative group max-w-4xl mx-auto">
            <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-violet-500/10 rounded-2xl blur-xl transition-all duration-300 group-focus-within:opacity-100 opacity-0" />
            <div className="relative flex gap-3 p-2 bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-2xl shadow-xl transition-all group-focus-within:border-primary/50 group-focus-within:ring-4 group-focus-within:ring-primary/5">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything about your schedule, or describe what you need..."
                rows={1}
                className="flex-1 min-h-[44px] bg-transparent px-4 py-3 text-sm text-slate-800 dark:text-slate-100 placeholder-slate-400/80 focus:outline-none resize-none max-h-32"
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = "auto";
                  target.style.height = Math.min(target.scrollHeight, 128) + "px";
                }}
              />
              <button
                type="submit"
                disabled={!input.trim() || isTyping}
                className="px-5 py-3 rounded-xl bg-gradient-to-br from-primary to-violet-600 hover:from-primary/90 hover:to-violet-600/90 disabled:opacity-30 disabled:grayscale text-white font-bold text-sm transition-all shadow-lg shadow-primary/20 flex items-center gap-2 shrink-0"
              >
                {isTyping ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
                <span className="hidden sm:inline">Send</span>
              </button>
            </div>
            <div className="mt-4 flex flex-wrap items-center justify-center gap-4">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest bg-slate-100 dark:bg-slate-800/50 px-3 py-1.5 rounded-full border border-slate-200/50 dark:border-slate-700/50">
                <Sparkles className="w-3 h-3 text-primary" />
                <span>AI Orchestration Active</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest bg-slate-100 dark:bg-slate-800/50 px-3 py-1.5 rounded-full border border-slate-200/50 dark:border-slate-700/50">
                <Calendar className="w-3 h-3 text-violet-400" />
                <span>{upcomingEvents.length} Events Loaded</span>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
