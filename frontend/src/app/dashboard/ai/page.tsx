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
import { sendAiChat } from "@/lib/api";
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

  const bottomRef  = useRef<HTMLDivElement>(null);
  const chatRef    = useRef<HTMLDivElement>(null);
  const inputRef   = useRef<HTMLTextAreaElement>(null);

  const { backendToken } = useAuth();
  const { connected, notification } = useWebSocket(undefined, backendToken ?? undefined);

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

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: Date.now(),
    };

    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const { result, action, milestone } = await sendAiChat(text, undefined, timezone);
      if (action?.type && action.type !== "none" && action.status !== "error" && action.status !== "conflict") {
        toast.success(labelMilestone(action.type, milestone));
      }

      const aiMsg: Message = {
        id: crypto.randomUUID(),
        role: "ai",
        content: result || "I couldn't process that request. Please try again.",
        timestamp: Date.now(),
        action,
        milestone,
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "ai",
        content: "I'm having trouble connecting right now. Please try again in a moment.",
        timestamp: Date.now(),
      };
      setMessages(prev => [...prev, aiMsg]);
      toast.error("Copilot connection error.");
    } finally {
      setIsTyping(false);
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
    setMessages([createGreeting()]);
    toast.info("Chat history cleared.");
  }

  return (
    <ErrorBoundary>
      <div className="flex flex-col h-[calc(100vh-8rem)] md:h-[calc(100vh-7rem)]">
        <div
          className="flex flex-col flex-1 overflow-hidden rounded-2xl bg-[var(--bg-card)] border border-[var(--border)]"
        >
          <div
            className="flex items-center justify-between px-5 py-4 border-b flex-shrink-0 border-[var(--border)] bg-[var(--bg-surface)]"
          >
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-[var(--peach-ghost)] border border-[var(--peach-border)]">
                  <Bot className="w-5 h-5 text-[var(--peach)]" />
                </div>
                <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 bg-[var(--success)] border-[var(--bg-surface)]" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-[var(--text)]">GraftAI Copilot</h2>
                <p className="text-xs text-[var(--success)]">● Active</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "hidden sm:inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.18em]",
                  connected && backendToken
                    ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-300"
                    : "border-amber-500/20 bg-amber-500/10 text-amber-300"
                )}
              >
                <span
                  className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    connected && backendToken ? "bg-emerald-400 animate-pulse" : "bg-amber-400 animate-pulse"
                  )}
                />
                {connected && backendToken ? "Live sync" : "Syncing"}
              </span>
              <span className="badge badge-peach hidden sm:inline-flex">
                <Sparkles className="w-3 h-3" /> AI Powered
              </span>
              <button
                className="btn btn-ghost p-2 min-h-0 min-w-0 text-xs"
                onClick={clearHistory}
                title="Clear history"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          <AnimatePresence initial={false}>
            {liveSignal && (
              <motion.div
                initial={{ opacity: 0, y: -8, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.98 }}
                transition={{ duration: 0.22, ease: [0.23, 1, 0.32, 1] }}
                className="mx-4 mt-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/8 px-4 py-3 shadow-[0_12px_30px_-18px_rgba(16,185,129,0.6)]"
              >
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.22em] text-emerald-300">
                  <CheckCircle2 className="h-4 w-4" />
                  Live success sync
                </div>
                <p className="mt-1 text-sm font-medium text-[var(--text)]">{liveSignal.title}</p>
                <p className="mt-1 text-xs leading-relaxed text-[var(--text-muted)]">{liveSignal.message}</p>
              </motion.div>
            )}
          </AnimatePresence>

          <div
            ref={chatRef}
            className="flex-1 overflow-y-auto px-4 py-5 space-y-4 scrollbar-hide"
          >
            <AnimatePresence initial={false}>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25, ease: [0.23, 1, 0.32, 1] }}
                  className={cn("flex gap-3 group", msg.role === "user" && "flex-row-reverse")}
                >
                  <div
                    className={cn(
                      "w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 self-end",
                      msg.role === "ai"
                        ? "bg-[var(--peach-ghost)] border border-[var(--peach-border)]"
                        : "bg-[var(--bg-hover)] border border-[var(--border)]"
                    )}
                  >
                    {msg.role === "ai"
                      ? <Sparkles className="w-4 h-4 text-[var(--peach)]" />
                      : <UserIcon className="w-4 h-4 text-[var(--text-muted)]" />
                    }
                  </div>

                  <div className={cn("flex flex-col gap-1 max-w-[80%]", msg.role === "user" && "items-end")}>
                    <div
                      className={cn(
                        "px-4 py-3 rounded-2xl text-sm leading-relaxed relative",
                        msg.role === "user"
                          ? "bg-[var(--peach)] text-[#1A0F0A] rounded-br-[4px]"
                          : "bg-[var(--bg-hover)] text-[var(--text)] border border-[var(--border)] rounded-bl-[4px]"
                      )}
                    >
                      <MessageContent content={msg.content} />

                      {msg.role === "ai" && msg.action?.type && msg.action.type !== "none" && msg.action.status !== "error" && msg.action.status !== "conflict" && (
                        <motion.div
                          initial={{ opacity: 0, y: 6, scale: 0.98 }}
                          animate={{ opacity: 1, y: 0, scale: 1 }}
                          transition={{ duration: 0.18, ease: [0.23, 1, 0.32, 1] }}
                          className="mt-3 inline-flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-[11px] font-medium text-emerald-300"
                        >
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          {labelMilestone(msg.action.type, msg.milestone)}
                        </motion.div>
                      )}

                      <button
                        className="absolute -top-2 right-2 p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity min-h-0 min-w-0 bg-[var(--bg-card)] border border-[var(--border)]"
                        onClick={() => copyMessage(msg.id, msg.content)}
                        title="Copy"
                      >
                        {copiedId === msg.id
                          ? <Check className="w-3 h-3 text-[var(--success)]" />
                          : <Copy className="w-3 h-3 text-[var(--text-muted)]" />
                        }
                      </button>
                    </div>

                    <span className="text-[11px] px-1 text-[var(--text-faint)]">
                      {msg.role === "user" ? "You" : "Copilot"} · {new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {isTyping && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-3"
              >
                <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-[var(--peach-ghost)] border border-[var(--peach-border)]">
                  <Bot className="w-4 h-4 animate-pulse text-[var(--peach)]" />
                </div>
                <div className="px-4 py-3 rounded-2xl flex gap-1.5 items-center bg-[var(--bg-hover)] border border-[var(--border)]">
                  {[0, 150, 300].map(delay => (
                    <motion.span
                      key={delay}
                      className="w-1.5 h-1.5 rounded-full bg-[var(--peach)]"
                      animate={{ y: [0, -3, 0], opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 0.75, repeat: Infinity, delay: delay / 1000, ease: "easeInOut" }}
                    />
                  ))}
                </div>
              </motion.div>
            )}

            <div ref={bottomRef} />
          </div>

          <AnimatePresence>
            {showScrollBtn && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="absolute bottom-28 right-6 p-2 rounded-full shadow-lg min-h-0 min-w-0 bg-[var(--bg-card)] border border-[var(--border)] z-10"
                onClick={() => scrollToBottom(true)}
              >
                <ChevronDown className="w-4 h-4 text-[var(--text-muted)]" />
              </motion.button>
            )}
          </AnimatePresence>

          <div className="px-4 pt-3 flex gap-2 overflow-x-auto scrollbar-hide flex-shrink-0">
            {QUICK_PROMPTS.map(p => (
              <button
                key={p}
                className="flex-shrink-0 text-xs px-3 py-1.5 rounded-full font-medium transition-colors min-h-0 bg-[var(--peach-ghost)] text-[var(--peach)] border border-[var(--peach-border)]"
                onClick={() => { setInput(p); inputRef.current?.focus(); }}
              >
                {p}
              </button>
            ))}
          </div>

          <div className="px-4 pb-4 pt-3 flex-shrink-0">
            <form
              onSubmit={handleSubmit}
              className="flex gap-2 items-end rounded-xl p-2 bg-[var(--bg-hover)] border border-[var(--border)]"
            >
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Message Copilot… (Enter to send, Shift+Enter for newline)"
                rows={1}
                className="flex-1 bg-transparent text-sm resize-none outline-none leading-relaxed px-2 py-1 max-h-[120px] text-[var(--text)]"
                disabled={isTyping}
              />
              <button
                type="submit"
                className="btn btn-primary p-[10px] flex-shrink-0 min-h-0 rounded-[var(--radius)]"
                disabled={!input.trim() || isTyping}
              >
                {isTyping
                  ? <Loader2 className="w-4 h-4 animate-spin" />
                  : <Send className="w-4 h-4" />
                }
              </button>
            </form>
            <p className="text-center text-[11px] mt-2 text-[var(--text-faint)]">
              AI can make mistakes. Verify important scheduling decisions.
            </p>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}

function MessageContent({ content }: { content: string }) {
  const lines = content.split("\n");
  return (
    <>
      {lines.map((line, i) => (
        <span key={i}>
          {line.split(/(\*\*[^*]+\*\*)/).map((part, j) => {
            if (part.startsWith("**") && part.endsWith("**")) {
              return <strong key={j}>{part.slice(2, -2)}</strong>;
            }
            return part;
          })}
          {i < lines.length - 1 && <br />}
        </span>
      ))}
    </>
  );
}
