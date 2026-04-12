"use client";

import { useEffect, useState } from "react";
import { Box, Paper, Typography, Button, Fade } from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, Calendar, Clock, Video, Mail, Sparkles } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";

interface SuccessCelebrationProps {
  isOpen: boolean;
  onClose: () => void;
  meetingDetails: {
    title: string;
    date: string;
    time: string;
    duration: number;
    attendee?: string;
    meetingUrl?: string;
  };
  onViewCalendar?: () => void;
}

export function SuccessCelebration({
  isOpen,
  onClose,
  meetingDetails,
  onViewCalendar,
}: SuccessCelebrationProps) {
  const { isDark } = useTheme();
  const [showConfetti, setShowConfetti] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setShowConfetti(true);
      const timer = setTimeout(() => setShowConfetti(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <Fade in={isOpen} timeout={300}>
        <Box
          sx={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            bgcolor: "rgba(0, 0, 0, 0.7)",
            zIndex: 1300,
            p: 2,
          }}
        >
          {/* Confetti Effect */}
          {showConfetti && (
            <Box
              sx={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                pointerEvents: "none",
                overflow: "hidden",
              }}
            >
              {Array.from({ length: 30 }).map((_, i) => (
                <motion.div
                  key={i}
                  initial={{
                    y: -20,
                    x: Math.random() * (typeof window !== "undefined" ? window.innerWidth : 1000),
                    rotate: 0,
                    opacity: 1,
                  }}
                  animate={{
                    y: typeof window !== "undefined" ? window.innerHeight : 800,
                    rotate: Math.random() * 360,
                    opacity: 0,
                  }}
                  transition={{
                    duration: 2 + Math.random() * 2,
                    ease: "easeOut",
                    delay: Math.random() * 0.5,
                  }}
                  style={{
                    position: "absolute",
                    width: 8 + Math.random() * 8,
                    height: 8 + Math.random() * 8,
                    borderRadius: Math.random() > 0.5 ? "50%" : "0%",
                    background: ["#6366f1", "#ec4899", "#10b981", "#f59e0b", "#8b5cf6"][
                      Math.floor(Math.random() * 5)
                    ],
                  }}
                />
              ))}
            </Box>
          )}

          <motion.div
            initial={{ scale: 0.8, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.8, opacity: 0, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
          >
            <Paper
              elevation={0}
              sx={{
                maxWidth: 480,
                width: "100%",
                p: { xs: 3, sm: 4 },
                textAlign: "center",
                background: isDark
                  ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                  : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
                border: "1px solid hsla(239, 84%, 67%, 0.2)",
                borderRadius: "20px",
                position: "relative",
                overflow: "hidden",
              }}
            >
              {/* Success Icon */}
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", damping: 20, stiffness: 300, delay: 0.1 }}
              >
                <Box
                  sx={{
                    width: 80,
                    height: 80,
                    borderRadius: "50%",
                    background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    mx: "auto",
                    mb: 3,
                    boxShadow: "0 10px 40px -10px rgba(16, 185, 129, 0.4)",
                  }}
                >
                  <CheckCircle2 size={40} color="white" />
                </Box>
              </motion.div>

              {/* Title */}
              <Typography
                variant="h4"
                sx={{
                  fontWeight: 700,
                  mb: 1,
                  color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                }}
              >
                Meeting Confirmed!
              </Typography>

              <Typography
                sx={{
                  color: isDark ? "hsl(215, 16%, 70%)" : "hsl(215, 16%, 47%)",
                  mb: 3,
                  fontSize: "1rem",
                }}
              >
                All set! Your meeting is locked in.
              </Typography>

              {/* Meeting Details Card */}
              <Paper
                elevation={0}
                sx={{
                  p: 3,
                  mb: 3,
                  background: isDark
                    ? "hsla(239, 84%, 67%, 0.1)"
                    : "hsla(239, 84%, 67%, 0.05)",
                  border: "1px solid hsla(239, 84%, 67%, 0.2)",
                  borderRadius: "12px",
                  textAlign: "left",
                }}
              >
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 600,
                    mb: 2,
                    color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                  }}
                >
                  {meetingDetails.title}
                </Typography>

                <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                    <Calendar size={18} color="hsl(239, 84%, 67%)" />
                    <Typography sx={{ color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)", fontSize: "0.9375rem" }}>
                      {meetingDetails.date}
                    </Typography>
                  </Box>

                  <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                    <Clock size={18} color="hsl(239, 84%, 67%)" />
                    <Typography sx={{ color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)", fontSize: "0.9375rem" }}>
                      {meetingDetails.time} • {meetingDetails.duration} minutes
                    </Typography>
                  </Box>

                  {meetingDetails.attendee && (
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                      <Mail size={18} color="hsl(239, 84%, 67%)" />
                      <Typography sx={{ color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)", fontSize: "0.9375rem" }}>
                        With: {meetingDetails.attendee}
                      </Typography>
                    </Box>
                  )}

                  {meetingDetails.meetingUrl && (
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                      <Video size={18} color="hsl(239, 84%, 67%)" />
                      <Typography sx={{ color: "hsl(239, 84%, 67%)", fontSize: "0.9375rem" }}>
                        Video link included
                      </Typography>
                    </Box>
                  )}
                </Box>
              </Paper>

              {/* Auto-Added Message */}
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 1,
                  mb: 3,
                  p: 2,
                  background: isDark
                    ? "hsla(142, 76%, 36%, 0.1)"
                    : "hsla(142, 76%, 36%, 0.05)",
                  borderRadius: "8px",
                }}
              >
                <Sparkles size={16} color="#10b981" />
                <Typography sx={{ color: "#10b981", fontSize: "0.875rem", fontWeight: 500 }}>
                  Calendar invite sent automatically
                </Typography>
              </Box>

              {/* Action Buttons */}
              <Box sx={{ display: "flex", gap: 2, flexDirection: { xs: "column", sm: "row" } }}>
                <Button
                  variant="contained"
                  fullWidth
                  onClick={onViewCalendar}
                  sx={{
                    background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                    textTransform: "none",
                    fontWeight: 600,
                    borderRadius: "10px",
                    py: 1.2,
                  }}
                >
                  View in Calendar
                </Button>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={onClose}
                  sx={{
                    textTransform: "none",
                    fontWeight: 600,
                    borderRadius: "10px",
                    borderColor: "hsla(239, 84%, 67%, 0.3)",
                    color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                    py: 1.2,
                  }}
                >
                  Book Another
                </Button>
              </Box>
            </Paper>
          </motion.div>
        </Box>
      </Fade>
    </AnimatePresence>
  );
}
