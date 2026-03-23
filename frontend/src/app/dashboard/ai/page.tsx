"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Send, Sparkles, User as UserIcon, Loader2 } from "lucide-react";
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
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

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
      // Backend Request to AI Router using central API Client
      const data = await sendAiChat(userMessage.content);
      
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
    <div className="flex flex-col h-[calc(100vh-8rem)] bg-white/80 backdrop-blur-sm border border-slate-200/50 rounded-2xl shadow-lg dark:bg-slate-950/50 dark:border-slate-800 overflow-hidden">
      
      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b border-slate-800/50 bg-slate-900/50">
        <div className="p-2 rounded-lg bg-primary/20 text-primary">
          <Bot className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-white">GraftAI Copilot</h2>
          <p className="text-xs text-emerald-400 font-medium flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Online & Ready
          </p>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.3 }}
              className={cn(
                "flex max-w-[85%] sm:max-w-[70%]",
                msg.role === "user" ? "ml-auto" : "mr-auto"
              )}
            >
              <div className={cn(
                "flex items-end gap-2",
                msg.role === "user" ? "flex-row-reverse" : "flex-row"
              )}>
                {/* Avatar */}
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center shrink-0 border",
                  msg.role === "user" 
                    ? "bg-slate-700/50 border-slate-600/50" 
                    : "bg-primary/20 border-primary/30"
                )}>
                  {msg.role === "user" ? (
                    <UserIcon className="w-4 h-4 text-slate-300" />
                  ) : (
                    <Bot className="w-4 h-4 text-primary" />
                  )}
                </div>

                {/* Message Bubble */}
                <div className={cn(
                  "px-4 py-3 rounded-2xl text-sm leading-relaxed",
                  msg.role === "user" 
                    ? "bg-primary text-white rounded-br-sm" 
                    : "bg-slate-800/80 border border-slate-700/50 text-slate-200 rounded-bl-sm"
                )}>
                  {msg.content}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isTyping && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex mr-auto max-w-[80%]"
          >
            <div className="flex items-end gap-2">
              <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-primary/20 border border-primary/30">
                <Bot className="w-4 h-4 text-primary" />
              </div>
              <div className="px-4 py-4 rounded-2xl rounded-bl-sm bg-slate-800/80 border border-slate-700/50 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-slate-800/50 bg-slate-900/30">
        <form onSubmit={handleSubmit} className="flex gap-2 relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask Copilot to schedule a meeting..."
            className="flex-1 bg-slate-900/80 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all shadow-inner"
          />
          <button
            type="submit"
            disabled={!input.trim() || isTyping}
            className="bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl px-4 py-3 flex items-center justify-center transition-all shadow-[0_0_15px_rgba(79,70,229,0.2)] disabled:shadow-none"
          >
            {isTyping ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          </button>
        </form>
        <div className="mt-2 text-center flex items-center justify-center gap-1 text-xs text-slate-500">
          <Sparkles className="w-3 h-3 text-fuchsia-400" />
          <span>Press Enter to send. Copilot can make mistakes.</span>
        </div>
      </div>
    </div>
  );
}
