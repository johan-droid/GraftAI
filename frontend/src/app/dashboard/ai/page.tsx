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
  Bot, Send, Sparkles, User as UserIcon, Loader2, Trash2, Copy, Check,
  Calendar, ChevronDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { sendAiChat } from "@/lib/api";
import { useLocalStorage } from "@/hooks/useQuery";
import { toast } from "@/components/ui/Toast";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
  timestamp: number;
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

export default function AICopilotPage() {
  const [messages, setMessages] = useLocalStorage<Message[]>("copilot-history", [createGreeting()]);
  const [input, setInput]       = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showScrollBtn, setShowScrollBtn] = useState(false);

  const bottomRef  = useRef<HTMLDivElement>(null);
  const chatRef    = useRef<HTMLDivElement>(null);
  const inputRef   = useRef<HTMLTextAreaElement>(null);

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
      const { result } = await sendAiChat(text, undefined, timezone);

      const aiMsg: Message = {
        id: crypto.randomUUID(),
        role: "ai",
        content: result || "I couldn't process that request. Please try again.",
        timestamp: Date.now(),
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
    setMessages([AI_GREETING]);
    toast.info("Chat history cleared.");
  }

  return (
    <ErrorBoundary>
      <div className="flex flex-col h-[calc(100vh-8rem)] md:h-[calc(100vh-7rem)]">
        <div
          className="flex flex-col flex-1 overflow-hidden rounded-2xl"
          style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}
        >
          <div
            className="flex items-center justify-between px-5 py-4 border-b flex-shrink-0"
            style={{ borderColor: "var(--border)", background: "var(--bg-surface)" }}
          >
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-9 h-9 rounded-xl flex items-center justify-center"
                  style={{ background: "var(--peach-ghost)", border: "1px solid var(--peach-border)" }}>
                  <Bot className="w-5 h-5" style={{ color: "var(--peach)" }} />
                </div>
                <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2"
                  style={{ background: "var(--success)", borderColor: "var(--bg-surface)" }} />
              </div>
              <div>
                <h2 className="text-sm font-semibold" style={{ color: "var(--text)" }}>GraftAI Copilot</h2>
                <p className="text-xs" style={{ color: "var(--success)" }}>● Active</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
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
                    className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 self-end"
                    style={msg.role === "ai"
                      ? { background: "var(--peach-ghost)", border: "1px solid var(--peach-border)" }
                      : { background: "var(--bg-hover)", border: "1px solid var(--border)" }
                    }
                  >
                    {msg.role === "ai"
                      ? <Sparkles className="w-4 h-4" style={{ color: "var(--peach)" }} />
                      : <UserIcon className="w-4 h-4" style={{ color: "var(--text-muted)" }} />
                    }
                  </div>

                  <div className={cn("flex flex-col gap-1 max-w-[80%]", msg.role === "user" && "items-end")}>
                    <div
                      className="px-4 py-3 rounded-2xl text-sm leading-relaxed relative"
                      style={msg.role === "user"
                        ? {
                            background: "var(--peach)",
                            color: "#1A0F0A",
                            borderBottomRightRadius: 4,
                          }
                        : {
                            background: "var(--bg-hover)",
                            color: "var(--text)",
                            border: "1px solid var(--border)",
                            borderBottomLeftRadius: 4,
                          }
                      }
                    >
                      <MessageContent content={msg.content} />

                      <button
                        className="absolute -top-2 right-2 p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity min-h-0 min-w-0"
                        style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}
                        onClick={() => copyMessage(msg.id, msg.content)}
                        title="Copy"
                      >
                        {copiedId === msg.id
                          ? <Check className="w-3 h-3" style={{ color: "var(--success)" }} />
                          : <Copy className="w-3 h-3" style={{ color: "var(--text-muted)" }} />
                        }
                      </button>
                    </div>

                    <span className="text-[11px] px-1" style={{ color: "var(--text-faint)" }}>
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
                <div className="w-8 h-8 rounded-xl flex items-center justify-center"
                  style={{ background: "var(--peach-ghost)", border: "1px solid var(--peach-border)" }}>
                  <Bot className="w-4 h-4 animate-pulse" style={{ color: "var(--peach)" }} />
                </div>
                <div className="px-4 py-3 rounded-2xl flex gap-1.5 items-center"
                  style={{ background: "var(--bg-hover)", border: "1px solid var(--border)" }}>
                  {[0, 150, 300].map(delay => (
                    <span key={delay} className="w-1.5 h-1.5 rounded-full animate-bounce"
                      style={{ background: "var(--peach)", animationDelay: `${delay}ms` }} />
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
                className="absolute bottom-28 right-6 p-2 rounded-full shadow-lg min-h-0 min-w-0"
                style={{ background: "var(--bg-card)", border: "1px solid var(--border)", zIndex: 10 }}
                onClick={() => scrollToBottom(true)}
              >
                <ChevronDown className="w-4 h-4" style={{ color: "var(--text-muted)" }} />
              </motion.button>
            )}
          </AnimatePresence>

          <div className="px-4 pt-3 flex gap-2 overflow-x-auto scrollbar-hide flex-shrink-0">
            {QUICK_PROMPTS.map(p => (
              <button
                key={p}
                className="flex-shrink-0 text-xs px-3 py-1.5 rounded-full font-medium transition-colors min-h-0"
                style={{
                  background: "var(--peach-ghost)",
                  color: "var(--peach)",
                  border: "1px solid var(--peach-border)",
                }}
                onClick={() => { setInput(p); inputRef.current?.focus(); }}
              >
                {p}
              </button>
            ))}
          </div>

          <div className="px-4 pb-4 pt-3 flex-shrink-0">
            <form
              onSubmit={handleSubmit}
              className="flex gap-2 items-end rounded-xl p-2"
              style={{ background: "var(--bg-hover)", border: "1px solid var(--border)" }}
            >
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Message Copilot… (Enter to send, Shift+Enter for newline)"
                rows={1}
                className="flex-1 bg-transparent text-sm resize-none outline-none leading-relaxed px-2 py-1 max-h-[120px]"
                style={{ color: "var(--text)" }}
                disabled={isTyping}
              />
              <button
                type="submit"
                className="btn btn-primary p-2.5 flex-shrink-0 min-h-0"
                disabled={!input.trim() || isTyping}
                style={{ borderRadius: "var(--radius)", padding: "10px" }}
              >
                {isTyping
                  ? <Loader2 className="w-4 h-4 animate-spin" />
                  : <Send className="w-4 h-4" />
                }
              </button>
            </form>
            <p className="text-center text-[11px] mt-2" style={{ color: "var(--text-faint)" }}>
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
