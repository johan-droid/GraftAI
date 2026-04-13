"use client";

import { useState } from "react";
import { Box, Typography, Container, Tabs, Tab } from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import { 
  LayoutDashboard, 
  Calendar, 
  Sparkles, 
  Plug, 
  Shield,
  Check,
  Globe,
  Lock,
  Zap,
  Cpu
} from "lucide-react";

const tabs = [
  {
    id: "overview",
    label: "NODE_OVERVIEW",
    icon: LayoutDashboard,
    title: "System Command Center",
    description: "Your unified telemetry dashboard for all scheduling operations. Orchestrate meetings, calibrate logic, and monitor productivity throughput from a single high-fidelity terminal.",
    features: ["UNIFIED_NODE_STATE", "METRIC_ANALYTICS", "THROUGHPUT_INSIGHTS", "RAPID_EXEC_ACTIONS"],
  },
  {
    id: "calendar",
    label: "SYNC_ENGINE",
    icon: Calendar,
    title: "Heuristic Calendar Core",
    description: "Binary-optimized scheduling that adapts to your work-life heuristics. Automatically clusters workloads for peak focus-efficiency.",
    features: ["CLUSTER_SYNC", "AI_TIME_BLOCKING", "COLLISION_DETECTION", "SMART_SUGGESTIONS"],
  },
  {
    id: "ai",
    label: "COGNITIVE_AI",
    icon: Sparkles,
    title: "Intelligent Kernel Logic",
    description: "Autonomous scheduling agents handle high-latency coordination. Built on advanced LLM-logic to protect focus-cycles and eliminate scheduling overhead.",
    features: ["NL_PARSER", "AUTO_SUMMARY", "PROACTIVE_ALERTS", "FOCUS_ISOLATION"],
  },
  {
    id: "integrations",
    label: "CLUSTER_PLUGINS",
    icon: Plug,
    title: "Seamless Plugin Layer",
    description: "Modular architecture supports 50+ third-party nodes. Extend your capability with Google, Outlook, Slack, and dedicated API hooks.",
    features: ["MULTI_NODE_SYNC", "PROTOCOL_BRIDGES", "SLACK_WEBHOOKS", "MASTER_API_ACCESS"],
  },
  {
    id: "security",
    label: "SECURITY_MESH",
    icon: Shield,
    title: "Encryption Layer Protection",
    description: "Hardened security protocols protect every data packet. Built with AES-256 standards and SOC 2 hardened infrastructure.",
    features: ["E2E_ENCRYPTION", "SOC_2_READY", "SAML_AUTH_V2", "EVENT_AUDIT_LOGS"],
  },
];

