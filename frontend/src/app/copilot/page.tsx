"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Sparkles,
  Bot,
  User,
  Calendar,
  Clock,
  Lightbulb,
  Wand2,
  Copy,
  Check,
  Trash2,
  Activity,
  ArrowUp,
  RefreshCw,
  MoreVertical,
  Plus,
  Zap,
} from "lucide-react";
import { useAuth } from "@/app/providers/auth-provider";
import { MobileSidebar } from "@/components/dashboard/MobileSidebar";
import { BottomNav } from "@/components/dashboard/BottomNav";
import { Header } from "@/components/dashboard/Header";
import { AgentExecutionTimeline } from "@/components/ui/Timeline";
import { aiAutomationApi } from "@/lib/ai-api";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import styles from "./copilot.module.css";

interface AgentPhase {
  name: string;
  timeMs: number;
  status: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  agentExecuted?: boolean;
  agentType?: string;
  intent?: string;
  phases?: AgentPhase[];
}

const suggestedPrompts = [
  { icon: Calendar, label: "Schedule a meeting", prompt: "Schedule a team sync for next Tuesday at 2 PM", color: "text-blue-500", bg: "bg-blue-50" },
  { icon: Clock, label: "Find free time", prompt: "When am I free this week for deep work?", color: "text-purple-500", bg: "bg-purple-50" },
  { icon: Lightbulb, label: "Meeting insights", prompt: "Analyze my meeting patterns", color: "text-amber-500", bg: "bg-amber-50" },
  { icon: Wand2, label: "Optimize schedule", prompt: "Optimize my schedule to reduce context switching", color: "text-emerald-500", bg: "bg-emerald-50" },
];

