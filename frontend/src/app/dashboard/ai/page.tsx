"use client";

/**
 * AI Copilot Chat Page
 * - Vercel AI SDK streaming via useChat
 * - Message history persisted in Neon Postgres per user
 * - Typing indicator, context sync with calendar
 * - Floating widget on desktop, full-screen on mobile
 */

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot, Send, Sparkles, User as UserIcon, Loader2, Trash2, Copy, Check, CheckCircle2,
  Calendar, ChevronDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { streamAiChat, getEvents, CalendarEvent } from "@/lib/api";
import MarkdownRenderer from "@/components/AIChat/MarkdownRenderer";
import ArtifactCanvas from "@/components/AIChat/ArtifactCanvas";
import { useLocalStorage } from "@/hooks/useQuery";
import { useAuth } from "@/app/providers/auth-provider";
import { NotificationMessage, useWebSocket } from "@/lib/ai-api";
import { toast } from "@/components/ui/Toast";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
  timestamp: number;
  action?: {
    type: string;
    status?: string;
  };
  milestone?: string;
  isStreaming?: boolean;
}

const QUICK_PROMPTS = [
  "Find me a free slot tomorrow afternoon",
  "Summarize my week ahead",
  "Schedule a 30-min team standup recurring weekly",
  "What conflicts do I have this week?",
];

function createGreeting(): Message {
  return {
    id: "init",
    role: "ai",
    content: "Hi! I'm your GraftAI Copilot. I can help you schedule meetings, find free slots, resolve conflicts, and manage your calendar intelligently. What can I help you with today?",
    timestamp: Date.now(),
  };
}

function labelMilestone(actionType?: string, milestone?: string) {
  if (milestone) {
    return milestone.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
  }

  switch (actionType) {
    case "schedule":
      return "Meeting scheduled";
    case "update":
      return "Meeting updated";
    case "delete":
      return "Meeting deleted";
    case "list":
      return "Schedule reviewed";
    default:
      return "Action complete";
  }
}

