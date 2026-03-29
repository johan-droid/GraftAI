"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Send, Sparkles, User as UserIcon, Loader2, Calendar, Clock, Globe } from "lucide-react";
import { cn } from "@/lib/utils";
import { sendAiChat } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
}

export default function AICopilotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "ai",
      content: "Hello! I am your GraftAI Copilot. Let me know what you'd like to schedule, analyze, or configure today."
    }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [greeting, setGreeting] = useState("");
  const [currentTime, setCurrentTime] = useState("");
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const hour = now.getHours();
      const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      setCurrentTime(timeStr);

      if (hour < 12) setGreeting("Good Morning");
      else if (hour < 17) setGreeting("Good Afternoon");
      else setGreeting("Good Evening");
    };

    updateTime();
    const timer = setInterval(updateTime, 60000);
    return () => clearInterval(timer);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    try {
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const data = await sendAiChat(userMessage.content, undefined, timezone);
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "ai",
        content: data.result || "I'm sorry, I couldn't process that request.",
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error(error);
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "ai",
        content: "We're experiencing a connection issue with the Copilot API. Please try again later.",
      };
      setMessages((prev) => [...prev, aiMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] bg-slate-50/50 backdrop-blur-xl border border-slate-200/60 rounded-3xl shadow-2xl dark:bg-slate-950/40 dark:border-slate-800/60 overflow-hidden">
      
      {/* Header */}
      <div className="flex items-center justify-between p-5 border-b border-slate-200/50 dark:border-slate-800/50 bg-white/40 dark:bg-slate-900/40 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="p-2.5 rounded-2xl bg-gradient-to-br from-primary to-violet-600 text-white shadow-lg shadow-primary/20">
              <Bot className="w-5 h-5" />
            </div>
            <span className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-emerald-500 border-2 border-white dark:border-slate-900" />
          </div>
          <div>
            <h2 className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-slate-400">GraftAI Copilot</h2>
            <div className="flex items-center gap-2">
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold uppercase tracking-wider">Active</span>
              <span className="text-xs text-slate-400 dark:text-slate-500 font-medium">Ready to orchestrate</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
           <div className="px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200/50 dark:border-slate-700/50 text-[11px] font-bold text-slate-500 dark:text-slate-400 flex items-center gap-2">
             <Clock className="w-3.5 h-3.5 text-primary" />
             {currentTime}
           </div>
        </div>
      </div>

      {/* Greeting Banner */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mx-6 mt-4 p-4 rounded-3xl bg-gradient-to-r from-primary/5 via-violet-500/5 to-white dark:from-primary/10 dark:via-violet-500/10 dark:to-slate-900 border border-primary/10 shadow-sm"
      >
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex w-12 h-12 rounded-2xl bg-white dark:bg-slate-800 items-center justify-center shadow-sm border border-slate-100 dark:border-slate-700 text-2xl">
            {greeting === "Good Morning" ? "🌅" : greeting === "Good Afternoon" ? "☀️" : "🌙"}
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800 dark:text-white">{greeting}, explorer!</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              It&apos;s {currentTime} in your timezone. Ready to schedule your cross-country meetings?
            </p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <button className="text-[10px] px-3 py-1.5 rounded-xl bg-primary/10 hover:bg-primary/20 text-primary font-bold transition-all border border-primary/20 uppercase tracking-tight flex items-center gap-1.5">
              <Calendar className="w-3 h-3" />
              View Agenda
            </button>
          </div>
        </div>
      </motion.div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 12, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
              className={cn(
                "flex max-w-[90%] sm:max-w-[75%]",
                msg.role === "user" ? "ml-auto" : "mr-auto"
              )}
            >
              <div className={cn(
                "flex gap-3",
                msg.role === "user" ? "flex-row-reverse" : "flex-row"
              )}>
                {/* Avatar */}
                <div className={cn(
                  "w-9 h-9 rounded-2xl flex items-center justify-center shrink-0 border shadow-sm",
                  msg.role === "user" 
                    ? "bg-slate-100 border-slate-200 dark:bg-slate-800 dark:border-slate-700" 
                    : "bg-white border-slate-200 dark:bg-slate-900 dark:border-slate-800"
                )}>
                  {msg.role === "user" ? (
                    <UserIcon className="w-4.5 h-4.5 text-slate-600 dark:text-slate-400" />
                  ) : (
                    <Sparkles className="w-4.5 h-4.5 text-primary" />
                  )}
                </div>
                
                <div className={cn(
                  "flex flex-col gap-1.5",
                  msg.role === "user" ? "items-end" : "items-start"
                )}>
                  {/* Message Bubble */}
                  <div className={cn(
                    "px-4.5 py-3.5 rounded-2xl text-[13.5px] leading-relaxed shadow-sm transition-all",
                    msg.role === "user" 
                      ? "bg-gradient-to-br from-primary to-violet-600 text-white rounded-tr-none shadow-primary/20" 
                      : "bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 text-slate-700 dark:text-slate-300 rounded-tl-none"
                  )}>
                    {msg.content}
                  </div>
                  <span className="text-[10px] text-slate-400 dark:text-slate-500 px-1 font-medium">
                    {msg.role === "user" ? "You" : "Copilot"} • {currentTime}
                  </span>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isTyping && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex mr-auto"
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-2xl flex items-center justify-center shrink-0 bg-primary/5 border border-primary/10">
                <Bot className="w-4.5 h-4.5 text-primary animate-pulse" />
              </div>
              <div className="flex gap-1.5 px-4 py-3 bg-white dark:bg-slate-900 border border-slate-200/50 dark:border-slate-800/80 rounded-2xl rounded-tl-none shadow-sm">
                <span className="w-1.5 h-1.5 rounded-full bg-primary/40 animate-bounce [animation-delay:-0.3s]" />
                <span className="w-1.5 h-1.5 rounded-full bg-primary/40 animate-bounce [animation-delay:-0.15s]" />
                <span className="w-1.5 h-1.5 rounded-full bg-primary/40 animate-bounce" />
              </div>
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-6 border-t border-slate-200/50 dark:border-slate-800/50 bg-white/40 dark:bg-slate-950/40 backdrop-blur-md">
        <form onSubmit={handleSubmit} className="relative group max-w-4xl mx-auto text-black">
          <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-violet-500/10 rounded-2xl blur-xl transition-all duration-300 group-focus-within:opacity-100 opacity-0" />
          <div className="relative flex gap-3 p-1.5 bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-2xl shadow-xl transition-all group-focus-within:border-primary/50 group-focus-within:ring-4 group-focus-within:ring-primary/5">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="How can I help you coordinate today?"
              className="flex-1 bg-transparent px-4 py-3 text-[14px] text-slate-800 dark:text-slate-100 placeholder-slate-400/80 focus:outline-none"
            />
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className="px-5 py-3 rounded-xl bg-gradient-to-br from-primary to-violet-600 hover:from-primary/90 hover:to-violet-600/90 disabled:opacity-30 disabled:grayscale text-white font-bold text-sm transition-all shadow-lg shadow-primary/20 flex items-center gap-2"
            >
              {isTyping ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              <span className="hidden sm:inline">Send</span>
            </button>
          </div>
        </form>
        
        <div className="mt-4 flex flex-wrap items-center justify-center gap-4">
          <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest bg-slate-100 dark:bg-slate-800/50 px-3 py-1 rounded-full border border-slate-200/50 dark:border-slate-700/50 transition-all hover:bg-slate-200 dark:hover:bg-slate-800 cursor-help group">
            <Sparkles className="w-3 h-3 text-primary group-hover:rotate-12 transition-transform" />
            <span>AI Orchestration Active</span>
          </div>
          <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest bg-slate-100 dark:bg-slate-800/50 px-3 py-1 rounded-full border border-slate-200/50 dark:border-slate-700/50 transition-all">
            <Globe className="w-3 h-3 text-violet-400" />
            <span>Cross-Country Mode</span>
          </div>
        </div>
      </div>
    </div>
  );
}