export default function CopilotPage() {
  const router = useRouter();
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedAgentId, setExpandedAgentId] = useState<string | null>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8F9FA]">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-10 h-10 rounded-full border-4 border-blue-100 border-t-blue-600"
        />
      </div>
    );
  }

  if (!isAuthenticated) {
    router.replace("/login");
    return null;
  }

  const handleSendMessage = async (text?: string) => {
    const finalContent = text || inputValue.trim();
    if (!finalContent || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: finalContent,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await aiAutomationApi.sendChatMessage({
        message: finalContent,
        conversation_id: conversationId || undefined,
      });
      
      const phasesArray: AgentPhase[] = response.phases
        ? Object.entries(response.phases).map(([name, phase]) => ({
            name: name.charAt(0).toUpperCase() + name.slice(1),
            timeMs: phase.time_ms || phase.duration_ms || 0,
            status: phase.status,
          }))
        : [];
      
      const aiResponse: Message = {
        id: response.id || Date.now().toString(),
        role: "assistant",
        content: response.content,
        timestamp: new Date(response.timestamp || Date.now()),
        agentExecuted: response.agent_executed,
        agentType: response.agent_type,
        intent: response.intent,
        phases: phasesArray,
      };
      
      setMessages((prev) => [...prev, aiResponse]);
      
      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id);
      }
      
      if (response.agent_executed) {
        setExpandedAgentId(aiResponse.id);
      }
    } catch (err) {
      toast.error("I'm having trouble responding right now. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const copyMessage = (id: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const clearChat = () => {
    setMessages([]);
    setConversationId(null);
  };

  return (
    <div className="flex flex-col h-screen bg-[#F8F9FA] overflow-hidden selection:bg-blue-100">
      <MobileSidebar />
      
      {/* HEADER SECTION */}
      <div className="px-4 pt-4 md:px-8 md:pt-6 shrink-0">
        <Header
          userName={(user as any)?.name}
          userEmail={user?.email}
          userAvatar={(user as any)?.avatar}
          notificationCount={0}
        />
      </div>

      {/* MAIN CHAT AREA */}
      <div className={cn("flex-1 overflow-y-auto px-4 md:px-6 py-4 chat-scroll", styles["chat-scroll"])}>
        <div className="max-w-4xl mx-auto min-h-full flex flex-col">
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center py-12 px-4 text-center">
              <motion.div 
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="mb-8"
              >
                <div className="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600">
                  <Sparkles size={32} />
                </div>
              </motion.div>

              <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.1 }}
              >
                <h1 className="text-3xl md:text-4xl font-normal text-slate-900 tracking-tight mb-3">
                  How can I help you today?
                </h1>
                <p className="text-slate-500 text-lg max-w-lg mx-auto mb-10">
                  I can manage your calendar, find optimal meeting times, and help you stay productive.
                </p>
              </motion.div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-2xl">
                {suggestedPrompts.map((item, index) => (
                  <motion.button
                    key={index}
                    initial={{ y: 10, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.2 + index * 0.05 }}
                    whileHover={{ scale: 1.02, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleSendMessage(item.prompt)}
                    className="flex items-start gap-4 p-5 text-left bg-white border border-slate-200 rounded-2xl hover:border-blue-400 hover:shadow-sm transition-all group"
                  >
                    <div className={cn("shrink-0 p-3 rounded-xl transition-colors", item.bg, item.color)}>
                      <item.icon size={20} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-800 text-sm mb-1">{item.label}</h3>
                      <p className="text-slate-500 text-sm line-clamp-2 leading-relaxed">{item.prompt}</p>
                    </div>
                  </motion.button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-8 pb-32 pt-4">
              <AnimatePresence initial={false}>
                {messages.map((msg, idx) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                    className={cn(
                      "flex group",
                      msg.role === "user" ? "justify-end" : "justify-start"
                    )}
                  >
                    <div className={cn(
                      "flex max-w-[85%] md:max-w-[75%]",
                      msg.role === "user" ? "flex-row-reverse" : "flex-row"
                    )}>
                      {/* Avatar */}
                      <div className={cn(
                        "shrink-0 mt-1",
                        msg.role === "user" ? "ml-3" : "mr-3"
                      )}>
                        <div className={cn(
                          "w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold",
                          msg.role === "user" ? "bg-blue-600 text-white shadow-md shadow-blue-200" : "bg-white border border-slate-200 text-blue-600"
                        )}>
                          {msg.role === "user" ? <User size={14} /> : <Bot size={14} />}
                        </div>
                      </div>

                      {/* Content */}
                      <div className="flex flex-col items-start gap-2">
                        <div className={cn(
                          "px-5 py-4 text-[15px] leading-relaxed shadow-sm transition-shadow",
                          msg.role === "user" 
                            ? "bg-blue-600 text-white rounded-[24px] rounded-tr-sm" 
                            : "bg-white border border-slate-200 text-slate-800 rounded-[24px] rounded-tl-sm hover:shadow-md",
                          styles["message-bubble"]
                        )}>
                          <p className="whitespace-pre-wrap">{msg.content}</p>
                        </div>

                        {/* Message Footer */}
                        <div className={cn(
                          "flex items-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity px-2",
                          msg.role === "user" ? "flex-row-reverse" : "flex-row"
                        )}>
                          <span className="text-[11px] font-medium text-slate-400">
                            {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </span>

                          {msg.agentExecuted && (
                            <button
                              onClick={() => setExpandedAgentId(expandedAgentId === msg.id ? null : msg.id)}
                              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-50 text-blue-600 text-[10px] font-bold uppercase tracking-wider hover:bg-blue-100 transition-colors"
                            >
                              <Activity size={10} />
                              {msg.agentType || "Agent"}
                              {expandedAgentId === msg.id ? <RefreshCw size={10} className="animate-spin-slow" /> : <Plus size={10} />}
                            </button>
                          )}

                          {msg.role === "assistant" && (
                            <button
                              onClick={() => copyMessage(msg.id, msg.content)}
                              className="text-slate-400 hover:text-blue-600 transition-colors"
                            >
                              {copiedId === msg.id ? <Check size={14} /> : <Copy size={14} />}
                            </button>
                          )}
                        </div>

                        {/* Expanded Timeline */}
                        {msg.agentExecuted && expandedAgentId === msg.id && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="w-full mt-4 p-5 bg-white border border-blue-100 rounded-3xl shadow-sm overflow-hidden"
                          >
                            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-50">
                              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                <Zap size={12} className="text-blue-500" /> Trace Execution
                              </h4>
                              {msg.intent && (
                                <span className="text-xs font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full">
                                  {msg.intent}
                                </span>
                              )}
                            </div>
                            
                            <AgentExecutionTimeline
                              size="small"
                              perception={{
                                status: msg.phases?.find(p => p.name.toLowerCase().includes("percep"))?.status === "completed" ? "completed" : "pending",
                                duration_ms: msg.phases?.find(p => p.name.toLowerCase().includes("percep"))?.timeMs,
                              }}
                              cognition={{
                                status: msg.phases?.find(p => p.name.toLowerCase().includes("cogn") || p.name.toLowerCase().includes("decis"))?.status === "completed" ? "completed" : "pending",
                                duration_ms: msg.phases?.find(p => p.name.toLowerCase().includes("cogn") || p.name.toLowerCase().includes("decis"))?.timeMs,
                                decision: msg.intent,
                              }}
                              action={{
                                status: msg.phases?.find(p => p.name.toLowerCase().includes("action"))?.status === "completed" ? "completed" : "pending",
                                duration_ms: msg.phases?.find(p => p.name.toLowerCase().includes("action"))?.timeMs,
                              }}
                              reflection={{
                                status: msg.phases?.find(p => p.name.toLowerCase().includes("reflect"))?.status === "completed" ? "completed" : "pending",
                                duration_ms: msg.phases?.find(p => p.name.toLowerCase().includes("reflect"))?.timeMs,
                              }}
                            />
                          </motion.div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}

                {isLoading && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex justify-start"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shrink-0 mt-1">
                        <Sparkles size={14} className="animate-pulse" />
                      </div>
                      <div className="bg-white border border-slate-200 rounded-[24px] rounded-tl-sm px-6 py-4 flex items-center gap-2 h-[52px]">
                         <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce [animation-delay:-0.3s]" />
                         <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce [animation-delay:-0.15s]" />
                         <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" />
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
              <div ref={messagesEndRef} className="h-10" />
            </div>
          )}
        </div>
      </div>

      {/* COMPOSER SECTION */}
      <div className="relative z-20 shrink-0 px-4 pb-6 md:pb-10 pt-4 bg-gradient-to-t from-[#F8F9FA] via-[#F8F9FA] to-transparent">
        <div className="max-w-3xl mx-auto">
          {/* Quick Actions (Floating) */}
          <AnimatePresence>
             {messages.length > 0 && !isLoading && (
               <motion.div 
                 initial={{ opacity: 0, y: 10 }}
                 animate={{ opacity: 1, y: 0 }}
                 exit={{ opacity: 0, y: 10 }}
                 className="flex justify-center gap-2 mb-4"
               >
                 <button 
                   onClick={clearChat}
                   className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white border border-slate-200 text-slate-500 text-xs font-medium hover:bg-slate-50 transition-colors shadow-sm"
                 >
                   <RefreshCw size={12} /> New Chat
                 </button>
                 <button 
                   className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white border border-slate-200 text-slate-500 text-xs font-medium hover:bg-slate-50 transition-colors shadow-sm"
                 >
                   <MoreVertical size={12} /> Feedback
                 </button>
               </motion.div>
             )}
          </AnimatePresence>

          {/* Input Bar */}
          <div className={cn(
            "relative flex items-end gap-2 p-2 pl-6 bg-white border border-slate-200 rounded-[32px] shadow-lg focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-100 transition-all",
            styles["glass-composer"]
          )}>
            <textarea
              ref={inputRef}
              rows={1}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                target.style.height = `${Math.min(target.scrollHeight, 200)}px`;
              }}
              placeholder="Ask me to schedule or organize..."
              className="flex-1 max-h-[200px] py-3 bg-transparent border-0 focus:ring-0 text-[15px] text-slate-800 placeholder:text-slate-400 resize-none outline-none"
            />
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => handleSendMessage()}
              disabled={!inputValue.trim() || isLoading}
              className={cn(
                "mb-1 flex h-11 w-11 items-center justify-center rounded-full transition-all shadow-md",
                inputValue.trim() ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-400"
              )}
            >
              {isLoading ? <RefreshCw size={18} className="animate-spin" /> : <ArrowUp size={20} />}
            </motion.button>
          </div>
          <p className="text-center mt-3 text-[10px] text-slate-400 font-medium uppercase tracking-widest">
            AI Assistant may make mistakes. Verify important schedules.
          </p>
        </div>
      </div>

      <BottomNav />
    </div>
  );
}
