"use client";

import { Box, Typography, Container, Stepper, Step, StepLabel, StepContent, Stack } from "@mui/material";
import { motion } from "framer-motion";
import { Link, Settings, Sparkles, Terminal, Activity, ShieldCheck, Database, Cpu } from "lucide-react";
import { useState } from "react";

const steps = [
  {
    icon: Link,
    title: "INIT_PROTOCOL: CALENDAR_SYNC",
    description: "Establish encrypted handshakes with Google, Microsoft, and Apple clusters. We pull real-time availability payloads across all endpoints to build your local schedule baseline.",
    footer: "PROTOCOL_STABLE: 256-BIT_AES",
    color: "var(--primary)",
  },
  {
    icon: Settings,
    title: "PARAM_CONFIG: USER_HEURISTICS",
    description: "Define neural parameters for deep-work windows, latency buffers, and priority tiers. Our AI agent parses your high-level intent into actionable schedule architecture.",
    footer: "PARAM_LOADED: MEMORY_OPTIMIZED",
    color: "#00E0FF", // Accent Cyan
  },
  {
    icon: Sparkles,
    title: "EXEC_SEQUENCE: REAL_TIME_OPTIM",
    description: "Activate background scheduling engine. Conflict resolution, smart-rerouting, and focus protection run in a background kernel—preserving your bandwidth while maximizing output.",
    footer: "STATUS: ACTIVE_NODE_SYNC",
    color: "var(--primary)",
  },
];

export function HowItWorks() {
  const [activeStep, setActiveStep] = useState(0);

  return (
    <Box id="how-it-works" sx={{ py: { xs: 10, md: 20 }, background: "var(--bg-base)" }}>
      <Container maxWidth="xl">
        {/* Header */}
        <Box sx={{ mb: { xs: 8, md: 12 } }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
          >
            <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
               <Database size={14} className="text-[var(--primary)]" />
               <Typography className="telemetry-text">[ SEQUENTIAL_INTEGRATION_FLOW_v1.0.4 ]</Typography>
            </Stack>
            <Typography
              variant="h2"
              sx={{ 
                fontSize: { xs: "2.5rem", sm: "3.5rem", md: "4.5rem" }, 
                fontWeight: 900, 
                fontFamily: "var(--font-mono)",
                letterSpacing: "-0.05em",
                color: "var(--text-primary)",
                textTransform: "uppercase",
                lineHeight: 1
              }}
            >
              System Deployment <Box component="span" sx={{ color: "var(--text-faint)" }}>In 60s</Box>.
            </Typography>
          </motion.div>
        </Box>

        {/* Steps */}
        <Box sx={{ maxWidth: 1000 }}>
          <Stepper 
            orientation="vertical" 
            activeStep={activeStep}
            connector={null}
            sx={{
              "& .MuiStep-root": { mb: 4 }
            }}
          >
            {steps.map((step, index) => (
              <Step key={index} expanded>
                <StepLabel
                  onClick={() => setActiveStep(index)}
                  sx={{
                    cursor: "pointer",
                    padding: 0,
                    "& .MuiStepLabel-iconContainer": { padding: 0 },
                    "& .MuiStepLabel-label": {
                       display: "flex",
                       alignItems: "center",
                       gap: 3,
                       color: activeStep === index ? "var(--primary)" : "var(--text-faint)",
                       fontSize: { xs: "14px", md: "18px" },
                       fontWeight: 900,
                       fontFamily: "var(--font-mono)",
                       textTransform: "uppercase",
                       letterSpacing: "0.1em",
                       transition: "color 0.3s"
                    },
                  }}
                  StepIconComponent={() => (
                    <Box 
                      sx={{ 
                        width: 50, 
                        height: 50, 
                        display: "flex", 
                        alignItems: "center", 
                        justifyContent: "center",
                        border: `1px solid ${activeStep === index ? step.color : "var(--border-subtle)"}`,
                        background: activeStep === index ? "rgba(0,0,0,0.5)" : "transparent",
                        transition: "all 0.3s"
                      }}
                    >
                      <step.icon size={20} style={{ color: activeStep >= index ? step.color : "var(--text-faint)" }} />
                    </Box>
                  )}
                >
                  {step.title}
                </StepLabel>
                <StepContent sx={{ borderLeft: "1px dashed var(--border-subtle)", ml: "25px", pl: 6, py: 4 }}>
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.4 }}
                  >
                    <Box
                      sx={{
                        p: { xs: 3, md: 5 },
                        background: "rgba(255, 255, 255, 0.01)",
                        border: `1px dashed var(--border-subtle)`,
                        position: "relative",
                        "&:hover": { borderColor: step.color }
                      }}
                    >
                      <Typography 
                        sx={{ 
                          color: "var(--text-secondary)", 
                          mb: 4, 
                          lineHeight: 1.8,
                          fontSize: "14px",
                          fontFamily: "var(--font-mono)",
                          maxWidth: 700
                        }}
                      >
                        {step.description}
                      </Typography>
                      
                      <Stack direction="row" spacing={4} sx={{ borderTop: "1px dashed var(--border-subtle)", pt: 3 }}>
                        <Stack direction="row" spacing={1} alignItems="center" sx={{ color: step.color }}>
                          <Activity size={14} />
                          <Typography sx={{ fontWeight: 800, fontSize: "10px", fontFamily: "var(--font-mono)", textTransform: "uppercase" }}>
                            {step.footer}
                          </Typography>
                        </Stack>
                        <Stack direction="row" spacing={1} alignItems="center" sx={{ color: "var(--text-faint)" }}>
                          <ShieldCheck size={14} />
                          <Typography sx={{ fontSize: "10px", fontFamily: "var(--font-mono)", textTransform: "uppercase" }}>
                            ENCRYPTED_ENDPOINT
                          </Typography>
                        </Stack>
                      </Stack>
                    </Box>
                  </motion.div>
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </Box>

        <Box sx={{ mt: 10, display: "flex", alignItems: "center", gap: 2 }}>
           <Cpu size={16} className="text-[var(--text-faint)]" />
           <Typography className="telemetry-text" sx={{ color: "var(--text-faint)" }}>
             SYSTEM_STABILITY: 100% // ALL_STREAMS_ACTIVE
           </Typography>
        </Box>
      </Container>
    </Box>
  );
}
