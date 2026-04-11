"use client";

import { Box, Typography, Container, Stepper, Step, StepLabel, StepContent, Paper } from "@mui/material";
import { motion } from "framer-motion";
import { Link, Settings, Sparkles, CheckCircle } from "lucide-react";
import { useState } from "react";

const steps = [
  {
    icon: Link,
    title: "Connect Your Calendars",
    description: "One-click integration with Google Calendar, Outlook, Apple Calendar, and more. We sync everything in real-time.",
    color: "#6366f1",
  },
  {
    icon: Settings,
    title: "Set Your Preferences",
    description: "Tell us your ideal meeting times, focus hours, and break preferences. The AI learns from every choice you make.",
    color: "#ec4899",
  },
  {
    icon: Sparkles,
    title: "Let AI Handle the Rest",
    description: "Auto-scheduling, conflict resolution, smart reminders, and focus time protection—all working in the background.",
    color: "#10b981",
  },
];

export function HowItWorks() {
  const [activeStep, setActiveStep] = useState(0);

  return (
    <Box id="how-it-works" sx={{ py: { xs: 10, md: 16 }, background: "rgba(26, 26, 46, 0.3)" }}>
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
              Get Started in{" "}
              <Box
                component="span"
                sx={{
                  background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                60 Seconds
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
              Three simple steps to transform your scheduling forever
            </Typography>
          </motion.div>
        </Box>

        {/* Steps */}
        <Box sx={{ maxWidth: 800, mx: "auto" }}>
          <Stepper 
            orientation="vertical" 
            activeStep={activeStep}
            sx={{
              "& .MuiStepConnector-root": {
                ml: 2.5,
                borderLeft: "2px solid rgba(99, 102, 241, 0.2)",
              },
              "& .MuiStepConnector-active, & .MuiStepConnector-completed": {
                borderColor: "#6366f1",
              },
            }}
          >
            {steps.map((step, index) => (
              <Step key={index}>
                <StepLabel
                  onClick={() => setActiveStep(index)}
                  sx={{
                    cursor: "pointer",
                    "& .MuiStepLabel-iconContainer": {
                      bgcolor: activeStep === index ? step.color : "rgba(99, 102, 241, 0.1)",
                      borderRadius: "50%",
                      width: 48,
                      height: 48,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      border: `2px solid ${activeStep >= index ? step.color : "rgba(99, 102, 241, 0.2)"}`,
                      transition: "all 0.3s ease",
                    },
                    "& .MuiStepLabel-label": {
                      color: activeStep === index ? "#f8fafc" : "#94a3b8",
                      fontSize: "1.25rem",
                      fontWeight: 600,
                    },
                  }}
                  StepIconComponent={() => (
                    <step.icon size={24} style={{ color: activeStep >= index ? "white" : "#94a3b8" }} />
                  )}
                >
                  {step.title}
                </StepLabel>
                <StepContent>
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <Paper
                      sx={{
                        p: 3,
                        background: "rgba(15, 15, 26, 0.8)",
                        border: `1px solid ${step.color}40`,
                        borderRadius: 2,
                        mb: 2,
                      }}
                    >
                      <Typography variant="body1" sx={{ color: "#94a3b8", mb: 2 }}>
                        {step.description}
                      </Typography>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1, color: step.color }}>
                        <CheckCircle size={18} />
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {index === 0 ? "Syncs in real-time" : index === 1 ? "Learns continuously" : "Works 24/7"}
                        </Typography>
                      </Box>
                    </Paper>
                  </motion.div>
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </Box>
      </Container>
    </Box>
  );
}
