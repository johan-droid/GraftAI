"use client";

import { Box, Typography, Container, Grid, Paper } from "@mui/material";
import { motion } from "framer-motion";
import { 
  Sparkles, 
  Calendar, 
  Shield, 
  Clock, 
  BarChart3, 
  Users,
  Zap,
  Globe
} from "lucide-react";

const features = [
  {
    icon: Sparkles,
    title: "AI-Powered Scheduling",
    description: "Learns your preferences and optimizes your calendar automatically. The more you use it, the smarter it gets.",
    size: "large",
    gradient: "linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(236, 72, 153, 0.1) 100%)",
  },
  {
    icon: Calendar,
    title: "Smart Conflict Resolution",
    description: "Detects and fixes double-bookings across all your calendars instantly.",
    size: "medium",
    gradient: "linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(16, 185, 129, 0.05) 100%)",
  },
  {
    icon: Globe,
    title: "Cross-Platform Sync",
    description: "Real-time sync with Google, Outlook, Apple Calendar, and more.",
    size: "medium",
    gradient: "linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(99, 102, 241, 0.05) 100%)",
  },
  {
    icon: Clock,
    title: "Focus Time Protection",
    description: "AI automatically blocks focus sessions and defends them from meeting requests.",
    size: "medium",
    gradient: "linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(245, 158, 11, 0.05) 100%)",
  },
  {
    icon: BarChart3,
    title: "Meeting Analytics",
    description: "Track time spent in meetings, identify patterns, and optimize your schedule.",
    size: "small",
    gradient: "linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(99, 102, 241, 0.05) 100%)",
  },
  {
    icon: Users,
    title: "Team Coordination",
    description: "Find optimal meeting times across your entire team's schedules.",
    size: "small",
    gradient: "linear-gradient(135deg, rgba(236, 72, 153, 0.15) 0%, rgba(236, 72, 153, 0.05) 100%)",
  },
];

export function FeatureBento() {
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
            <Typography
              variant="h2"
              sx={{ fontSize: { xs: "1.75rem", sm: "2.25rem", md: "3rem" }, fontWeight: 800, mb: 2 }}
            >
              Everything You Need for{" "}
              <Box
                component="span"
                sx={{
                  background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Intelligent Scheduling
              </Box>
            </Typography>
          </motion.div>
        </Box>

        {/* Bento Grid */}
        <Grid container spacing={3}>
          {/* Large Feature */}
          <Grid item xs={12} md={6}>
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              viewport={{ once: true }}
              style={{ height: "100%" }}
            >
              <Paper
                sx={{
                  height: "100%",
                  minHeight: { xs: 280, md: 350 },
                  p: { xs: 3, md: 4 },
                  background: features[0].gradient,
                  border: "1px solid rgba(99, 102, 241, 0.2)",
                  borderRadius: 3,
                  position: "relative",
                  overflow: "hidden",
                  transition: "all 0.3s ease",
                  "&:hover": {
                    transform: "translateY(-4px)",
                    borderColor: "rgba(99, 102, 241, 0.4)",
                    boxShadow: "0 20px 40px -20px rgba(99, 102, 241, 0.3)",
                  },
                }}
              >
                <Box sx={{ position: "relative", zIndex: 1 }}>
                  <Box
                    sx={{
                      width: 56,
                      height: 56,
                      borderRadius: 2,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      background: "rgba(99, 102, 241, 0.2)",
                      mb: 3,
                    }}
                  >
                    <Sparkles size={28} style={{ color: "#6366f1" }} />
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                    {features[0].title}
                  </Typography>
                  <Typography variant="body1" sx={{ color: "#94a3b8", maxWidth: 400 }}>
                    {features[0].description}
                  </Typography>
                </Box>
                {/* Decorative Element */}
                <Box
                  sx={{
                    position: "absolute",
                    bottom: -30,
                    right: -30,
                    width: 150,
                    height: 150,
                    background: "radial-gradient(circle, rgba(99, 102, 241, 0.3) 0%, transparent 70%)",
                    borderRadius: "50%",
                  }}
                />
              </Paper>
            </motion.div>
          </Grid>

          {/* Right Column */}
          <Grid item xs={12} md={6}>
            <Grid container spacing={3}>
              {features.slice(1, 3).map((feature, index) => (
                <Grid item xs={12} sm={6} md={12} key={index}>
                  <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: index * 0.1 }}
                    viewport={{ once: true }}
                  >
                    <Paper
                      sx={{
                        p: 3,
                        height: "100%",
                        background: feature.gradient,
                        border: "1px solid rgba(99, 102, 241, 0.1)",
                        borderRadius: 3,
                        transition: "all 0.3s ease",
                        "&:hover": {
                          transform: "translateY(-4px)",
                          borderColor: "rgba(99, 102, 241, 0.3)",
                        },
                      }}
                    >
                      <Box
                        sx={{
                          width: 44,
                          height: 44,
                          borderRadius: 1.5,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          background: "rgba(255, 255, 255, 0.05)",
                          mb: 2,
                        }}
                      >
                        <feature.icon size={22} style={{ color: "#6366f1" }} />
                      </Box>
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, fontSize: "1.1rem" }}>
                        {feature.title}
                      </Typography>
                      <Typography variant="body2" sx={{ color: "#94a3b8" }}>
                        {feature.description}
                      </Typography>
                    </Paper>
                  </motion.div>
                </Grid>
              ))}
            </Grid>
          </Grid>

          {/* Bottom Row */}
          {features.slice(3).map((feature, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Paper
                  sx={{
                    p: 3,
                    height: "100%",
                    background: feature.gradient,
                    border: "1px solid rgba(99, 102, 241, 0.1)",
                    borderRadius: 3,
                    transition: "all 0.3s ease",
                    "&:hover": {
                      transform: "translateY(-4px)",
                      borderColor: "rgba(99, 102, 241, 0.3)",
                    },
                  }}
                >
                  <Box
                    sx={{
                      width: 44,
                      height: 44,
                      borderRadius: 1.5,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      background: "rgba(255, 255, 255, 0.05)",
                      mb: 2,
                    }}
                  >
                    <feature.icon size={22} style={{ color: "#6366f1" }} />
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, fontSize: "1.1rem" }}>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" sx={{ color: "#94a3b8" }}>
                    {feature.description}
                  </Typography>
                </Paper>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
}
