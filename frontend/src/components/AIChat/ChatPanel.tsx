"use client";

import { useState, useRef, useEffect, type ReactNode } from "react";
import { Send, X, Calendar, Clock, Users, Sparkles, Bot, Loader2 } from "lucide-react";
import { sendAiChat, getEvents } from "@/lib/api";
import MarkdownRenderer from "@/components/AIChat/MarkdownRenderer";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface QuickAction {
  label: string;
  icon: ReactNode;
  prompt: string;
}

interface CalendarEvent {
  id: string | number;
  title: string;
  start_time: string;
  end_time: string;
  status: string;
}

export default function ChatPanel({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [upcomingEvents, setUpcomingEvents] = useState<CalendarEvent[]>([]);
  const [isLoadingEvents, setIsLoadingEvents] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const quickActions: QuickAction[] = [
    { label: "Schedule Meeting", icon: <Calendar size={18} />, prompt: "Schedule a meeting for tomorrow" },
    { label: "Check Availability", icon: <Clock size={18} />, prompt: "What is my availability today?" },
    { label: "Team Sync", icon: <Users size={18} />, prompt: "Find a time for a team sync" },
  ];

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  useEffect(() => {
    if (!isOpen) return;

    const loadTodayEvents = async () => {
      setIsLoadingEvents(true);
      try {
        const now = new Date();
        const start = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0).toISOString();
        const end = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59).toISOString();
        const events = await getEvents(start, end);
        setUpcomingEvents(events);
      } catch (error) {
        console.warn("Unable to load events for AI chat", error);
      } finally {
        setIsLoadingEvents(false);
      }
    };

    loadTodayEvents();
  }, [isOpen]);

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;

    const prompt = input.trim();
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: prompt,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    try {
      const context = upcomingEvents.map((event) =>
        `${new Date(event.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} — ${event.title}`
      );
      const response = await sendAiChat(prompt, context, Intl.DateTimeFormat().resolvedOptions().timeZone);

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.result || "I couldn't process that request.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Sorry, I am having trouble connecting right now. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleQuickAction = (action: QuickAction) => {
    setInput(action.prompt);
    inputRef.current?.focus();
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[420px] border-l flex flex-col shadow-2xl z-50" style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-subtle)' }}>
      <div className="flex items-center justify-between p-4" style={{ borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-surface)' }}>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ background: 'var(--primary-glow)', color: 'var(--primary)' }}>
            <Sparkles size={20} style={{ color: 'var(--primary)' }} />
          </div>
          <div>
            <h3 className="text-[#202124] font-semibold text-sm">GraftAI Assistant</h3>
            <p className="text-[#5F6368] text-xs flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#137333]" /> Online
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          aria-label="Close chat panel"
          title="Close chat panel"
          className="p-2 hover:bg-[#E8EAED] rounded-full transition-colors text-[#5F6368]"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6" style={{ background: 'var(--bg-surface)' }}>
        {messages.length === 0 && (
          <div className="text-center py-8">
            <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-white border flex items-center justify-center shadow-sm" style={{ borderColor: 'var(--border-subtle)' }}>
              <Calendar className="w-7 h-7" style={{ color: 'var(--primary)' }} />
            </div>
            <h4 className="text-[#202124] font-medium mb-2">How can I help?</h4>
            <p className="text-[#5F6368] text-sm mb-8 px-4">
              Schedule meetings, check your availability, or manage your calendar instantly.
            </p>

            <div className="space-y-3 px-2">
              {quickActions.map((action) => (
                <button
                  key={action.label}
                  type="button"
                  onClick={() => handleQuickAction(action)}
                  className="w-full flex items-center gap-3 px-4 py-3 bg-white hover:shadow-sm rounded-2xl transition-all text-left"
                  style={{ border: '1px solid var(--border-subtle)' }}
                >
                  <span className="text-[#5F6368] bg-[#F1F3F4] p-2 rounded-xl transition-colors">
                    {action.icon}
                  </span>
                  <span className="text-[#202124] text-sm font-medium">{action.label}</span>
                </button>
              ))}
            </div>

            <div className="mt-6 text-left text-xs text-[#5F6368] px-4">
              {isLoadingEvents
                ? "Fetching today's schedule..."
                : upcomingEvents.length > 0
                ? `Found ${upcomingEvents.length} event${upcomingEvents.length === 1 ? "" : "s"} today.`
                : "No events found for today."}
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
            {message.role === "assistant" && (
              <div className="w-8 h-8 shrink-0 rounded-full flex items-center justify-center mr-3 mt-1" style={{ background: 'var(--primary-glow)', color: 'var(--primary)' }}>
                  <Sparkles size={14} style={{ color: 'var(--primary)' }} />
                </div>
            )}
                <div
              className={`max-w-[80%] px-4 py-3 text-[14px] leading-relaxed shadow-sm ${
                message.role === "user"
                  ? "text-white rounded-2xl rounded-tr-sm"
                  : "bg-white text-[#202124] rounded-2xl rounded-tl-sm"
              }`}
              style={
                message.role === "user"
                  ? { background: 'var(--primary)' }
                  : { border: '1px solid var(--border-subtle)', background: 'var(--bg-base)' }
              }
            >
              <MarkdownRenderer content={message.content} />
              <p className="text-[10px] opacity-60 mt-2 text-right">
                {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </p>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="w-8 h-8 shrink-0 rounded-full flex items-center justify-center mr-3 mt-1" style={{ background: 'var(--primary-glow)', color: 'var(--primary)' }}>
              <Bot size={14} style={{ color: 'var(--primary)' }} />
            </div>
            <div className="rounded-2xl rounded-tl-sm px-4 py-4 flex items-center gap-1.5 h-[46px] shadow-sm" style={{ border: '1px solid var(--border-subtle)', background: 'var(--bg-base)' }}>
              <span className="w-2 h-2 rounded-full bg-[#DADCE0] animate-bounce dot-delay-0" />
              <span className="w-2 h-2 rounded-full bg-[#DADCE0] animate-bounce dot-delay-150" />
              <span className="w-2 h-2 rounded-full bg-[#DADCE0] animate-bounce dot-delay-300" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} className="h-2" />
      </div>

      <div className="p-4" style={{ borderTop: '1px solid var(--border-subtle)', background: 'var(--bg-surface)' }}>
      <div className="relative flex items-center rounded-[24px] px-2 py-1.5 transition-all" style={{ border: '1px solid var(--border-subtle)', background: 'var(--bg-elevated)' }}>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask your assistant..."
            className="flex-1 bg-transparent border-none px-3 text-[#202124] placeholder:text-[#5F6368] focus:outline-none text-sm"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            aria-label="Send message"
            title="Send message"
            className="w-9 h-9 flex items-center justify-center rounded-full transition-colors disabled:bg-[#DADCE0] disabled:text-[#9AA0A6]"
            style={{ background: 'var(--primary)', color: '#fff' }}
          >
            {isTyping ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} className="ml-0.5" />}
          </button>
        </div>
        <p className="text-[#5F6368] text-[11px] mt-2.5 text-center">
          AI may make mistakes. Verify important information.
        </p>
      </div>
    </div>
  );
}
