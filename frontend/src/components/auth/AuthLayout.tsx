"use client";

import { Box, useMediaQuery, useTheme } from "@mui/material";
import { motion } from "framer-motion";
import { ReactNode } from "react";
import { Sparkles } from "lucide-react";
import Link from "next/link";

interface AuthLayoutProps {
  children: ReactNode;
  title: string;
  subtitle?: string;
}

export function AuthLayout({ children, title, subtitle }: AuthLayoutProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        background: "hsl(240, 24%, 7%)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Animated Background Gradient */}
      <Box
        sx={{
          position: "absolute",
          inset: 0,
          background: `
            radial-gradient(ellipse at 20% 20%, hsla(239, 84%, 67%, 0.15) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 80%, hsla(330, 81%, 60%, 0.1) 0%, transparent 50%)
          `,
        }}
      />

      {/* Left Side - Visual Showcase (hidden on mobile) */}
      {!isMobile && (
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            padding: 48,
            background: "linear-gradient(135deg, hsla(239, 84%, 67%, 0.1) 0%, hsla(330, 81%, 60%, 0.05) 100%)",
            borderRight: "1px solid hsla(239, 84%, 67%, 0.1)",
            position: "relative",
          }}
        >
          {/* Decorative Elements */}
          <motion.div
            animate={{
              y: [0, -20, 0],
              rotate: [0, 5, 0],
            }}
            transition={{
              duration: 6,
              repeat: Infinity,
              ease: "easeInOut",
            }}
            style={{
              width: 300,
              height: 300,
              borderRadius: 30,
              background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
              opacity: 0.3,
              filter: "blur(60px)",
              position: "absolute",
            }}
          />

          <Box sx={{ position: "relative", zIndex: 1, textAlign: "center" }}>
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.5 }}
            >
              <Box
                sx={{
                  width: 80,
                  height: 80,
                  borderRadius: 3,
                  background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  mx: "auto",
                  mb: 4,
                  boxShadow: "0 20px 40px hsla(239, 84%, 67%, 0.4)",
                }}
              >
                <Sparkles size={40} color="white" />
              </Box>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.5 }}
            >
              <Box
                component="h1"
                sx={{
                  fontSize: "2.5rem",
                  fontWeight: 800,
                  background: "linear-gradient(135deg, hsl(220, 20%, 98%) 0%, hsl(215, 16%, 70%) 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  mb: 2,
                  letterSpacing: "-0.02em",
                }}
              >
                Welcome to GraftAI
              </Box>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.5 }}
            >
              <Box
                component="p"
                sx={{
                  color: "hsl(215, 16%, 55%)",
                  fontSize: "1.125rem",
                  maxWidth: 400,
                  lineHeight: 1.6,
                }}
              >
                AI-powered scheduling that transforms how you manage your time and meetings.
              </Box>
            </motion.div>

            {/* Feature Pills */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8, duration: 0.5 }}
              style={{
                display: "flex",
                gap: 12,
                justifyContent: "center",
                marginTop: 40,
                flexWrap: "wrap",
              }}
            >
              {["AI Scheduling", "Smart Sync", "Team Coordination"].map((feature, i) => (
                <Box
                  key={feature}
                  sx={{
                    px: 3,
                    py: 1.5,
                    background: "hsla(239, 84%, 67%, 0.1)",
                    border: "1px solid hsla(239, 84%, 67%, 0.2)",
                    borderRadius: 10,
                    color: "hsl(215, 16%, 70%)",
                    fontSize: "0.875rem",
                    fontWeight: 500,
                  }}
                >
                  {feature}
                </Box>
              ))}
            </motion.div>
          </Box>
        </motion.div>
      )}

      {/* Right Side - Form */}
      <Box
        sx={{
          flex: isMobile ? 1 : 0.6,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          p: { xs: 3, sm: 4, md: 6 },
          position: "relative",
          zIndex: 1,
        }}
      >
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          style={{ width: "100%", maxWidth: 420 }}
        >
          {/* Mobile Logo */}
          {isMobile && (
            <Box sx={{ textAlign: "center", mb: 4 }}>
              <Box
                sx={{
                  width: 56,
                  height: 56,
                  borderRadius: 2,
                  background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  mx: "auto",
                  mb: 2,
                }}
              >
                <Sparkles size={28} color="white" />
              </Box>
              <Box
                component="h1"
                sx={{
                  fontSize: "1.5rem",
                  fontWeight: 700,
                  background: "linear-gradient(135deg, hsl(220, 20%, 98%) 0%, hsl(215, 16%, 70%) 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                GraftAI
              </Box>
            </Box>
          )}

          {/* Form Header */}
          <Box sx={{ mb: 4 }}>
            <Box
              component="h2"
              sx={{
                fontSize: "1.875rem",
                fontWeight: 700,
                color: "hsl(220, 20%, 98%)",
                mb: 1,
                letterSpacing: "-0.01em",
              }}
            >
              {title}
            </Box>
            {subtitle && (
              <Box
                component="p"
                sx={{
                  fontSize: "1rem",
                  color: "hsl(215, 16%, 55%)",
                }}
              >
                {subtitle}
              </Box>
            )}
          </Box>

          {children}

          {/* Footer */}
          <Box sx={{ mt: 4, textAlign: "center" }}>
            <Box
              component="p"
              sx={{
                fontSize: "0.875rem",
                color: "hsl(215, 16%, 40%)",
              }}
            >
              By continuing, you agree to our{" "}
              <Link
                href="/terms"
                style={{
                  color: "hsl(239, 84%, 67%)",
                  textDecoration: "none",
                  fontWeight: 500,
                }}
              >
                Terms of Service
              </Link>{" "}
              and{" "}
              <Link
                href="/privacy"
                style={{
                  color: "hsl(239, 84%, 67%)",
                  textDecoration: "none",
                  fontWeight: 500,
                }}
              >
                Privacy Policy
              </Link>
            </Box>
          </Box>
        </motion.div>
      </Box>
    </Box>
  );
}
