"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Box, Typography, Container, TextField, InputAdornment } from "@mui/material";
import { motion } from "framer-motion";
import { ArrowRight, Mail, Sparkles } from "lucide-react";
import { GradientButton } from "@/components/ui/GradientButton";

interface CTASectionProps {
  variant?: "email" | "buttons";
}

export function CTASection({ variant = "buttons" }: CTASectionProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState<string | null>(null);

  const handleGetStarted = () => {
    const trimmedEmail = email.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!trimmedEmail) {
      setEmailError("Please enter your email address.");
      return;
    }

    if (!emailRegex.test(trimmedEmail)) {
      setEmailError("Please enter a valid email address.");
      return;
    }

    setEmailError(null);
    router.push(`/register?email=${encodeURIComponent(trimmedEmail)}`);
  };

  if (variant === "email") {
    return (
      <Box sx={{ py: { xs: 10, md: 14 }, background: "rgba(15, 15, 26, 0.8)" }}>
        <Container maxWidth="md">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <Box sx={{ textAlign: "center" }}>
              <Typography
                variant="h3"
                sx={{ fontWeight: 700, mb: 2, fontSize: { xs: "1.5rem", md: "2.5rem" } }}
              >
                Ready to save{" "}
                <Box
                  component="span"
                  sx={{
                    background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                  }}
                >
                  5+ hours
                </Box>{" "}
                every week?
              </Typography>
              <Typography variant="body1" sx={{ color: "#94a3b8", mb: 4, maxWidth: 500, mx: "auto" }}>
                Join thousands of professionals who transformed their scheduling with GraftAI.
              </Typography>

              <Box
                sx={{
                  display: "flex",
                  flexDirection: { xs: "column", sm: "row" },
                  gap: 2,
                  maxWidth: 500,
                  mx: "auto",
                }}
              >
                <TextField
                  placeholder="Enter your email"
                  fullWidth
                  value={email}
                  onChange={(event) => {
                    setEmail(event.target.value);
                    if (emailError) setEmailError(null);
                  }}
                  error={Boolean(emailError)}
                  helperText={emailError || ""}
                  sx={{
                    "& .MuiOutlinedInput-root": {
                      background: "rgba(26, 26, 46, 0.8)",
                      borderRadius: "12px",
                      border: "1px solid rgba(99, 102, 241, 0.2)",
                      color: "#f8fafc",
                      "& fieldset": { border: "none" },
                      "&:hover": { borderColor: "rgba(99, 102, 241, 0.4)" },
                      "&.Mui-focused": { borderColor: "#6366f1" },
                    },
                    "& .MuiInputBase-input::placeholder": { color: "#64748b" },
                  }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Mail size={20} style={{ color: "#64748b" }} />
                      </InputAdornment>
                    ),
                  }}
                />
                <GradientButton
                  onClick={handleGetStarted}
                  gradientVariant="primary"
                  size="large"
                  sx={{ minWidth: { sm: 180 }, whiteSpace: "nowrap" }}
                >
                  Get Started
                  <ArrowRight size={18} style={{ marginLeft: 8 }} />
                </GradientButton>
              </Box>
            </Box>
          </motion.div>
        </Container>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        py: { xs: 12, md: 20 },
        background: "linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(236, 72, 153, 0.1) 100%)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Decorative Elements */}
      <Box
        sx={{
          position: "absolute",
          top: "-20%",
          left: "-10%",
          width: { xs: 200, md: 400 },
          height: { xs: 200, md: 400 },
          background: "radial-gradient(circle, rgba(99,102,241,0.2) 0%, transparent 70%)",
          borderRadius: "50%",
        }}
      />
      <Box
        sx={{
          position: "absolute",
          bottom: "-20%",
          right: "-10%",
          width: { xs: 200, md: 400 },
          height: { xs: 200, md: 400 },
          background: "radial-gradient(circle, rgba(236,72,153,0.15) 0%, transparent 70%)",
          borderRadius: "50%",
        }}
      />

      <Container maxWidth="lg" sx={{ position: "relative", zIndex: 1 }}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
        >
          <Box sx={{ textAlign: "center", maxWidth: 700, mx: "auto" }}>
            <Box
              sx={{
                display: "inline-flex",
                alignItems: "center",
                gap: 1,
                px: 3,
                py: 1,
                background: "rgba(99, 102, 241, 0.1)",
                border: "1px solid rgba(99, 102, 241, 0.2)",
                borderRadius: 10,
                mb: 4,
              }}
            >
              <Sparkles size={18} style={{ color: "#6366f1" }} />
              <Typography variant="body2" sx={{ color: "#a5b4fc", fontWeight: 500 }}>
                Start your free 14-day trial today
              </Typography>
            </Box>

            <Typography
              variant="h2"
              sx={{
                fontWeight: 800,
                mb: 3,
                fontSize: { xs: "2rem", sm: "2.5rem", md: "3.5rem" },
              }}
            >
              Transform Your{" "}
              <Box
                component="span"
                sx={{
                  background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Scheduling Today
              </Box>
            </Typography>

            <Typography variant="body1" sx={{ color: "#94a3b8", mb: 6, fontSize: "1.125rem" }}>
              Join thousands of professionals who save hours every week with GraftAI's
              AI-powered scheduling.
            </Typography>

            <Box
              sx={{
                display: "flex",
                flexDirection: { xs: "column", sm: "row" },
                gap: 3,
                justifyContent: "center",
              }}
            >
              <GradientButton
                component={Link}
                href="/register"
                gradientVariant="primary"
                size="large"
                sx={{ minWidth: 200 }}
              >
                Start Free Trial
                <ArrowRight size={20} style={{ marginLeft: 8 }} />
              </GradientButton>
              <GradientButton
                component={Link}
                href="/contact"
                gradientVariant="outline"
                size="large"
                sx={{ minWidth: 180 }}
              >
                Talk to Sales
              </GradientButton>
            </Box>
          </Box>
        </motion.div>
      </Container>
    </Box>
  );
}
