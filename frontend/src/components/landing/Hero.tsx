"use client";

import { Box, Typography, Container, Chip, Stack } from "@mui/material";
import { motion } from "framer-motion";
import Link from "next/link";
import { 
  Sparkles, 
  ArrowRight, 
  Play, 
  Star, 
  Shield, 
  Zap,
  Calendar
} from "lucide-react";
import { GradientButton } from "@/components/ui/GradientButton";

export function Hero() {
  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        position: "relative",
        overflow: "hidden",
        pt: { xs: 10, md: 0 },
        background: "linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #0f0f1a 100%)",
      }}
    >
      {/* Background Gradient Orbs */}
      <Box
        sx={{
          position: "absolute",
          top: "10%",
          right: "-10%",
          width: { xs: 300, md: 600 },
          height: { xs: 300, md: 600 },
          background: "radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%)",
          borderRadius: "50%",
          filter: "blur(60px)",
        }}
      />
      <Box
        sx={{
          position: "absolute",
          bottom: "10%",
          left: "-10%",
          width: { xs: 250, md: 500 },
          height: { xs: 250, md: 500 },
          background: "radial-gradient(circle, rgba(236,72,153,0.1) 0%, transparent 70%)",
          borderRadius: "50%",
          filter: "blur(60px)",
        }}
      />

      <Container maxWidth="lg" sx={{ position: "relative", zIndex: 1 }}>
        <Box
          sx={{
            display: "flex",
            flexDirection: { xs: "column", md: "row" },
            alignItems: "center",
            gap: { xs: 6, md: 8 },
            py: { xs: 8, md: 12 },
          }}
        >
          {/* Left Content */}
          <Box sx={{ flex: 1, textAlign: { xs: "center", md: "left" }, maxWidth: { md: "600px" } }}>
            {/* Trust Badge */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <Chip
                icon={<Sparkles size={16} />}
                label="Trusted by 50,000+ professionals"
                sx={{
                  mb: 3,
                  background: "linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(236, 72, 153, 0.2))",
                  color: "#a5b4fc",
                  border: "1px solid rgba(99, 102, 241, 0.3)",
                  fontWeight: 500,
                  py: 0.5,
                  px: 1,
                }}
              />
            </motion.div>

            {/* Headline */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
            >
              <Typography
                variant="h1"
                sx={{
                  fontSize: { xs: "2.5rem", sm: "3rem", md: "3.75rem" },
                  fontWeight: 800,
                  lineHeight: 1.1,
                  mb: 3,
                  letterSpacing: "-0.02em",
                }}
              >
                AI Scheduling That{" "}
                <Box
                  component="span"
                  sx={{
                    background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                  }}
                >
                  Thinks Like You
                </Box>
              </Typography>
            </motion.div>

            {/* Subheadline */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <Typography
                variant="h5"
                sx={{
                  color: "#94a3b8",
                  fontSize: { xs: "1.1rem", md: "1.35rem" },
                  lineHeight: 1.6,
                  mb: 4,
                  maxWidth: { xs: "100%", md: "90%" },
                }}
              >
                GraftAI learns your preferences, finds optimal meeting times, 
                and protects your focus time—all automatically.
              </Typography>
            </motion.div>

            {/* CTA Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <Stack
                direction={{ xs: "column", sm: "row" }}
                spacing={2}
                sx={{ 
                  mb: 4,
                  justifyContent: { xs: "center", md: "flex-start" }
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
                  gradientVariant="outline"
                  size="large"
                  sx={{ minWidth: 180 }}
                  onClick={() => {
                    // TODO: open demo modal or navigate to live demo route when available
                    alert("Demo coming soon!");
                  }}
                >
                  <Play size={18} style={{ marginRight: 8 }} />
                  Watch Demo
                </GradientButton>
              </Stack>
            </motion.div>

            {/* Trust Indicators */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <Stack
                direction={{ xs: "column", sm: "row" }}
                spacing={3}
                sx={{
                  color: "#64748b",
                  fontSize: "0.875rem",
                  justifyContent: { xs: "center", md: "flex-start" },
                  alignItems: "center",
                }}
              >
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                  <Shield size={16} />
                  <span>No credit card required</span>
                </Box>
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                  <Zap size={16} />
                  <span>Setup in 60 seconds</span>
                </Box>
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                  <Star size={16} style={{ color: "#fbbf24" }} />
                  <span>4.9/5 from 2,000+ reviews</span>
                </Box>
              </Stack>
            </motion.div>
          </Box>

          {/* Right Content - Product Demo */}
          <Box
            sx={{
              flex: 1,
              display: { xs: "none", md: "flex" },
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <motion.div
              initial={{ opacity: 0, x: 50, rotateY: 15 }}
              animate={{ opacity: 1, x: 0, rotateY: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              style={{ perspective: 1000 }}
            >
              <Box
                sx={{
                  position: "relative",
                  width: 500,
                  height: 400,
                }}
              >
                {/* Main Dashboard Card */}
                <Box
                  sx={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    height: "100%",
                    background: "linear-gradient(135deg, rgba(26, 26, 46, 0.9) 0%, rgba(15, 15, 26, 0.95) 100%)",
                    borderRadius: 4,
                    border: "1px solid rgba(99, 102, 241, 0.2)",
                    boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 40px rgba(99, 102, 241, 0.1)",
                    overflow: "hidden",
                    transform: "rotateY(-5deg) rotateX(5deg)",
                  }}
                >
                  {/* Fake Browser Header */}
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      px: 2,
                      py: 1.5,
                      borderBottom: "1px solid rgba(99, 102, 241, 0.1)",
                      background: "rgba(15, 15, 26, 0.5)",
                    }}
                  >
                    <Box sx={{ display: "flex", gap: 0.5 }}>
                      <Box sx={{ width: 12, height: 12, borderRadius: "50%", background: "#ef4444" }} />
                      <Box sx={{ width: 12, height: 12, borderRadius: "50%", background: "#f59e0b" }} />
                      <Box sx={{ width: 12, height: 12, borderRadius: "50%", background: "#10b981" }} />
                    </Box>
                    <Box
                      sx={{
                        flex: 1,
                        mx: 2,
                        py: 0.5,
                        px: 2,
                        background: "rgba(99, 102, 241, 0.1)",
                        borderRadius: 1,
                        fontSize: "0.75rem",
                        color: "#64748b",
                        textAlign: "center",
                      }}
                    >
                      graftai.tech/dashboard
                    </Box>
                  </Box>

                  {/* Fake Dashboard Content */}
                  <Box sx={{ p: 3 }}>
                    <Box sx={{ display: "flex", gap: 2, mb: 3 }}>
                      <Box sx={{ flex: 1, height: 80, background: "rgba(99, 102, 241, 0.1)", borderRadius: 2 }} />
                      <Box sx={{ flex: 1, height: 80, background: "rgba(236, 72, 153, 0.1)", borderRadius: 2 }} />
                      <Box sx={{ flex: 1, height: 80, background: "rgba(16, 185, 129, 0.1)", borderRadius: 2 }} />
                    </Box>
                    <Box sx={{ height: 200, background: "rgba(99, 102, 241, 0.05)", borderRadius: 2, mb: 2 }} />
                  </Box>
                </Box>

                {/* Floating Elements */}
                <motion.div
                  animate={{ y: [0, -10, 0] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                  style={{
                    position: "absolute",
                    top: 60,
                    right: -30,
                    background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                    padding: "12px 16px",
                    borderRadius: 12,
                    boxShadow: "0 10px 30px rgba(99, 102, 241, 0.3)",
                  }}
                >
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Calendar size={20} color="white" />
                    <Typography sx={{ color: "white", fontWeight: 600, fontSize: "0.875rem" }}>
                      AI Optimized
                    </Typography>
                  </Box>
                </motion.div>

                <motion.div
                  animate={{ y: [0, 10, 0] }}
                  transition={{ duration: 3, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                  style={{
                    position: "absolute",
                    bottom: 40,
                    left: -20,
                    background: "rgba(26, 26, 46, 0.95)",
                    padding: "12px 16px",
                    borderRadius: 12,
                    border: "1px solid rgba(99, 102, 241, 0.3)",
                  }}
                >
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Sparkles size={18} style={{ color: "#6366f1" }} />
                    <Typography sx={{ color: "#f8fafc", fontWeight: 500, fontSize: "0.875rem" }}>
                      Focus Time Protected
                    </Typography>
                  </Box>
                </motion.div>
              </Box>
            </motion.div>
          </Box>
        </Box>
      </Container>
    </Box>
  );
}
