"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Send, 
  Sparkles, 
  User as UserIcon, 
  Loader2, 
  Plus,
  ArrowUp,
  CheckCircle2
} from "lucide-react";
import { cn } from "@/lib/utils";
import { streamAiChat } from "@/lib/api";

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
      content: "Hello! How can I help you today?"
    }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    const aiMessageId = (Date.now() + 1).toString();
    const newAiMessage: Message = {
      id: aiMessageId,
      role: "ai",
      content: "",
    };
    setMessages((prev) => [...prev, newAiMessage]);

    try {
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const stream = streamAiChat(userMessage.content, timezone);
      
      let accumulatedText = "";
      for await (const chunk of stream) {
        if (chunk.text) {
          accumulatedText += chunk.text;
          setMessages((prev) => 
            prev.map(msg => msg.id === aiMessageId ? { ...msg, content: accumulatedText } : msg)
          );
        }
        
        // Trigger Success UI if action was successful
        if (chunk.success) {
          setShowSuccess(true);
          setTimeout(() => setShowSuccess(false), 2500);
        }
      }
    } catch (error) {
      console.error(error);
      setMessages((prev) => 
        prev.map(msg => msg.id === aiMessageId ? { ...msg, content: "Sorry, something went wrong. Please try again." } : msg)
      );
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full max-w-3xl bg-transparent border-none">
      
      {/* Header - Simple & Clean */}
      <div className="flex items-center justify-between p-6 bg-transparent">
        <h2 className="text-lg font-semibold text-white/90">GraftAI Chat</h2>
        <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-[11px] text-white/40 font-medium uppercase tracking-wider">Online</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 space-y-6 scrollbar-hide flex flex-col pt-4">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn(
                "flex w-full mb-4",
                msg.role === "user" ? "justify-end" : "justify-start"
              )}
            >
              <div className={cn(
                "flex gap-3 max-w-[85%]",
                msg.role === "user" ? "flex-row-reverse" : "flex-row"
              )}>
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                  msg.role === "user" ? "bg-white/5 text-white/40" : "bg-white text-[#0A0E27]"
                )}>
                  {msg.role === "user" ? <UserIcon size={16} /> : <Sparkles size={16} />}
                </div>
                
                <div className={cn(
                  "px-4 py-3 rounded-[1.25rem] text-[15px] leading-relaxed shadow-sm",
                  msg.role === "user" 
                    ? "bg-[#0066FF] text-white rounded-tr-none" 
                    : "bg-white/[0.03] border border-white/5 text-white/90 rounded-tl-none"
                )}>
                  {msg.content}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isTyping && (
           <div className="flex gap-3 ml-1 animate-pulse">
             <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center">
                <Sparkles size={16} className="text-white/20" />
             </div>
             <div className="px-5 py-3 bg-white/[0.02] border border-white/5 rounded-2xl rounded-tl-none flex items-baseline gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-white/20 animate-bounce" />
                <span className="w-1.5 h-1.5 rounded-full bg-white/20 animate-bounce [animation-delay:0.2s]" />
                <span className="w-1.5 h-1.5 rounded-full bg-white/20 animate-bounce [animation-delay:0.4s]" />
             </div>
           </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Sovereign Success Animation (PhonePe Style) */}
      <AnimatePresence>
        {showSuccess && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-[#0A0E27]/40 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.5, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.5, y: -20 }}
              transition={{ type: "spring", damping: 15, stiffness: 200 }}
              className="bg-white rounded-[2.5rem] p-12 shadow-[0_32px_64px_-16px_rgba(0,102,255,0.4)] flex flex-col items-center gap-6"
            >
                <div className="relative">
                    <motion.div 
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.2, type: "spring" }}
                        className="w-24 h-24 bg-emerald-500 rounded-full flex items-center justify-center text-white"
                    >
                        <CheckCircle2 size={56} strokeWidth={3} />
                    </motion.div>
                    
                    {/* Ring Pulse */}
                    <motion.div 
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1.5, opacity: 0 }}
                        transition={{ duration: 0.8, repeat: Infinity, ease: "easeOut" }}
                        className="absolute inset-0 border-4 border-emerald-500 rounded-full"
                    />
                </div>
                
                <div className="text-center">
                    <h3 className="text-2xl font-bold text-[#0A0E27] mb-1">Confirmed</h3>
                    <p className="text-[#0A0E27]/40 font-medium">Schedule Synchronized</p>
                </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input - Clean Simple Bar */}
      <div className="p-6 pt-2 bg-transparent">
        <form onSubmit={handleSubmit} className="relative group max-w-2xl mx-auto">
          <div className="relative flex items-center gap-3 bg-white/[0.03] border border-white/10 rounded-[1.5rem] px-4 py-2 hover:border-white/20 transition-all focus-within:border-white/30 shadow-2xl">
            <button className="p-1.5 text-white/30 hover:text-white/60 transition-colors">
                <Plus size={20} />
            </button>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything..."
              className="flex-1 bg-transparent py-3 text-[15px] text-white placeholder-white/20 focus:outline-none"
            />
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className="w-10 h-10 rounded-full bg-white flex items-center justify-center text-[#0A0E27] shadow-xl hover:scale-105 active:scale-95 disabled:opacity-20 disabled:scale-100 transition-all"
            >
              {isTyping ? <Loader2 size={18} className="animate-spin" /> : <ArrowUp size={20} strokeWidth={3} />}
            </button>
          </div>
          <p className="text-center text-[10px] text-white/20 mt-3 font-medium tracking-wide">
            Model: GraftAI Orchestrator • Enterprise Standard
          </p>
        </form>
      </div>
    </div>
  );
}
