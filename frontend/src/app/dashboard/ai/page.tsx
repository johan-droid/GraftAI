"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Send, Sparkles, Loader2, MoreHorizontal, Maximize2, Paperclip } from "lucide-react";
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
      content: "Hi. I'm GraftAI Copilot. How can I help orchestrate your schedule today?"
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
        content: "Network exception: Unable to connect to Copilot core.",
      };
      setMessages((prev) => [...prev, aiMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#070711] sm:bg-transparent font-sans">
      
      {/* ── Main Chat Area ── */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 md:px-12 pt-6 pb-40 scrollbar-hide">
        <div className="max-w-3xl mx-auto space-y-10">
          <AnimatePresence initial={false}>
            {messages.map((msg, i) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                className={cn(
                  "flex items-start gap-4 sm:gap-6 group",
                  msg.role === "user" ? "flex-row-reverse" : "flex-row"
                )}
              >
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
                  "flex flex-col text-[14.5px] leading-relaxed max-w-[85%] sm:max-w-[75%]",
                  msg.role === "user" ? "items-end" : "items-start"
                )}>
                  {msg.role === "user" ? (
                    <div className="px-5 py-3.5 rounded-3xl bg-slate-800/80 text-white shadow-xl ring-1 ring-white/5 rounded-tr-sm backdrop-blur-xl">
                      {msg.content}
                    </div>
                  ) : (
                    <div className="px-1 py-2 text-slate-200">
                      {msg.content}
                    </div>
                  )}
                  
                  {/* AI Actions (Copy, Edit, etc) mapping subtly on hover */}
                  {msg.role === "ai" && (
                    <div className="mt-2 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button className="p-1 px-2 text-[11px] text-slate-500 bg-white/[0.04] hover:bg-white/[0.08] hover:text-slate-300 rounded-lg transition-colors border border-white/[0.05]">
                        Sources (2)
                      </button>
                      <button className="p-1 px-2 text-[11px] text-slate-500 bg-white/[0.04] hover:bg-white/[0.08] hover:text-slate-300 rounded-lg transition-colors border border-white/[0.05]">
                        <Bot className="w-3 h-3 inline-block mr-1" /> Suggest time
                      </button>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}

            {isTyping && (
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-start gap-4 sm:gap-6"
              >
                <div className="flex-shrink-0 mt-1 w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500/20 to-violet-600/20 border border-indigo-500/30 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-indigo-400 animate-pulse" />
                </div>
                <div className="px-1 py-3 text-slate-400 flex items-center gap-1.5 h-8">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-500/50 animate-bounce [animation-delay:-0.3s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-500/50 animate-bounce [animation-delay:-0.15s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-500/50 animate-bounce" />
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} className="h-4" />
          </AnimatePresence>
        </div>
      </div>

      {/* ── Floating Command Input ── */}
      <div className="absolute bottom-6 left-0 right-0 px-4 sm:px-6 pointer-events-none flex justify-center z-20">
        <div className="w-full max-w-3xl pointer-events-auto">
          {/* Action pills above input */}
          <div className="flex items-center justify-center gap-2 mb-3">
             <button className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900/60 backdrop-blur-xl border border-white/[0.08] rounded-full text-[11px] font-semibold text-slate-300 hover:text-white hover:bg-slate-800 transition-colors shadow-lg">
                <Sparkles className="w-3 h-3 text-amber-400" /> Deep Seek R1
             </button>
          </div>

          <form onSubmit={handleSubmit} className="relative group">
            {/* Ethereal Glow */}
            <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500/20 via-violet-500/20 to-indigo-500/20 rounded-[24px] blur-md opacity-50 group-focus-within:opacity-100 transition-opacity duration-500" />
            
            <div className="relative flex items-end gap-2 p-2 bg-slate-900/80 backdrop-blur-3xl border border-white/[0.1] rounded-[24px] shadow-2xl">
              <button 
                type="button"
                className="p-3 text-slate-400 hover:text-indigo-400 hover:bg-white/[0.05] rounded-full transition-colors flex-shrink-0 mb-0.5"
              >
                <Paperclip className="w-[18px] h-[18px]" strokeWidth={2.5} />
              </button>

              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if(input.trim() && !isTyping) handleSubmit(e);
                  }
                }}
                placeholder="Ask Copilot anything..."
                rows={1}
                className="w-full bg-transparent text-[14.5px] text-slate-200 placeholder-slate-500 focus:outline-none resize-none pt-3.5 pb-3 max-h-[150px] scrollbar-hide leading-relaxed"
                style={{ minHeight: '52px' }}
              />

              <div className="flex items-center gap-1 mb-0.5 mr-0.5 shrink-0">
                <button 
                  type="submit"
                  disabled={!input.trim() || isTyping}
                  className="p-2.5 rounded-full bg-white text-slate-900 hover:bg-slate-200 disabled:opacity-20 disabled:hover:bg-white transition-all flex items-center justify-center shrink-0 shadow-sm"
                >
                  {isTyping ? <Loader2 className="w-[18px] h-[18px] animate-spin" /> : <Send className="w-[18px] h-[18px]" strokeWidth={2.5} />}
                </button>
              </div>
            </div>
          </form>

          {/* Footer Text */}
          <div className="text-center mt-3 text-[10.5px] text-slate-500 font-medium">
            AI can make mistakes. Consider verifying calendar changes before finalizing.
          </div>
        </div>
      </div>
    </div>
  );
}