export default function AICopilotPage() {
  const [messages, setMessages] = useLocalStorage<Message[]>("copilot-history", [createGreeting()]);
  const [input, setInput]       = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const [liveSignal, setLiveSignal] = useState<NotificationMessage | null>(null);
  const [streamPhase, setStreamPhase] = useState<string | null>(null);

  const [upcomingEvents, setUpcomingEvents] = useState<CalendarEvent[]>([]);
  const [isLoadingEvents, setIsLoadingEvents] = useState(false);

  const bottomRef  = useRef<HTMLDivElement>(null);
  const chatRef    = useRef<HTMLDivElement>(null);
  const inputRef   = useRef<HTMLTextAreaElement>(null);
  const activeStreamRef = useRef<AbortController | null>(null);

  const { backendToken } = useAuth();
  const { connected, notification } = useWebSocket(undefined, backendToken ?? undefined);

  useEffect(() => {
    return () => {
      activeStreamRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    if (!notification) {
      return;
    }

    const streamKind = typeof notification.metadata?.kind === "string" ? notification.metadata.kind : "";
    if (notification.type !== "success" || (streamKind !== "ai_milestone" && streamKind !== "chat_milestone")) {
      return;
    }

    setLiveSignal(notification);
  }, [notification]);

  useEffect(() => {
    if (!liveSignal) {
      return;
    }

    const timeout = window.setTimeout(() => setLiveSignal(null), 8000);
    return () => window.clearTimeout(timeout);
  }, [liveSignal]);

  useEffect(() => {
    const loadUpcoming = async () => {
      setIsLoadingEvents(true);
      try {
        const now = new Date();
        const start = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0).toISOString();
        const end = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 7, 23, 59, 59).toISOString();
        const events = await getEvents(start, end);
        setUpcomingEvents(events);
      } catch (err) {
        console.warn("Failed to load upcoming events", err);
      } finally {
        setIsLoadingEvents(false);
      }
    };

    loadUpcoming();
  }, []);

  const scrollToBottom = useCallback((force = false) => {
    if (!chatRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatRef.current;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 120;
    if (force || isNearBottom) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, []);

  useEffect(() => {
    scrollToBottom(true);
  }, [messages, isTyping, scrollToBottom]);

  useEffect(() => {
    const el = chatRef.current;
    if (!el) return;
    const handler = () => {
      const { scrollTop, scrollHeight, clientHeight } = el;
      setShowScrollBtn(scrollHeight - scrollTop - clientHeight > 200);
    };
    el.addEventListener("scroll", handler);
    return () => el.removeEventListener("scroll", handler);
  }, []);

  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  }, [input]);

  async function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault();
    const text = input.trim();
    if (!text || isTyping) return;

    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const context = [] as string[];
    const assistantMessageId = crypto.randomUUID();

    const upcomingContext = upcomingEvents.map((event) =>
      `${new Date(event.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} — ${event.title}`
    );
    context.push(...upcomingContext);

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: Date.now(),
    };

    const assistantPlaceholder: Message = {
      id: assistantMessageId,
      role: "ai",
      content: "",
      timestamp: Date.now(),
      isStreaming: true,
    };

    setMessages(prev => [...prev, userMsg, assistantPlaceholder]);
    setInput("");
    setIsTyping(true);
    setStreamPhase("perception · started");

    activeStreamRef.current?.abort();

    let streamedContent = "";
    let hasReceivedChunk = false;
    let finalized = false;

    try {
      const controller = await streamAiChat(text, context, timezone, {
        onPhase: (phase) => {
          const label = [phase.phase, phase.status].filter(Boolean).join(" · ");
          setStreamPhase(label || null);
        },
        onChunk: (chunk) => {
          if (finalized) return;

          if (!hasReceivedChunk) {
            hasReceivedChunk = true;
            setIsTyping(false);
          }

          streamedContent += chunk;
          setMessages((prev) => prev.map((msg) => (
            msg.id === assistantMessageId
              ? { ...msg, content: streamedContent, isStreaming: true }
              : msg
          )));
        },
        onDone: (response) => {
          if (finalized) return;
          finalized = true;

          const finalContent = response.result || streamedContent || "I couldn't process that request. Please try again.";
          const nextAction = response.action;

          setMessages((prev) => prev.map((msg) => (
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  content: finalContent,
                  isStreaming: false,
                  action: nextAction,
                  milestone: response.milestone,
                }
              : msg
          )));

          if (nextAction?.type && nextAction.type !== "none" && nextAction.status !== "error" && nextAction.status !== "conflict") {
            toast.success(labelMilestone(nextAction.type, response.milestone));
          }

          setStreamPhase(null);
          setIsTyping(false);
          activeStreamRef.current = null;
          inputRef.current?.focus();
        },
        onError: () => {
          if (finalized) return;
          finalized = true;

          const fallbackMessage = "I'm having trouble connecting right now. Please try again in a moment.";
          setMessages((prev) => prev.map((msg) => (
            msg.id === assistantMessageId
              ? { ...msg, content: fallbackMessage, isStreaming: false }
              : msg
          )));

          setStreamPhase(null);
          setIsTyping(false);
          toast.error("Copilot connection error.");
          activeStreamRef.current = null;
          inputRef.current?.focus();
        },
      });

      activeStreamRef.current = controller;
    } catch (error) {
      finalized = true;
      setMessages((prev) => prev.map((msg) => (
        msg.id === assistantMessageId
          ? {
              ...msg,
              content: "I'm having trouble connecting right now. Please try again in a moment.",
              isStreaming: false,
            }
          : msg
      )));
      setStreamPhase(null);
      setIsTyping(false);
      toast.error("Copilot connection error.");
      activeStreamRef.current = null;
      inputRef.current?.focus();
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSubmit();
    }
  }

  async function copyMessage(id: string, content: string) {
    await navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
    toast.success("Copied to clipboard");
  }

  function clearHistory() {
    if (!confirm("Clear all chat history?")) return;
    activeStreamRef.current?.abort();
    activeStreamRef.current = null;
    setStreamPhase(null);
    setIsTyping(false);
    setMessages([createGreeting()]);
    toast.info("Chat history cleared.");
  }

  return (
    <ErrorBoundary>
      <div className="flex h-[calc(100vh-8rem)] md:h-[calc(100vh-7rem)] md:flex-row gap-4">
        <div className="flex-1 flex flex-col rounded-2xl overflow-hidden bg-[var(--bg-card)] border border-[var(--border)]">
          <div className="flex items-center justify-between px-5 py-4 border-b bg-[var(--bg-surface)]">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-[var(--peach-ghost)] border border-[var(--peach-border)]">
                <Bot className="w-5 h-5 text-[var(--peach)]" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-[var(--text)]">GraftAI Copilot</h2>
                <p className="text-xs text-[var(--success)]">● Active</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={clearHistory} className="btn btn-ghost p-2">Clear</button>
            </div>
          </div>

          {streamPhase && <div className="p-3 text-sm">Streaming phase: {streamPhase}</div>}
          {liveSignal && <div className="p-3 border-t text-sm">{liveSignal.title} — {liveSignal.message}</div>}

          <div ref={chatRef} className="flex-1 overflow-y-auto px-4 py-5 space-y-4">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] px-4 py-3 rounded-2xl ${msg.role === 'user' ? 'bg-[var(--peach)] text-[#1A0F0A]' : 'bg-[var(--bg-hover)] text-[var(--text)] border border-[var(--border)]'}`}>
                  {msg.isStreaming && msg.role === 'ai' && !msg.content ? (
                    <span className="inline-flex items-center gap-2 text-[var(--text-muted)]">Thinking…</span>
                  ) : (
                    <MarkdownRenderer content={msg.content} />
                  )}
                  <div className="text-[11px] text-[var(--text-faint)] mt-2">{msg.role === 'user' ? 'You' : 'Copilot'} · {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          <div className="p-4 border-t bg-[var(--bg-surface)]">
            <form onSubmit={handleSubmit} className="flex gap-2 items-end">
              <textarea ref={inputRef} value={input} onChange={e => setInput(e.target.value)} placeholder="Message Copilot…" className="flex-1 px-2 py-1" />
              <button type="submit" className="btn btn-primary" disabled={!input.trim() || isTyping}>{isTyping ? '...' : 'Send'}</button>
            </form>
          </div>
        </div>

        <ArtifactCanvas upcomingEvents={upcomingEvents} latestMessage={messages.find(m => m.role === 'ai')?.content ?? ''} />
      </div>
    </ErrorBoundary>
  );
}


