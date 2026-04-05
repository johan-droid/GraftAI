"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Send, Sparkles, User as UserIcon, Loader2, Zap, Clock, Calendar, Globe } from "lucide-react";
import { cn } from "@/lib/utils";
import { sendAiChat } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
  timestamp: Date;
}

const QUICK_PROMPTS = [
  { icon: Calendar, text: "Find the best time for a team meeting next week" },
  { icon: Globe, text: "Schedule a call with someone in Tokyo and New York" },
  { icon: Clock, text: "Block focus time every morning for deep work" },
  { icon: Zap, text: "Analyze my busiest days and suggest optimizations" },
];

export default function AISchedulerAssistantPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "ai",
      content:
        "Hi! I'm your GraftAI Scheduler Assistant. I can help you schedule meetings, find optimal time slots, coordinate across timezones, and manage your calendar intelligently. What would you like to do?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const send = async (text: string) => {
    if (!text.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const data = await sendAiChat(text, undefined, tz);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "ai",
          content: data.result || "I couldn't process that. Please try again.",
          timestamp: new Date(),
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "ai",
          content: "Assistant is temporarily offline. I can still handle list, schedule, update, and delete calendar requests once connection resumes.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    send(input);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  };

  const formatTime = (d: Date) => d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  return (
    <div className="flex flex-col h-[calc(100vh-53px)]">
      {/* Header */}
      <div className="flex items-center gap-4 px-5 py-3.5 border-b border-white/[0.06] bg-[#040a18]/40 shrink-0">
        <div className="relative">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Bot className="w-4.5 h-4.5 text-white" />
          </div>
          <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-[#030712]" />
        </div>
        <div>
          <h2 className="text-sm font-bold text-white">GraftAI Scheduler Assistant</h2>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
            <span className="text-[11px] text-slate-500">Active · Ready to schedule</span>
          </div>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 border border-white/8 text-[11px] font-bold text-slate-500 uppercase tracking-wide">
            <Sparkles className="w-3 h-3 text-indigo-400" /> AI Orchestration Active
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-5">
        {/* Quick prompts - show only when minimal messages */}
        {messages.length <= 1 && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-2xl mx-auto mb-4"
          >
            {QUICK_PROMPTS.map((p) => (
              <button
                key={p.text}
                onClick={() => send(p.text)}
                className="flex items-start gap-3 p-3.5 rounded-xl border border-white/[0.07] bg-white/[0.025] hover:border-indigo-500/30 hover:bg-indigo-500/5 text-left transition-all group"
              >
                <div className="w-7 h-7 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center shrink-0">
                  <p.icon className="w-3.5 h-3.5 text-indigo-400" />
                </div>
                <span className="text-[12px] text-slate-400 group-hover:text-slate-200 leading-relaxed transition-colors">{p.text}</span>
              </button>
            ))}
          </motion.div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className={cn(
                "flex max-w-[85%] md:max-w-[70%]",
                msg.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
              )}
            >
              <div className={cn("flex gap-3", msg.role === "user" ? "flex-row-reverse" : "flex-row")}>
                {/* Avatar */}
                <div className="flex-shrink-0 mt-1">
                  {msg.role === "user" ? (
                    <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700/60 flex items-center justify-center text-[11px] font-bold text-slate-300 shadow-md">
                      YOU
                    </div>
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                      <Sparkles className="w-4 h-4 text-white" />
                    </div>
                  )}
                </div>

                {/* Message Content */}
                <div className={cn(
                  "flex flex-col gap-1",
                  msg.role === "user" ? "items-end" : "items-start"
                )}>
                  <div className={cn(
                    "px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap break-words",
                    msg.role === "user"
                      ? "bg-indigo-600/95 text-white rounded-2xl shadow-sm"
                      : "bg-white/[0.035] border border-white/[0.04] text-slate-200 rounded-2xl"
                  )}>
                    {msg.content}
                  </div>
                  <span className="text-[10px] text-slate-600 px-1">{formatTime(msg.timestamp)}</span>
                </div>
              </div>
            </motion.div>
          ))}

          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex mr-auto"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500/20 to-violet-600/20 border border-indigo-500/30 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-indigo-400 animate-pulse" />
                </div>
                <div className="flex gap-1.5 px-4 py-3 bg-white/[0.03] border border-white/[0.04] rounded-2xl">
                  {[0, 1, 2].map((i) => (
                    <motion.span
                      key={i}
                      className="w-1.5 h-1.5 rounded-full bg-indigo-400/60"
                      animate={{ y: [0, -4, 0] }}
                      transition={{ duration: 0.7, repeat: Infinity, delay: i * 0.15 }}
                    />
                  ))}
                </div>
              </div>
            </motion.div>
          )}
          <div ref={endRef} className="h-4" />
        </AnimatePresence>
      </div>

      {/* Input */}
      <div className="absolute bottom-6 left-0 right-0 px-4 md:px-8 pointer-events-none flex justify-center z-20">
        <div className="w-full max-w-3xl pointer-events-auto">
          {/* Action pills above input */}
          <div className="flex items-center justify-center gap-2 mb-3">
            <span className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900/60 backdrop-blur-xl border border-white/[0.08] rounded-full text-[11px] font-semibold text-slate-300 shadow-lg">
              <Sparkles className="w-3 h-3 text-amber-400" /> Scheduler Core
            </span>
          </div>

          <form onSubmit={handleSubmit} className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500/20 via-violet-500/20 to-indigo-500/20 rounded-[24px] blur-md opacity-50 group-focus-within:opacity-100 transition-opacity duration-500" />
            <div className="relative flex items-end gap-2 p-2 bg-slate-900/80 backdrop-blur-3xl border border-white/[0.1] rounded-[24px] shadow-2xl">
              {/* Attachment removed for a cleaner, less-cluttered input on mobile and desktop. */}

              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask Scheduler Assistant..."
                rows={1}
                className="w-full min-h-[56px] bg-transparent text-[15px] text-slate-200 placeholder-slate-500 focus:outline-none resize-none pt-4 pb-3 max-h-[150px] scrollbar-hide leading-relaxed break-words"
              />

              <div className="flex items-center gap-1 mb-0.5 mr-0.5 shrink-0">
                <button
                  type="submit"
                  aria-label="Send message"
                  title="Send message"
                  disabled={!input.trim() || isTyping}
                  className="p-2.5 rounded-full bg-indigo-500 text-white hover:bg-indigo-600 disabled:opacity-50 transition-all flex items-center justify-center shrink-0 shadow-md"
                >
                  {isTyping ? <Loader2 className="w-[18px] h-[18px] animate-spin" /> : <Send className="w-[18px] h-[18px]" strokeWidth={2.5} />}
                </button>
              </div>
            </div>

            <div className="text-center mt-3 text-[10.5px] text-slate-500 font-medium">
              Press <kbd className="font-mono bg-white/5 px-1 rounded">Enter</kbd> to send · <kbd className="font-mono bg-white/5 px-1 rounded">Shift+Enter</kbd> for new line
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
