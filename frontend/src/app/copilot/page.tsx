"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  IconButton,
  Avatar,
  Chip,
  Button,
  Collapse,
} from "@mui/material";
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
  ChevronDown,
  ChevronUp,
  Eye,
  Brain,
  Zap,
  CheckCircle,
  Activity,
} from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";
import { useAuthContext } from "@/app/providers/auth-provider";
import { MobileSidebar } from "@/components/dashboard/MobileSidebar";
import { BottomNav } from "@/components/dashboard/BottomNav";
import { Header } from "@/components/dashboard/Header";
import { AgentExecutionTimeline } from "@/components/ui/Timeline";
import { aiAutomationApi, AIChatResponse } from "@/lib/ai-api";
import { toast } from "sonner";

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
  { icon: Calendar, label: "Schedule a meeting", prompt: "Help me schedule a meeting with my team for next Tuesday at 2 PM" },
  { icon: Clock, label: "Find free time", prompt: "When am I free this week for a 2-hour deep work session?" },
  { icon: Lightbulb, label: "Meeting insights", prompt: "Analyze my meeting patterns and suggest improvements" },
  { icon: Wand2, label: "Optimize schedule", prompt: "Optimize my schedule to reduce context switching" },
];

// No mock conversation - all messages come from real API

export default function CopilotPage() {
  const router = useRouter();
  const { user, isAuthenticated, loading: authLoading } = useAuthContext();
  const { isDark } = useTheme();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedAgentId, setExpandedAgentId] = useState<string | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  if (authLoading) {
    return (
      <Box sx={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          style={{
            width: 40,
            height: 40,
            borderRadius: "50%",
            border: "3px solid hsla(239, 84%, 67%, 0.2)",
            borderTopColor: "hsl(239, 84%, 67%)",
          }}
        />
      </Box>
    );
  }

  if (!isAuthenticated) {
    router.replace("/login");
    return null;
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await aiAutomationApi.sendChatMessage({
        message: userMessage.content,
        conversation_id: conversationId || undefined,
      });
      
      // Convert phases object to array for display
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
      
      // Store conversation ID for this session
      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id);
      }
      
      // Auto-expand agent execution details if agent was executed
      if (response.agent_executed) {
        setExpandedAgentId(aiResponse.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get response");
      toast.error("Failed to get AI response. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestedPrompt = (prompt: string) => {
    setInputValue(prompt);
    inputRef.current?.focus();
  };

  const copyMessage = (id: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background: isDark ? "hsl(240, 24%, 7%)" : "hsl(220, 14%, 96%)",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <MobileSidebar />

      <Box sx={{ px: { xs: 2, md: 4 }, pt: { xs: 2, md: 4 } }}>
        <Header
          userName={(user as any)?.name}
          userEmail={user?.email}
          userAvatar={(user as any)?.avatar}
          notificationCount={0}
        />
      </Box>

      <Container
        maxWidth="lg"
        sx={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          px: { xs: 2, md: 4 },
          py: 2,
          overflow: "hidden",
        }}
      >
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}
        >
          <Box sx={{ mb: 3, display: { xs: "none", sm: "block" } }}>
            <Typography
              variant="h4"
              sx={{
                fontWeight: 700,
                color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                mb: 1,
                display: "flex",
                alignItems: "center",
                gap: 1,
              }}
            >
              <Sparkles size={28} style={{ color: "hsl(239, 84%, 67%)" }} />
              AI Copilot
            </Typography>
            <Typography sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
              Your intelligent scheduling assistant
            </Typography>
          </Box>

          <Paper
            elevation={0}
            sx={{
              flex: 1,
              background: isDark
                ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
              border: "1px solid hsla(239, 84%, 67%, 0.15)",
              borderRadius: "16px",
              overflow: "auto",
              mb: 2,
              display: "flex",
              flexDirection: "column",
            }}
          >
            {messages.length === 0 ? (
              <Box
                sx={{
                  flex: 1,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  p: 4,
                  textAlign: "center",
                }}
              >
                <Box
                  sx={{
                    width: 80,
                    height: 80,
                    borderRadius: "20px",
                    background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    mb: 3,
                    boxShadow: "0 10px 40px -10px hsla(239, 84%, 67%, 0.5)",
                  }}
                >
                  <Bot size={40} color="white" />
                </Box>
                <Typography
                  variant="h5"
                  sx={{
                    fontWeight: 700,
                    color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                    mb: 1,
                  }}
                >
                  How can I help you today?
                </Typography>
                <Typography
                  sx={{
                    color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)",
                    mb: 4,
                    maxWidth: 500,
                  }}
                >
                  I can help schedule meetings, find free time, analyze your calendar, and optimize your schedule.
                </Typography>

                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2, justifyContent: "center" }}>
                  {suggestedPrompts.map((item, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Paper
                        onClick={() => handleSuggestedPrompt(item.prompt)}
                        sx={{
                          p: 2,
                          px: 3,
                          background: isDark
                            ? "hsla(239, 84%, 67%, 0.1)"
                            : "hsla(239, 84%, 67%, 0.05)",
                          border: "1px solid hsla(239, 84%, 67%, 0.2)",
                          borderRadius: "12px",
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          gap: 1.5,
                          transition: "all 0.2s ease",
                          "&:hover": {
                            background: isDark
                              ? "hsla(239, 84%, 67%, 0.15)"
                              : "hsla(239, 84%, 67%, 0.1)",
                            borderColor: "hsla(239, 84%, 67%, 0.4)",
                          },
                        }}
                      >
                        <item.icon size={18} style={{ color: "hsl(239, 84%, 67%)" }} />
                        <Typography
                          sx={{
                            fontWeight: 500,
                            color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                            fontSize: "0.875rem",
                          }}
                        >
                          {item.label}
                        </Typography>
                      </Paper>
                    </motion.div>
                  ))}
                </Box>
              </Box>
            ) : (
              <Box sx={{ p: 3, display: "flex", flexDirection: "column", gap: 3 }}>
                <AnimatePresence>
                  {messages.map((message) => (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ duration: 0.3 }}
                    >
                      <Box
                        sx={{
                          display: "flex",
                          gap: 2,
                          flexDirection: message.role === "user" ? "row-reverse" : "row",
                        }}
                      >
                        <Avatar
                          sx={{
                            width: 36,
                            height: 36,
                            background:
                              message.role === "user"
                                ? isDark
                                  ? "hsl(240, 24%, 22%)"
                                  : "hsl(220, 14%, 90%)"
                                : "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                            border:
                              message.role === "user"
                                ? `1px solid ${isDark ? "hsla(239, 84%, 67%, 0.2)" : "hsla(239, 84%, 67%, 0.1)"}`
                                : "none",
                          }}
                        >
                          {message.role === "user" ? (
                            <User size={18} style={{ color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }} />
                          ) : (
                            <Sparkles size={18} color="white" />
                          )}
                        </Avatar>

                        <Box sx={{ maxWidth: "80%" }}>
                          <Paper
                            elevation={0}
                            sx={{
                              p: 2,
                              px: 3,
                              background:
                                message.role === "user"
                                  ? isDark
                                    ? "hsla(239, 84%, 67%, 0.15)"
                                    : "hsla(239, 84%, 67%, 0.1)"
                                  : isDark
                                  ? "hsl(240, 24%, 14%)"
                                  : "hsl(0, 0%, 100%)",
                              border:
                                message.role === "assistant"
                                  ? `1px solid ${isDark ? "hsla(239, 84%, 67%, 0.15)" : "hsla(239, 84%, 67%, 0.1)"}`
                                  : "none",
                              borderRadius:
                                message.role === "user" ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
                            }}
                          >
                            <Typography
                              sx={{
                                color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                                lineHeight: 1.6,
                                whiteSpace: "pre-wrap",
                              }}
                            >
                              {message.content}
                            </Typography>
                          </Paper>

                          <Box
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              gap: 1,
                              mt: 0.5,
                              justifyContent: message.role === "user" ? "flex-end" : "flex-start",
                            }}
                          >
                            <Typography
                              sx={{
                                fontSize: "0.6875rem",
                                color: isDark ? "hsl(215, 16%, 40%)" : "hsl(215, 16%, 60%)",
                              }}
                            >
                              {message.timestamp.toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </Typography>
                            
                            {/* Agent executed badge */}
                            {message.agentExecuted && (
                              <Chip
                                size="small"
                                icon={<Activity size={12} />}
                                label={message.agentType || "Agent"}
                                onClick={() => setExpandedAgentId(
                                  expandedAgentId === message.id ? null : message.id
                                )}
                                sx={{
                                  height: "20px",
                                  fontSize: "0.65rem",
                                  fontWeight: 600,
                                  background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                                  color: "white",
                                  cursor: "pointer",
                                  "& .MuiChip-icon": {
                                    color: "white",
                                  },
                                  "&:hover": {
                                    opacity: 0.9,
                                  },
                                }}
                              />
                            )}
                            
                            {message.role === "assistant" && (
                              <IconButton
                                size="small"
                                onClick={() => copyMessage(message.id, message.content)}
                                sx={{
                                  width: 24,
                                  height: 24,
                                  color: copiedId === message.id ? "hsl(160, 84%, 39%)" : "hsl(215, 16%, 55%)",
                                }}
                              >
                                {copiedId === message.id ? <Check size={14} /> : <Copy size={14} />}
                              </IconButton>
                            )}
                          </Box>
                          
                          {/* Agent Execution Timeline */}
                          {message.agentExecuted && (
                            <Collapse in={expandedAgentId === message.id} timeout="auto" unmountOnExit>
                              <Box
                                sx={{
                                  mt: 2,
                                  p: 2,
                                  backgroundColor: isDark ? "hsla(239, 84%, 67%, 0.05)" : "hsla(239, 84%, 67%, 0.03)",
                                  borderRadius: "12px",
                                  border: `1px solid ${isDark ? "hsla(239, 84%, 67%, 0.1)" : "hsla(239, 84%, 67%, 0.08)"}`,
                                }}
                              >
                                <Box
                                  sx={{
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "space-between",
                                    mb: 2,
                                  }}
                                >
                                  <Typography
                                    variant="caption"
                                    sx={{
                                      fontWeight: 600,
                                      color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                                      display: "flex",
                                      alignItems: "center",
                                      gap: 0.5,
                                    }}
                                  >
                                    <Zap size={14} />
                                    Agent Execution Details
                                  </Typography>
                                  <IconButton
                                    size="small"
                                    onClick={() => setExpandedAgentId(null)}
                                    sx={{
                                      width: 24,
                                      height: 24,
                                      color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)",
                                    }}
                                  >
                                    <ChevronUp size={16} />
                                  </IconButton>
                                </Box>
                                
                                <AgentExecutionTimeline
                                  size="small"
                                  perception={{
                                    status: message.phases?.find(p => p.name.toLowerCase().includes("percep"))?.status === "completed" ? "completed" : "pending",
                                    duration_ms: message.phases?.find(p => p.name.toLowerCase().includes("percep"))?.timeMs,
                                  }}
                                  cognition={{
                                    status: message.phases?.find(p => p.name.toLowerCase().includes("cogn") || p.name.toLowerCase().includes("decis"))?.status === "completed" ? "completed" : "pending",
                                    duration_ms: message.phases?.find(p => p.name.toLowerCase().includes("cogn") || p.name.toLowerCase().includes("decis"))?.timeMs,
                                    decision: message.intent,
                                    confidence: message.phases?.find(p => p.name.toLowerCase().includes("cogn"))?.status === "completed" ? "High" : undefined,
                                  }}
                                  action={{
                                    status: message.phases?.find(p => p.name.toLowerCase().includes("action"))?.status === "completed" ? "completed" : "pending",
                                    duration_ms: message.phases?.find(p => p.name.toLowerCase().includes("action"))?.timeMs,
                                  }}
                                  reflection={{
                                    status: message.phases?.find(p => p.name.toLowerCase().includes("reflect"))?.status === "completed" ? "completed" : "pending",
                                    duration_ms: message.phases?.find(p => p.name.toLowerCase().includes("reflect"))?.timeMs,
                                  }}
                                />
                              </Box>
                            </Collapse>
                          )}
                        </Box>
                      </Box>
                    </motion.div>
                  ))}
                </AnimatePresence>

                {isLoading && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                    <Box sx={{ display: "flex", gap: 2 }}>
                      <Avatar
                        sx={{
                          width: 36,
                          height: 36,
                          background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                        }}
                      >
                        <Sparkles size={18} color="white" />
                      </Avatar>
                      <Paper
                        sx={{
                          p: 2,
                          px: 3,
                          background: isDark ? "hsl(240, 24%, 14%)" : "hsl(0, 0%, 100%)",
                          border: `1px solid ${isDark ? "hsla(239, 84%, 67%, 0.15)" : "hsla(239, 84%, 67%, 0.1)"}`,
                          borderRadius: "16px 16px 16px 4px",
                          display: "flex",
                          alignItems: "center",
                          gap: 1,
                        }}
                      >
                        <Box
                          sx={{
                            display: "flex",
                            gap: 0.5,
                            "& span": {
                              width: 8,
                              height: 8,
                              borderRadius: "50%",
                              background: "hsl(239, 84%, 67%)",
                              animation: "pulse 1.4s ease-in-out infinite",
                              "&:nth-of-type(2)": { animationDelay: "0.2s" },
                              "&:nth-of-type(3)": { animationDelay: "0.4s" },
                            },
                            "@keyframes pulse": {
                              "0%, 80%, 100%": { transform: "scale(0.6)", opacity: 0.5 },
                              "40%": { transform: "scale(1)", opacity: 1 },
                            },
                          }}
                        >
                          <span />
                          <span />
                          <span />
                        </Box>
                      </Paper>
                    </Box>
                  </motion.div>
                )}

                <div ref={messagesEndRef} />
              </Box>
            )}
          </Paper>

          <Paper
            elevation={0}
            sx={{
              p: 2,
              background: isDark
                ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
              border: "1px solid hsla(239, 84%, 67%, 0.15)",
              borderRadius: "16px",
              display: "flex",
              alignItems: "center",
              gap: 1,
            }}
          >
            <TextField
              inputRef={inputRef}
              fullWidth
              placeholder="Ask me to schedule a meeting, find free time, or optimize your calendar..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              multiline
              maxRows={4}
              variant="outlined"
              sx={{
                "& .MuiOutlinedInput-root": {
                  background: "transparent",
                  borderRadius: "12px",
                  color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                  "& fieldset": { border: "none" },
                  "& textarea": {
                    padding: "8px 0",
                    "&::placeholder": {
                      color: isDark ? "hsl(215, 16%, 40%)" : "hsl(215, 16%, 60%)",
                    },
                  },
                },
              }}
            />

            <Box sx={{ display: "flex", gap: 1 }}>
              {messages.length > 0 && (
                <IconButton
                  onClick={clearChat}
                  sx={{
                    color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)",
                    "&:hover": { color: "hsl(346, 84%, 61%)" },
                  }}
                >
                  <Trash2 size={20} />
                </IconButton>
              )}

              <IconButton
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                sx={{
                  width: 44,
                  height: 44,
                  background: inputValue.trim()
                    ? "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)"
                    : isDark
                    ? "hsl(240, 24%, 22%)"
                    : "hsl(220, 14%, 90%)",
                  color: inputValue.trim() ? "white" : isDark ? "hsl(215, 16%, 40%)" : "hsl(215, 16%, 60%)",
                  borderRadius: "12px",
                  transition: "all 0.2s ease",
                  "&:hover": inputValue.trim()
                    ? {
                        background: "linear-gradient(135deg, hsl(239, 84%, 57%) 0%, hsl(330, 81%, 50%) 100%)",
                        transform: "scale(1.05)",
                      }
                    : {},
                  "&:disabled": {
                    opacity: 0.5,
                  },
                }}
              >
                <Send size={20} />
              </IconButton>
            </Box>
          </Paper>
        </motion.div>
      </Container>

      <BottomNav />
    </Box>
  );
}
