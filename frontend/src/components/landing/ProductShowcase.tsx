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
  Check
} from "lucide-react";

const tabs = [
  {
    id: "overview",
    label: "Overview",
    icon: LayoutDashboard,
    title: "Everything in One Place",
    description: "Your unified command center for all scheduling needs. View calendars, manage meetings, and track productivity all from a single dashboard.",
    features: ["Unified calendar view", "Meeting analytics", "Productivity insights", "Quick actions"],
  },
  {
    id: "calendar",
    label: "Calendar",
    icon: Calendar,
    title: "Smart Calendar Management",
    description: "AI-powered calendar that learns your preferences and automatically optimizes your schedule for maximum productivity.",
    features: ["Multi-calendar sync", "AI time blocking", "Conflict detection", "Smart suggestions"],
  },
  {
    id: "ai",
    label: "AI Features",
    icon: Sparkles,
    title: "Intelligent Scheduling",
    description: "Let our advanced AI handle the heavy lifting. From finding optimal meeting times to protecting your focus hours.",
    features: ["Natural language scheduling", "Auto-meeting notes", "Smart reminders", "Focus time protection"],
  },
  {
    id: "integrations",
    label: "Integrations",
    icon: Plug,
    title: "Connect Your Tools",
    description: "Seamlessly integrate with your favorite productivity tools. Works with Google, Outlook, Zoom, Slack, and 50+ more.",
    features: ["Google & Outlook sync", "Zoom & Teams integration", "Slack notifications", "API access"],
  },
  {
    id: "security",
    label: "Security",
    icon: Shield,
    title: "Enterprise-Grade Security",
    description: "Bank-level encryption and compliance standards to keep your data safe. SOC 2 Type II certified and GDPR compliant.",
    features: ["End-to-end encryption", "SOC 2 compliant", "SSO & SAML", "Audit logs"],
  },
];

