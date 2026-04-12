"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Box, Paper, Typography, Button, TextField, Stepper, Step, StepLabel, Grid, Chip } from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import { User, Calendar, Sparkles, Check, ArrowRight, ArrowLeft, Zap, Clock, Bell } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";
import { toast } from "@/components/ui/Toast";
import { AuthLayout } from "@/components/auth/AuthLayout";

const steps = ["Welcome", "Profile", "Preferences", "Complete"];

const timeZones = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Paris",
  "Asia/Tokyo",
  "Asia/Singapore",
  "Australia/Sydney",
];

export default function OnboardingPage() {
  const router = useRouter();
  const { isDark } = useTheme();

  const [activeStep, setActiveStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  // Form state
  const [name, setName] = useState("");
  const [timeZone, setTimeZone] = useState("UTC");
  const [workHours, setWorkHours] = useState({ start: "09:00", end: "17:00" });
  const [notifications, setNotifications] = useState(true);
  const [aiSuggestions, setAiSuggestions] = useState(true);

  const handleNext = () => {
    if (activeStep === 1 && !name.trim()) {
      toast.error("Please enter your name");
      return;
    }
    setActiveStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const handleComplete = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("/api/auth/onboarding", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          timezone: timeZone,
          work_hours_start: workHours.start,
          work_hours_end: workHours.end,
          notifications_enabled: notifications,
          ai_suggestions_enabled: aiSuggestions,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to complete onboarding");
      }

      toast.success("Welcome to GraftAI!");
      router.push("/dashboard");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Something went wrong. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout title="Welcome">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Stepper */}
        <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel
                sx={{
                  "& .MuiStepLabel-label": {
                    color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)",
                    fontSize: "0.75rem",
                  },
                  "& .Mui-active .MuiStepLabel-label": {
                    color: "hsl(239, 84%, 67%) !important",
                    fontWeight: 600,
                  },
                  "& .Mui-completed .MuiStepLabel-label": {
                    color: isDark ? "hsl(160, 84%, 39%)" : "hsl(160, 84%, 39%)",
                  },
                }}
              >
                {label}
              </StepLabel>
            </Step>
          ))}
        </Stepper>

        <Paper
          elevation={0}
          sx={{
            p: { xs: 3, md: 4 },
            background: isDark
              ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
              : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
            border: "1px solid hsla(239, 84%, 67%, 0.15)",
            borderRadius: "16px",
          }}
        >
          <AnimatePresence mode="wait">
            {activeStep === 0 && (
              <motion.div
                key="step0"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <Box sx={{ textAlign: "center", mb: 4 }}>
                  <Box
                    sx={{
                      width: 80,
                      height: 80,
                      borderRadius: "20px",
                      background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      margin: "0 auto 16px",
                      boxShadow: "0 10px 40px -10px hsla(239, 84%, 67%, 0.5)",
                    }}
                  >
                    <Sparkles size={40} color="white" />
                  </Box>

                  <Typography
                    variant="h4"
                    sx={{
                      fontWeight: 700,
                      color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                      mb: 2,
                    }}
                  >
                    Welcome to GraftAI
                  </Typography>

                  <Typography sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                    Your AI-powered scheduling assistant is ready to help you save time and stay organized.
                    Let's set up your account in just a few steps.
                  </Typography>
                </Box>

                <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mb: 4 }}>
                  {[
                    { icon: Zap, text: "Smart meeting scheduling" },
                    { icon: Clock, text: "Automatic availability detection" },
                    { icon: Bell, text: "Intelligent reminders" },
                  ].map((feature, i) => (
                    <Box
                      key={i}
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 2,
                        p: 2,
                        borderRadius: "10px",
                        background: isDark ? "hsla(239, 84%, 67%, 0.1)" : "hsla(239, 84%, 67%, 0.05)",
                      }}
                    >
                      <Box
                        sx={{
                          width: 36,
                          height: 36,
                          borderRadius: "8px",
                          background: "hsla(239, 84%, 67%, 0.2)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                        }}
                      >
                        <feature.icon size={18} style={{ color: "hsl(239, 84%, 67%)" }} />
                      </Box>
                      <Typography sx={{ color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }}>
                        {feature.text}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </motion.div>
            )}

            {activeStep === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <Box sx={{ textAlign: "center", mb: 4 }}>
                  <Box
                    sx={{
                      width: 64,
                      height: 64,
                      borderRadius: "16px",
                      background: "hsla(239, 84%, 67%, 0.15)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      margin: "0 auto 16px",
                      border: "1px solid hsla(239, 84%, 67%, 0.3)",
                    }}
                  >
                    <User size={28} style={{ color: "hsl(239, 84%, 67%)" }} />
                  </Box>

                  <Typography
                    variant="h5"
                    sx={{
                      fontWeight: 700,
                      color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                      mb: 1,
                    }}
                  >
                    Set up your profile
                  </Typography>

                  <Typography sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                    Tell us a bit about yourself so we can personalize your experience.
                  </Typography>
                </Box>

                <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
                  <TextField
                    fullWidth
                    label="Your Name"
                    placeholder="John Doe"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    sx={{
                      "& .MuiOutlinedInput-root": {
                        background: "transparent",
                        borderRadius: "10px",
                        color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                        "& fieldset": { borderColor: "hsla(239, 84%, 67%, 0.3)" },
                        "&:hover fieldset": { borderColor: "hsla(239, 84%, 67%, 0.5)" },
                        "&.Mui-focused fieldset": { borderColor: "hsl(239, 84%, 67%)" },
                      },
                      "& .MuiInputLabel-root": { color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" },
                    }}
                  />

                  <TextField
                    fullWidth
                    select
                    label="Time Zone"
                    value={timeZone}
                    onChange={(e) => setTimeZone(e.target.value)}
                    SelectProps={{ native: true, inputProps: { title: "Time Zone" } }}
                    sx={{
                      "& .MuiOutlinedInput-root": {
                        background: "transparent",
                        borderRadius: "10px",
                        color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                        "& fieldset": { borderColor: "hsla(239, 84%, 67%, 0.3)" },
                      },
                      "& .MuiInputLabel-root": { color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" },
                    }}
                  >
                    {timeZones.map((tz) => (
                      <option key={tz} value={tz}>
                        {tz}
                      </option>
                    ))}
                  </TextField>
                </Box>
              </motion.div>
            )}

            {activeStep === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <Box sx={{ textAlign: "center", mb: 4 }}>
                  <Box
                    sx={{
                      width: 64,
                      height: 64,
                      borderRadius: "16px",
                      background: "hsla(239, 84%, 67%, 0.15)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      margin: "0 auto 16px",
                      border: "1px solid hsla(239, 84%, 67%, 0.3)",
                    }}
                  >
                    <Calendar size={28} style={{ color: "hsl(239, 84%, 67%)" }} />
                  </Box>

                  <Typography
                    variant="h5"
                    sx={{
                      fontWeight: 700,
                      color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                      mb: 1,
                    }}
                  >
                    Your preferences
                  </Typography>

                  <Typography sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                    Configure how GraftAI works for you.
                  </Typography>
                </Box>

                <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
                  <Paper
                    elevation={0}
                    sx={{
                      p: 3,
                      background: isDark ? "hsla(239, 84%, 67%, 0.05)" : "hsla(239, 84%, 67%, 0.03)",
                      border: "1px solid hsla(239, 84%, 67%, 0.1)",
                      borderRadius: "12px",
                    }}
                  >
                    <Typography
                      sx={{ fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)", mb: 2 }}
                    >
                      Working Hours
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <TextField
                          fullWidth
                          type="time"
                          label="Start"
                          value={workHours.start}
                          onChange={(e) => setWorkHours((p) => ({ ...p, start: e.target.value }))}
                          sx={{
                            "& .MuiOutlinedInput-root": {
                              borderRadius: "10px",
                              "& fieldset": { borderColor: "hsla(239, 84%, 67%, 0.3)" },
                            },
                            "& .MuiInputLabel-root": { color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" },
                          }}
                        />
                      </Grid>
                      <Grid item xs={6}>
                        <TextField
                          fullWidth
                          type="time"
                          label="End"
                          value={workHours.end}
                          onChange={(e) => setWorkHours((p) => ({ ...p, end: e.target.value }))}
                          sx={{
                            "& .MuiOutlinedInput-root": {
                              borderRadius: "10px",
                              "& fieldset": { borderColor: "hsla(239, 84%, 67%, 0.3)" },
                            },
                            "& .MuiInputLabel-root": { color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" },
                          }}
                        />
                      </Grid>
                    </Grid>
                  </Paper>

                  <Paper
                    elevation={0}
                    onClick={() => setNotifications(!notifications)}
                    sx={{
                      p: 3,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      background: isDark ? "hsla(239, 84%, 67%, 0.05)" : "hsla(239, 84%, 67%, 0.03)",
                      border: "1px solid hsla(239, 84%, 67%, 0.1)",
                      borderRadius: "12px",
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                      "&:hover": {
                        borderColor: "hsla(239, 84%, 67%, 0.3)",
                      },
                    }}
                  >
                    <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                      <Box
                        sx={{
                          width: 40,
                          height: 40,
                          borderRadius: "10px",
                          background: "hsla(239, 84%, 67%, 0.15)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                        }}
                      >
                        <Bell size={20} style={{ color: "hsl(239, 84%, 67%)" }} />
                      </Box>
                      <Box>
                        <Typography sx={{ fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }}>
                          Notifications
                        </Typography>
                        <Typography sx={{ fontSize: "0.875rem", color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                          Get reminders about upcoming meetings
                        </Typography>
                      </Box>
                    </Box>
                    <Box
                      sx={{
                        width: 48,
                        height: 24,
                        borderRadius: "12px",
                        background: notifications ? "hsl(239, 84%, 67%)" : isDark ? "hsl(240, 24%, 25%)" : "hsl(220, 14%, 80%)",
                        position: "relative",
                        transition: "background 0.2s ease",
                        cursor: "pointer",
                      }}
                    >
                      <Box
                        sx={{
                          width: 20,
                          height: 20,
                          borderRadius: "50%",
                          background: "white",
                          position: "absolute",
                          top: 2,
                          left: notifications ? 26 : 2,
                          transition: "left 0.2s ease",
                        }}
                      />
                    </Box>
                  </Paper>

                  <Paper
                    elevation={0}
                    onClick={() => setAiSuggestions(!aiSuggestions)}
                    sx={{
                      p: 3,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      background: isDark ? "hsla(239, 84%, 67%, 0.05)" : "hsla(239, 84%, 67%, 0.03)",
                      border: "1px solid hsla(239, 84%, 67%, 0.1)",
                      borderRadius: "12px",
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                      "&:hover": {
                        borderColor: "hsla(239, 84%, 67%, 0.3)",
                      },
                    }}
                  >
                    <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                      <Box
                        sx={{
                          width: 40,
                          height: 40,
                          borderRadius: "10px",
                          background: "hsla(239, 84%, 67%, 0.15)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                        }}
                      >
                        <Sparkles size={20} style={{ color: "hsl(239, 84%, 67%)" }} />
                      </Box>
                      <Box>
                        <Typography sx={{ fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }}>
                          AI Suggestions
                        </Typography>
                        <Typography sx={{ fontSize: "0.875rem", color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                          Let AI optimize your schedule
                        </Typography>
                      </Box>
                    </Box>
                    <Box
                      sx={{
                        width: 48,
                        height: 24,
                        borderRadius: "12px",
                        background: aiSuggestions ? "hsl(239, 84%, 67%)" : isDark ? "hsl(240, 24%, 25%)" : "hsl(220, 14%, 80%)",
                        position: "relative",
                        transition: "background 0.2s ease",
                        cursor: "pointer",
                      }}
                    >
                      <Box
                        sx={{
                          width: 20,
                          height: 20,
                          borderRadius: "50%",
                          background: "white",
                          position: "absolute",
                          top: 2,
                          left: aiSuggestions ? 26 : 2,
                          transition: "left 0.2s ease",
                        }}
                      />
                    </Box>
                  </Paper>
                </Box>
              </motion.div>
            )}

            {activeStep === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <Box sx={{ textAlign: "center", mb: 4 }}>
                  <Box
                    sx={{
                      width: 80,
                      height: 80,
                      borderRadius: "20px",
                      background: "linear-gradient(135deg, hsl(160, 84%, 39%) 0%, hsl(160, 84%, 49%) 100%)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      margin: "0 auto 16px",
                      boxShadow: "0 10px 40px -10px hsla(160, 84%, 39%, 0.5)",
                    }}
                  >
                    <Check size={40} color="white" />
                  </Box>

                  <Typography
                    variant="h4"
                    sx={{
                      fontWeight: 700,
                      color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                      mb: 2,
                    }}
                  >
                    You're all set!
                  </Typography>

                  <Typography sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                    Your account is ready. Start exploring GraftAI and let us help you take control of your schedule.
                  </Typography>
                </Box>

                <Box sx={{ display: "flex", justifyContent: "center", mb: 4 }}>
                  <Chip
                    label="Setup Complete"
                    sx={{
                      background: "hsla(160, 84%, 39%, 0.15)",
                      color: "hsl(160, 84%, 39%)",
                      fontWeight: 600,
                      px: 2,
                    }}
                  />
                </Box>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Navigation Buttons */}
          <Box sx={{ display: "flex", justifyContent: "space-between", mt: 4 }}>
            <Button
              onClick={handleBack}
              disabled={activeStep === 0}
              startIcon={<ArrowLeft size={18} />}
              sx={{
                color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                textTransform: "none",
                fontWeight: 600,
                "&:disabled": {
                  color: isDark ? "hsl(215, 16%, 30%)" : "hsl(215, 16%, 70%)",
                },
              }}
            >
              Back
            </Button>

            {activeStep === steps.length - 1 ? (
              <Button
                onClick={handleComplete}
                disabled={isLoading}
                variant="contained"
                endIcon={<ArrowRight size={18} />}
                sx={{
                  background: "linear-gradient(135deg, hsl(160, 84%, 39%) 0%, hsl(160, 84%, 49%) 100%)",
                  color: "white",
                  fontWeight: 600,
                  borderRadius: "10px",
                  textTransform: "none",
                  px: 4,
                  py: 1.5,
                  "&:hover": {
                    background: "linear-gradient(135deg, hsl(160, 84%, 29%) 0%, hsl(160, 84%, 39%) 100%)",
                  },
                }}
              >
                {isLoading ? "Setting up..." : "Get Started"}
              </Button>
            ) : (
              <Button
                onClick={handleNext}
                variant="contained"
                endIcon={<ArrowRight size={18} />}
                sx={{
                  background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                  color: "white",
                  fontWeight: 600,
                  borderRadius: "10px",
                  textTransform: "none",
                  px: 4,
                  py: 1.5,
                  "&:hover": {
                    background: "linear-gradient(135deg, hsl(239, 84%, 57%) 0%, hsl(330, 81%, 50%) 100%)",
                  },
                }}
              >
                Continue
              </Button>
            )}
          </Box>
        </Paper>
      </motion.div>
    </AuthLayout>
  );
}