export function ProductShowcase() {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <Box sx={{ py: { xs: 10, md: 16 }, background: "transparent", position: "relative" }}>
      <Container maxWidth="lg">
        {/* Header */}
        <Box sx={{ textAlign: "center", mb: { xs: 6, md: 8 } }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
          >
            <Typography
              variant="h2"
              sx={{ 
                fontSize: { xs: "1.75rem", sm: "2.25rem", md: "3rem" }, 
                fontWeight: 800, 
                mb: 2,
                fontFamily: "var(--font-mono)",
                textTransform: "uppercase"
              }}
            >
              System Operating{" "}
              <Box
                component="span"
                sx={{
                  color: "var(--primary)",
                }}
              >
                Features
              </Box>
            </Typography>
          </motion.div>
        </Box>

        {/* Tabs */}
        <Box sx={{ mb: { xs: 4, md: 6 } }}>
          <Tabs
            value={activeTab}
            onChange={(_, newValue) => setActiveTab(newValue)}
            variant="scrollable"
            scrollButtons="auto"
            allowScrollButtonsMobile
            sx={{
              "& .MuiTabs-flexContainer": {
                justifyContent: { xs: "flex-start", md: "center" },
                gap: 2,
              },
              "& .MuiTabs-scrollButtons": {
                color: "var(--text-secondary)",
              },
              "& .MuiTabs-indicator": {
                background: "var(--primary)",
                height: 2,
              },
            }}
          >
            {tabs.map((tab, index) => (
              <Tab
                key={tab.id}
                label={
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, py: 1 }}>
                    <tab.icon size={16} />
                    <span>{tab.label}</span>
                  </Box>
                }
                sx={{
                  textTransform: "uppercase",
                  color: "var(--text-secondary)",
                  fontWeight: 800,
                  fontSize: "11px",
                  fontFamily: "var(--font-mono)",
                  minWidth: { xs: "auto", md: 160 },
                  px: { xs: 2, md: 3 },
                  borderRadius: 0,
                  transition: "all 0.2s",
                  "&.Mui-selected": {
                    color: "var(--primary)",
                    background: "rgba(0, 255, 156, 0.05)",
                  },
                }}
              />
            ))}
          </Tabs>
        </Box>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            transition={{ duration: 0.3 }}
          >
            <Box
              sx={{
                display: "flex",
                flexDirection: { xs: "column", md: "row" },
                gap: { xs: 4, md: 8 },
                alignItems: "flex-start",
              }}
            >
              {/* Content */}
              <Box sx={{ flex: 1, order: { xs: 2, md: 1 } }}>
                <Typography
                  variant="h3"
                  sx={{ 
                    fontWeight: 800, 
                    mb: 3, 
                    fontSize: { xs: "1.5rem", md: "2.25rem" },
                    fontFamily: "var(--font-mono)",
                    textTransform: "uppercase"
                  }}
                >
                  {tabs[activeTab].title}
                </Typography>
                <Typography 
                  variant="body1" 
                  sx={{ 
                    color: "var(--text-muted)", 
                    mb: 6, 
                    fontSize: "15px",
                    lineHeight: 1.8,
                    fontFamily: "var(--font-mono)"
                  }}
                >
                   {"> "} {tabs[activeTab].description}
                </Typography>
                <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 3 }}>
                  {tabs[activeTab].features.map((feature, index) => (
                    <motion.div
                      key={feature}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <Box 
                        sx={{ 
                          display: "flex", 
                          alignItems: "center", 
                          gap: 1.5,
                          p: 1.5,
                          border: "1px dashed var(--border-subtle)",
                          "&:hover": { borderColor: "var(--primary)" }
                        }}
                      >
                        <Zap size={10} style={{ color: "var(--primary)" }} />
                        <Typography sx={{ color: "var(--text-primary)", fontSize: "10px", fontFamily: "var(--font-mono)", fontWeight: 700 }}>
                          {feature}
                        </Typography>
                      </Box>
                    </motion.div>
                  ))}
                </Box>
              </Box>

              {/* Visual Demo */}
              <Box
                sx={{
                  flex: 1.2,
                  order: { xs: 1, md: 2 },
                  width: "100%",
                }}
              >
                <Box
                  sx={{
                    background: "#0a0a0a",
                    borderRadius: 0,
                    border: "1px solid var(--border-subtle)",
                    boxShadow: "0 20px 40px rgba(0, 0, 0, 0.4)",
                    overflow: "hidden",
                    aspectRatio: "16/10",
                    position: "relative",
                  }}
                >
                  {/* Technical Browser Header */}
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      px: 2,
                      py: 1.5,
                      borderBottom: "1px solid var(--border-subtle)",
                      background: "rgba(255, 255, 255, 0.05)",
                    }}
                  >
                    <Box sx={{ display: "flex", gap: 1 }}>
                      <Box sx={{ width: 8, height: 8, background: "var(--border-subtle)" }} />
                      <Box sx={{ width: 8, height: 8, background: "var(--border-subtle)" }} />
                      <Box sx={{ width: 8, height: 8, background: "var(--border-subtle)" }} />
                    </Box>
                    <Typography
                      sx={{ 
                        fontSize: "9px", 
                        fontFamily: "var(--font-mono)", 
                        color: "var(--text-secondary)",
                        textTransform: "uppercase",
                        letterSpacing: "0.2em",
                        fontWeight: 700
                      }}
                    >
                      LOCAL_SYSTEM_MONITOR_v2.0
                    </Typography>
                    <Globe size={10} style={{ color: "var(--text-secondary)" }} />
                  </Box>

                  {/* Demo Content Based on Tab */}
                  <Box sx={{ p: 4, height: "calc(100% - 40px)", position: "relative" }}>
                    {activeTab === 0 && (
                      <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
                         <Box sx={{ display: "flex", gap: 3 }}>
                            <Box sx={{ flex: 1, height: 80, border: "1px dashed var(--primary)", opacity: 0.4 }} />
                            <Box sx={{ flex: 1, height: 80, border: "1px dashed var(--accent)", opacity: 0.4 }} />
                            <Box sx={{ flex: 1, height: 80, border: "1px dashed var(--primary)", opacity: 0.4 }} />
                         </Box>
                         <Box sx={{ height: 160, border: "1px solid var(--border-subtle)", position: "relative" }}>
                            <Box sx={{ position: "absolute", top: 20, left: 20, width: "60%", height: 10, background: "var(--primary)", opacity: 0.2 }} />
                            <Box sx={{ position: "absolute", top: 40, left: 20, width: "40%", height: 10, background: "var(--accent)", opacity: 0.2 }} />
                            <Box sx={{ position: "absolute", bottom: 20, left: 20, right: 20, height: 40, borderTop: "1px dashed var(--border-subtle)" }} />
                         </Box>
                      </Box>
                    )}
                    {activeTab === 1 && (
                      <Box sx={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: 1.5 }}>
                        {Array.from({ length: 28 }).map((_, i) => (
                          <Box
                            key={i}
                            sx={{
                              aspectRatio: "1",
                              border: "1px solid var(--border-subtle)",
                              background: i % 3 === 0 ? "rgba(0, 255, 156, 0.1)" : "transparent",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              fontSize: "8px",
                              fontFamily: "var(--font-mono)",
                              color: "var(--text-primary)",
                              fontWeight: 800
                            }}
                          >
                            {i + 1}
                          </Box>
                        ))}
                      </Box>
                    )}
                    {activeTab === 2 && (
                      <Box sx={{ display: "flex", flexDirection: "column", gap: 3, alignItems: "center", justifyContent: "center", height: "100%" }}>
                        <Cpu size={48} style={{ color: "var(--primary)", opacity: 0.6 }} className="pulse" />
                        <Typography sx={{ color: "var(--primary)", fontFamily: "var(--font-mono)", fontSize: "12px", textTransform: "uppercase" }}>
                          PROCESS_SYNC: CORE_LOGIC_ACTIVE
                        </Typography>
                        <Box sx={{ width: "200px", height: "2px", background: "var(--border-subtle)", position: "relative" }}>
                           <motion.div 
                             animate={{ x: [0, 198, 0] }}
                             transition={{ duration: 2, repeat: Infinity }}
                             style={{ width: "20px", height: "2px", background: "var(--primary)", position: "absolute" }} 
                           />
                        </Box>
                      </Box>
                    )}
                    {activeTab === 3 && (
                      <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}>
                        {["GOOGLE_SYNC", "ZOOM_CONNECT", "SLACK_RELAY", "MICROSOFT_365", "NOTION_DB", "CUSTOM_HOOK"].map((name) => (
                          <Box
                            key={name}
                            sx={{
                              p: 2,
                              background: "rgba(255, 255, 255, 0.02)",
                              border: "1px dashed var(--border-subtle)",
                              "&:hover": { borderColor: "var(--primary)" }
                            }}
                          >
                            <Typography sx={{ color: "var(--text-muted)", fontSize: "9px", fontFamily: "var(--font-mono)" }}>
                              {name} :: ACTIVE
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    )}
                    {activeTab === 4 && (
                      <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
                        <Box sx={{ p: 3, border: "1px solid var(--primary)", background: "rgba(0, 255, 156, 0.05)" }}>
                          <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1 }}>
                            <Lock size={16} style={{ color: "var(--primary)" }} />
                            <Typography sx={{ color: "var(--primary)", fontSize: "11px", fontWeight: 700, fontFamily: "var(--font-mono)" }}>
                              ENC_READY
                            </Typography>
                          </Box>
                          <Typography sx={{ color: "var(--text-muted)", fontSize: "9px", fontFamily: "var(--font-mono)" }}>
                            DATA_PACKET: STATUS=ENCRYPTED :: ALG=AES256
                          </Typography>
                        </Box>
                        <Box sx={{ p: 3, border: "1px solid var(--border-subtle)", opacity: 0.6 }}>
                           <Typography sx={{ color: "var(--text-faint)", fontSize: "9px", fontFamily: "var(--font-mono)" }}>
                              WAITING_FOR_HANDSHAKE...
                           </Typography>
                        </Box>
                      </Box>
                    )}
                  </Box>
                </Box>
              </Box>
            </Box>
          </motion.div>
        </AnimatePresence>
      </Container>
    </Box>
  );
}
