"use client";

import { Box, Typography, Container, Grid, Stack } from "@mui/material";
import { motion } from "framer-motion";
import { 
  MessageSquareX, 
  Brain, 
  AlertTriangle, 
  Check, 
  ArrowRight,
  Database,
  Cpu,
  Activity
} from "lucide-react";

const painPoints = [
  {
    icon: MessageSquareX,
    pain: "8+ emails just to schedule one meeting",
    solution: "AI suggests 3 optimal times instantly",
    nodeId: "0xFC1",
  },
  {
    icon: Brain,
    pain: "Constant interruptions kill productivity",
    solution: "Auto-blocks deep work sessions",
    nodeId: "0xFC2",
  },
  {
    icon: AlertTriangle,
    pain: "Double-bookings and timezone confusion",
    solution: "Smart conflict detection across all calendars",
    nodeId: "0xFC3",
  },
];

export function ProblemSolution() {
  return (
    <Box id="features" sx={{ py: { xs: 10, md: 20 }, background: "var(--bg-base)" }}>
      <Container maxWidth="xl">
        {/* Section Header */}
        <Box sx={{ mb: { xs: 8, md: 12 } }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
          >
            <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
               <Database size={14} className="text-[var(--primary)]" />
               <Typography className="telemetry-text">[ CONFLICT_RESOLUTION_MODULE ]</Typography>
            </Stack>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: "2.25rem", sm: "3rem", md: "4rem" },
                fontWeight: 900,
                fontFamily: "var(--font-mono)",
                maxWidth: 900,
                lineHeight: 1,
                letterSpacing: "-0.05em",
                color: "var(--text-primary)",
                textTransform: "uppercase"
              }}
            >
              Terminate <Box component="span" sx={{ color: "var(--text-faint)" }}>Calendar</Box> Chaos.
            </Typography>
          </motion.div>
        </Box>

        {/* Pain Point Cards */}
        <Grid container spacing={4}>
          {painPoints.map((point, index) => (
            <Grid item xs={12} md={4} key={index}>
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
                    p: { xs: 4, md: 5 },
                    background: "var(--bg-base)",
                    border: "1px dashed var(--border-subtle)",
                    position: "relative",
                    overflow: "hidden",
                    transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                    "&:hover": {
                      borderColor: "var(--primary)",
                      background: "rgba(0, 255, 156, 0.03)",
                      "& .status-glow": { opacity: 1 }
                    },
                  }}
                >
                  {/* Status Indicator */}
                  <Box 
                    className="status-glow"
                    sx={{ 
                      position: "absolute", 
                      top: 0, 
                      left: 0, 
                      width: "100%", 
                      height: "2px", 
                      background: "var(--primary)",
                      opacity: 0,
                      transition: "opacity 0.3s",
                      boxShadow: "0 0 15px var(--primary)"
                    }} 
                  />

                  <Stack spacing={4}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Box sx={{ p: 1.5, border: "1px solid var(--border-subtle)", color: "var(--text-faint)" }}>
                        <point.icon size={20} />
                      </Box>
                      <Typography className="telemetry-text" sx={{ opacity: 0.5 }}>
                        NODE_{point.nodeId}
                      </Typography>
                    </Stack>

                    <Stack spacing={2}>
                      <Typography sx={{ color: "var(--text-faint)", fontSize: "10px", fontFamily: "var(--font-mono)", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.1em" }}>
                        // LEGACY_INPUT
                      </Typography>
                      <Typography sx={{ color: "var(--text-secondary)", fontSize: "14px", fontFamily: "var(--font-mono)", fontWeight: 700, fontStyle: "italic", textDecoration: "line-through", opacity: 0.6 }}>
                        "{point.pain}"
                      </Typography>
                    </Stack>

                    <Box sx={{ py: 1, px: 2, background: "var(--bg-elevated)", borderLeft: "2px solid var(--primary)" }}>
                       <Stack direction="row" spacing={1} alignItems="center">
                          <Activity size={12} className="text-[var(--primary)]" />
                          <Typography className="telemetry-text" sx={{ color: "var(--primary)" }}>REFINEMENT_COMPLETE</Typography>
                       </Stack>
                    </Box>

                    <Stack spacing={2}>
                      <Typography sx={{ color: "var(--primary)", fontSize: "11px", fontFamily: "var(--font-mono)", fontWeight: 900, textTransform: "uppercase", letterSpacing: "0.1em" }}>
                        // GRAFT_OUTPUT
                      </Typography>
                      <Typography sx={{ color: "var(--text-primary)", fontSize: "15px", fontFamily: "var(--font-mono)", fontWeight: 800, lineHeight: 1.5 }}>
                        {point.solution}
                      </Typography>
                    </Stack>
                  </Stack>

                  {/* Decorative Background PID */}
                  <Typography sx={{ position: "absolute", bottom: 20, right: 20, fontSize: "40px", fontFamily: "var(--font-mono)", fontWeight: 900, color: "rgba(255,255,255,0.02)", pointerEvents: "none" }}>
                    {point.nodeId}
                  </Typography>
                </Box>
              </motion.div>
            </Grid>
          ))}
        </Grid>

        <Box sx={{ mt: 12, p: 4, border: "1px dashed var(--border-subtle)", textAlign: "center" }}>
           <Typography className="telemetry-text">
             SYSTEM_STATUS: <Box component="span" sx={{ color: "var(--primary)" }}>AUTO_OPTIMIZATION_ENABLED</Box> // SCAN_MODE: CONTINUOUS
           </Typography>
        </Box>
      </Container>
    </Box>
  );
}