export function ProductShowcase() {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <Box sx={{ py: { xs: 10, md: 16 }, background: "rgba(26, 26, 46, 0.3)" }}>
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
              sx={{ fontSize: { xs: "1.75rem", sm: "2.25rem", md: "3rem" }, fontWeight: 800, mb: 2 }}
            >
              Powerful Features for{" "}
              <Box
                component="span"
                sx={{
                  background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Modern Teams
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
                gap: 1,
              },
              "& .MuiTabs-scrollButtons": {
                color: "#94a3b8",
              },
              "& .MuiTabs-indicator": {
                background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                height: 3,
                borderRadius: "3px 3px 0 0",
              },
            }}
          >
            {tabs.map((tab, index) => (
              <Tab
                key={tab.id}
                label={
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, py: 1 }}>
                    <tab.icon size={18} />
                    <span>{tab.label}</span>
                  </Box>
                }
                sx={{
                  textTransform: "none",
                  color: "#94a3b8",
                  fontWeight: 500,
                  minWidth: { xs: "auto", md: 140 },
                  px: { xs: 2, md: 3 },
                  borderRadius: "8px 8px 0 0",
                  "&.Mui-selected": {
                    color: "#f8fafc",
                    background: "rgba(99, 102, 241, 0.1)",
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
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <Box
              sx={{
                display: "flex",
                flexDirection: { xs: "column", md: "row" },
                gap: { xs: 4, md: 6 },
                alignItems: "center",
              }}
            >
              {/* Content */}
              <Box sx={{ flex: 1, order: { xs: 2, md: 1 } }}>
                <Typography
                  variant="h4"
                  sx={{ fontWeight: 700, mb: 2, fontSize: { xs: "1.5rem", md: "2rem" } }}
                >
                  {tabs[activeTab].title}
                </Typography>
                <Typography variant="body1" sx={{ color: "#94a3b8", mb: 4, fontSize: "1.125rem" }}>
                  {tabs[activeTab].description}
                </Typography>
                <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                  {tabs[activeTab].features.map((feature, index) => (
                    <motion.div
                      key={feature}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                        <Box
                          sx={{
                            width: 24,
                            height: 24,
                            borderRadius: "50%",
                            background: "rgba(16, 185, 129, 0.2)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                          }}
                        >
                          <Check size={14} style={{ color: "#10b981" }} />
                        </Box>
                        <Typography sx={{ color: "#e2e8f0" }}>{feature}</Typography>
                      </Box>
                    </motion.div>
                  ))}
                </Box>
              </Box>

              {/* Visual Demo */}
              <Box
                sx={{
                  flex: 1,
                  order: { xs: 1, md: 2 },
                  width: "100%",
                }}
              >
                <Box
                  sx={{
                    background: "linear-gradient(135deg, rgba(26, 26, 46, 0.9) 0%, rgba(15, 15, 26, 0.95) 100%)",
                    borderRadius: 3,
                    border: "1px solid rgba(99, 102, 241, 0.2)",
                    boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
                    overflow: "hidden",
                    aspectRatio: "16/10",
                    position: "relative",
                  }}
                >
                  {/* Fake Browser Header */}
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      px: 2,
                      py: 1.5,
                      borderBottom: "1px solid rgba(99, 102, 241, 0.1)",
                      background: "rgba(15, 15, 26, 0.5)",
                    }}
                  >
                    <Box sx={{ display: "flex", gap: 0.5 }}>
                      <Box sx={{ width: 10, height: 10, borderRadius: "50%", background: "#ef4444" }} />
                      <Box sx={{ width: 10, height: 10, borderRadius: "50%", background: "#f59e0b" }} />
                      <Box sx={{ width: 10, height: 10, borderRadius: "50%", background: "#10b981" }} />
                    </Box>
                  </Box>

                  {/* Demo Content Based on Tab */}
                  <Box sx={{ p: 3 }}>
                    {activeTab === 0 && (
                      <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                        <Box sx={{ height: 40, background: "rgba(99, 102, 241, 0.1)", borderRadius: 1 }} />
                        <Box sx={{ display: "flex", gap: 2 }}>
                          <Box sx={{ flex: 1, height: 120, background: "rgba(99, 102, 241, 0.05)", borderRadius: 1 }} />
                          <Box sx={{ flex: 1, height: 120, background: "rgba(236, 72, 153, 0.05)", borderRadius: 1 }} />
                        </Box>
                      </Box>
                    )}
                    {activeTab === 1 && (
                      <Box sx={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: 1 }}>
                        {Array.from({ length: 28 }).map((_, i) => (
                          <Box
                            key={i}
                            sx={{
                              aspectRatio: "1",
                              background: i % 3 === 0 ? "rgba(99, 102, 241, 0.2)" : "rgba(99, 102, 241, 0.05)",
                              borderRadius: 0.5,
                            }}
                          />
                        ))}
                      </Box>
                    )}
                    {activeTab === 2 && (
                      <Box sx={{ display: "flex", flexDirection: "column", gap: 2, alignItems: "center", justifyContent: "center", height: "100%" }}>
                        <Sparkles size={48} style={{ color: "#6366f1", opacity: 0.5 }} />
                        <Typography sx={{ color: "#64748b" }}>AI Processing...</Typography>
                      </Box>
                    )}
                    {activeTab === 3 && (
                      <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", justifyContent: "center" }}>
                        {["Google", "Zoom", "Slack", "Teams", "Notion"].map((name) => (
                          <Box
                            key={name}
                            sx={{
                              px: 3,
                              py: 1.5,
                              background: "rgba(99, 102, 241, 0.1)",
                              borderRadius: 2,
                              border: "1px solid rgba(99, 102, 241, 0.2)",
                            }}
                          >
                            <Typography sx={{ color: "#94a3b8" }}>{name}</Typography>
                          </Box>
                        ))}
                      </Box>
                    )}
                    {activeTab === 4 && (
                      <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                        <Box sx={{ display: "flex", alignItems: "center", gap: 2, p: 2, background: "rgba(16, 185, 129, 0.1)", borderRadius: 1 }}>
                          <Shield size={20} style={{ color: "#10b981" }} />
                          <Typography sx={{ color: "#10b981" }}>End-to-End Encrypted</Typography>
                        </Box>
                        <Box sx={{ display: "flex", alignItems: "center", gap: 2, p: 2, background: "rgba(99, 102, 241, 0.05)", borderRadius: 1 }}>
                          <Check size={20} style={{ color: "#6366f1" }} />
                          <Typography sx={{ color: "#94a3b8" }}>SOC 2 Type II Certified</Typography>
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
