"use client";

import { Box, Typography, Container, Paper, Grid } from "@mui/material";
import { motion } from "framer-motion";
import { Check, X, Sparkles } from "lucide-react";

const features = [
  { name: "AI-Powered Scheduling", graftai: true, calendly: false, reclaim: true, motion: true },
  { name: "Natural Language Input", graftai: true, calendly: false, reclaim: false, motion: false },
  { name: "Focus Time Protection", graftai: true, calendly: false, reclaim: true, motion: true },
  { name: "Cross-Platform Sync", graftai: true, calendly: true, reclaim: true, motion: true },
  { name: "Team Coordination", graftai: true, calendly: true, reclaim: true, motion: true },
  { name: "Meeting Analytics", graftai: true, calendly: false, reclaim: true, motion: false },
  { name: "Custom Workflows", graftai: true, calendly: false, reclaim: false, motion: false },
  { name: "API Access (Free)", graftai: true, calendly: false, reclaim: false, motion: false },
  { name: "White-label Options", graftai: true, calendly: true, reclaim: false, motion: false },
  { name: "Starting Price", graftai: "$0", calendly: "$0", reclaim: "$0", motion: "$0" },
  { name: "Pro Plan", graftai: "$19/mo", calendly: "$12/mo", reclaim: "$15/mo", motion: "$19/mo" },
];

export function Comparison() {
  return (
    <Box sx={{ py: { xs: 10, md: 16 }, background: "rgba(26, 26, 46, 0.3)" }}>
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
              Why Choose{" "}
              <Box
                component="span"
                sx={{
                  background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                GraftAI
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
              See how we stack up against the competition
            </Typography>
          </motion.div>
        </Box>

        {/* Comparison Table */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          viewport={{ once: true }}
        >
          <Paper
            sx={{
              background: "linear-gradient(135deg, rgba(26, 26, 46, 0.9) 0%, rgba(15, 15, 26, 0.95) 100%)",
              border: "1px solid rgba(99, 102, 241, 0.2)",
              borderRadius: 3,
              overflow: "hidden",
            }}
          >
            {/* Header Row */}
            <Grid container sx={{ borderBottom: "1px solid rgba(99, 102, 241, 0.1)" }}>
              <Grid item xs={4} md={3} sx={{ p: 2 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: "#64748b" }}>
                  Feature
                </Typography>
              </Grid>
              <Grid item xs={2} md={2} sx={{ p: 2, textAlign: "center", background: "rgba(99, 102, 241, 0.1)" }}>
                <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 0.5 }}>
                  <Sparkles size={16} style={{ color: "#6366f1" }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, color: "#6366f1" }}>
                    GraftAI
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={2} md={2} sx={{ p: 2, textAlign: "center" }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: "#94a3b8" }}>
                  Calendly
                </Typography>
              </Grid>
              <Grid item xs={2} md={2} sx={{ p: 2, textAlign: "center" }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: "#94a3b8" }}>
                  Reclaim
                </Typography>
              </Grid>
              <Grid item xs={2} md={2} sx={{ p: 2, textAlign: "center" }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: "#94a3b8" }}>
                  Motion
                </Typography>
              </Grid>
            </Grid>

            {/* Feature Rows */}
            {features.map((feature, index) => (
              <Grid
                key={feature.name}
                container
                sx={{
                  borderBottom: index < features.length - 1 ? "1px solid rgba(99, 102, 241, 0.05)" : "none",
                  "&:hover": { background: "rgba(99, 102, 241, 0.03)" },
                }}
              >
                <Grid item xs={4} md={3} sx={{ p: 2 }}>
                  <Typography variant="body2" sx={{ color: "#e2e8f0", fontWeight: 500 }}>
                    {feature.name}
                  </Typography>
                </Grid>
                <Grid
                  item
                  xs={2}
                  md={2}
                  sx={{ p: 2, textAlign: "center", background: "rgba(99, 102, 241, 0.05)" }}
                >
                  {typeof feature.graftai === "boolean" ? (
                    feature.graftai ? (
                      <Check size={20} style={{ color: "#10b981", margin: "0 auto" }} />
                    ) : (
                      <X size={20} style={{ color: "#64748b", margin: "0 auto" }} />
                    )
                  ) : (
                    <Typography variant="body2" sx={{ color: "#6366f1", fontWeight: 600 }}>
                      {feature.graftai}
                    </Typography>
                  )}
                </Grid>
                <Grid item xs={2} md={2} sx={{ p: 2, textAlign: "center" }}>
                  {typeof feature.calendly === "boolean" ? (
                    feature.calendly ? (
                      <Check size={20} style={{ color: "#10b981", margin: "0 auto" }} />
                    ) : (
                      <X size={20} style={{ color: "#64748b", margin: "0 auto" }} />
                    )
                  ) : (
                    <Typography variant="body2" sx={{ color: "#94a3b8" }}>
                      {feature.calendly}
                    </Typography>
                  )}
                </Grid>
                <Grid item xs={2} md={2} sx={{ p: 2, textAlign: "center" }}>
                  {typeof feature.reclaim === "boolean" ? (
                    feature.reclaim ? (
                      <Check size={20} style={{ color: "#10b981", margin: "0 auto" }} />
                    ) : (
                      <X size={20} style={{ color: "#64748b", margin: "0 auto" }} />
                    )
                  ) : (
                    <Typography variant="body2" sx={{ color: "#94a3b8" }}>
                      {feature.reclaim}
                    </Typography>
                  )}
                </Grid>
                <Grid item xs={2} md={2} sx={{ p: 2, textAlign: "center" }}>
                  {typeof feature.motion === "boolean" ? (
                    feature.motion ? (
                      <Check size={20} style={{ color: "#10b981", margin: "0 auto" }} />
                    ) : (
                      <X size={20} style={{ color: "#64748b", margin: "0 auto" }} />
                    )
                  ) : (
                    <Typography variant="body2" sx={{ color: "#94a3b8" }}>
                      {feature.motion}
                    </Typography>
                  )}
                </Grid>
              </Grid>
            ))}
          </Paper>
        </motion.div>
      </Container>
    </Box>
  );
}
