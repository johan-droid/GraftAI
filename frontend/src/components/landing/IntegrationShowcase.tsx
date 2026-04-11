"use client";

import { Box, Typography, Container, Grid, Chip } from "@mui/material";
import { motion } from "framer-motion";
import { 
  Calendar, 
  Video, 
  MessageSquare, 
  Mail, 
  FileText,
  Clock,
  CheckCircle2,
  ArrowRight
} from "lucide-react";
import Link from "next/link";
import { GradientButton } from "@/components/ui/GradientButton";

const integrations = [
  {
    category: "Calendars",
    color: "#6366f1",
    tools: ["Google Calendar", "Outlook", "Apple Calendar", "CalDAV"],
    icon: Calendar,
  },
  {
    category: "Video Conferencing",
    color: "#ec4899",
    tools: ["Zoom", "Google Meet", "Microsoft Teams", "Webex"],
    icon: Video,
  },
  {
    category: "Communication",
    color: "#10b981",
    tools: ["Slack", "Discord", "Telegram", "WhatsApp"],
    icon: MessageSquare,
  },
  {
    category: "Email",
    color: "#f59e0b",
    tools: ["Gmail", "Outlook 365", "ProtonMail", "iCloud"],
    icon: Mail,
  },
  {
    category: "Productivity",
    color: "#8b5cf6",
    tools: ["Notion", "Asana", "Trello", "Linear"],
    icon: FileText,
  },
  {
    category: "Time Tracking",
    color: "#06b6d4",
    tools: ["Toggl", "Clockify", "Harvest", "RescueTime"],
    icon: Clock,
  },
];

export function IntegrationShowcase() {
  return (
    <Box sx={{ py: { xs: 10, md: 16 } }}>
      <Container maxWidth="lg">
        {/* Header */}
        <Box sx={{ textAlign: "center", mb: { xs: 6, md: 10 } }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
          >
            <Chip
              label="50+ Integrations"
              sx={{
                mb: 2,
                background: "rgba(99, 102, 241, 0.1)",
                color: "#a5b4fc",
                border: "1px solid rgba(99, 102, 241, 0.3)",
              }}
            />
            <Typography
              variant="h2"
              sx={{ fontSize: { xs: "1.75rem", sm: "2.25rem", md: "3rem" }, fontWeight: 800, mb: 2 }}
            >
              Works With Your{" "}
              <Box
                component="span"
                sx={{
                  background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Favorite Tools
              </Box>
            </Typography>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            viewport={{ once: true }}
          >
            <Typography variant="body1" sx={{ color: "#94a3b8", maxWidth: 600, mx: "auto" }}>
              Connect GraftAI with the tools you already use. One-click setup, seamless synchronization.
            </Typography>
          </motion.div>
        </Box>

        {/* Integration Grid */}
        <Grid container spacing={3}>
          {integrations.map((integration, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                style={{ height: "100%" }}
              >
                <Box
                  sx={{
                    height: "100%",
                    p: 3,
                    background: "linear-gradient(135deg, rgba(26, 26, 46, 0.8) 0%, rgba(15, 15, 26, 0.9) 100%)",
                    border: "1px solid rgba(99, 102, 241, 0.1)",
                    borderRadius: 3,
                    transition: "all 0.3s ease",
                    "&:hover": {
                      borderColor: `${integration.color}50`,
                      transform: "translateY(-4px)",
                      boxShadow: `0 20px 40px -20px ${integration.color}30`,
                    },
                  }}
                >
                  <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
                    <Box
                      sx={{
                        width: 48,
                        height: 48,
                        borderRadius: 2,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        background: `${integration.color}20`,
                      }}
                    >
                      <integration.icon size={24} style={{ color: integration.color }} />
                    </Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {integration.category}
                    </Typography>
                  </Box>

                  <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                    {integration.tools.map((tool) => (
                      <Chip
                        key={tool}
                        label={tool}
                        size="small"
                        sx={{
                          background: "rgba(99, 102, 241, 0.1)",
                          color: "#94a3b8",
                          fontSize: "0.75rem",
                          "&:hover": {
                            background: `${integration.color}30`,
                            color: "#f8fafc",
                          },
                        }}
                      />
                    ))}
                  </Box>

                  <Box sx={{ mt: 2, display: "flex", alignItems: "center", gap: 0.5, color: "#10b981" }}>
                    <CheckCircle2 size={14} />
                    <Typography variant="caption" sx={{ fontWeight: 500 }}>
                      One-click setup
                    </Typography>
                  </Box>
                </Box>
              </motion.div>
            </Grid>
          ))}
        </Grid>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          viewport={{ once: true }}
        >
          <Box sx={{ textAlign: "center", mt: 6 }}>
            <GradientButton
              component={Link}
              href="/integrations"
              gradientVariant="secondary"
              size="large"
            >
              View All Integrations
              <ArrowRight size={18} style={{ marginLeft: 8 }} />
            </GradientButton>
          </Box>
        </motion.div>
      </Container>
    </Box>
  );
}
