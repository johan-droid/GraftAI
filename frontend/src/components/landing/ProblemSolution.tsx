"use client";

import { Box, Typography, Container, Grid, Paper } from "@mui/material";
import { motion } from "framer-motion";
import { MessageSquareX, Brain, AlertTriangle, Check, Clock, CalendarCheck } from "lucide-react";

const painPoints = [
  {
    icon: MessageSquareX,
    pain: "8+ emails just to schedule one meeting",
    solution: "AI suggests 3 optimal times instantly",
    color: "#6366f1",
  },
  {
    icon: Brain,
    pain: "Constant interruptions kill productivity",
    solution: "Auto-blocks deep work sessions",
    color: "#ec4899",
  },
  {
    icon: AlertTriangle,
    pain: "Double-bookings and timezone confusion",
    solution: "Smart conflict detection across all calendars",
    color: "#10b981",
  },
];

export function ProblemSolution() {
  return (
    <Box id="features" sx={{ py: { xs: 10, md: 16 } }}>
      <Container maxWidth="lg">
        {/* Section Header */}
        <Box sx={{ textAlign: "center", mb: { xs: 6, md: 10 } }}>
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
                mb: 3,
                maxWidth: 800,
                mx: "auto",
              }}
            >
              Stop Calendar Chaos.{" "}
              <Box
                component="span"
                sx={{
                  background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Start Smart Scheduling.
              </Box>
            </Typography>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            viewport={{ once: true }}
          >
            <Typography variant="body1" sx={{ color: "#94a3b8", maxWidth: 600, mx: "auto", fontSize: "1.125rem" }}>
              Three ways GraftAI transforms your scheduling nightmare into a productivity dream.
            </Typography>
          </motion.div>
        </Box>

        {/* Pain Point Cards */}
        <Grid container spacing={3}>
          {painPoints.map((point, index) => (
            <Grid item xs={12} md={4} key={index}>
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                style={{ height: "100%" }}
              >
                <Paper
                  sx={{
                    height: "100%",
                    p: { xs: 3, md: 4 },
                    background: "linear-gradient(135deg, rgba(26, 26, 46, 0.8) 0%, rgba(15, 15, 26, 0.9) 100%)",
                    border: "1px solid rgba(99, 102, 241, 0.1)",
                    borderRadius: 3,
                    position: "relative",
                    overflow: "hidden",
                    transition: "all 0.3s ease",
                    "&:hover": {
                      borderColor: point.color,
                      transform: "translateY(-4px)",
                      boxShadow: `0 20px 40px -20px ${point.color}20`,
                    },
                  }}
                >
                  {/* Background Glow */}
                  <Box
                    sx={{
                      position: "absolute",
                      top: -50,
                      right: -50,
                      width: 150,
                      height: 150,
                      background: `radial-gradient(circle, ${point.color}20 0%, transparent 70%)`,
                      borderRadius: "50%",
                    }}
                  />

                  <Box sx={{ position: "relative", zIndex: 1 }}>
                    {/* Icon */}
                    <Box
                      sx={{
                        width: 56,
                        height: 56,
                        borderRadius: 2,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        background: `linear-gradient(135deg, ${point.color}30 0%, ${point.color}10 100%)`,
                        mb: 3,
                      }}
                    >
                      <point.icon size={28} style={{ color: point.color }} />
                    </Box>

                    {/* Pain */}
                    <Typography
                      variant="body2"
                      sx={{
                        color: "#64748b",
                        mb: 1,
                        display: "flex",
                        alignItems: "center",
                        gap: 0.5,
                        fontSize: "0.875rem",
                      }}
                    >
                      <MessageSquareX size={14} />
                      Before: {point.pain}
                    </Typography>

                    {/* Divider */}
                    <Box sx={{ width: "100%", height: 1, background: "rgba(99, 102, 241, 0.1)", my: 2 }} />

                    {/* Solution */}
                    <Typography
                      variant="body1"
                      sx={{
                        color: "#f8fafc",
                        display: "flex",
                        alignItems: "flex-start",
                        gap: 1,
                        fontWeight: 500,
                      }}
                    >
                      <Check size={18} style={{ color: "#10b981", flexShrink: 0, marginTop: 2 }} />
                      {point.solution}
                    </Typography>
                  </Box>
                </Paper>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
}
