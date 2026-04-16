"use client";

import { Box, Typography, Stack, Button, Container } from "@mui/material";
import { motion } from "framer-motion";
import Link from "next/link";
import { Sparkles, ArrowLeft, Moon, Power } from "lucide-react";

export default function GoodbyePage() {
  return (
    <Box sx={{ bgcolor: "var(--bg-base)", minHeight: "100vh", position: "relative", overflow: "hidden" }}>
      <Box 
        sx={{
          position: "absolute",
          inset: 0,
          background: `
            radial-gradient(circle at 50% 50%, rgba(0, 255, 156, 0.02) 0%, transparent 70%)
          `,
          pointerEvents: "none",
        }}
      />

      <Container maxWidth="sm" sx={{ pt: { xs: 20, md: 30 }, pb: 10, position: "relative", zIndex: 1 }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
        >
          <Stack spacing={6} alignItems="center" textAlign="center">
            <Box sx={{ 
              width: 80, 
              height: 80, 
              borderRadius: "50%", 
              bgcolor: "rgba(0, 255, 156, 0.05)", 
              border: "1px solid rgba(0, 255, 156, 0.1)",
              display: "grid",
              placeItems: "center",
              position: "relative"
            }}>
              <Box className="system-status-dot" sx={{ position: "absolute", top: 10, right: 10 }} />
              <Power size={32} className="text-primary" />
            </Box>

            <Stack spacing={2}>
              <Typography
                variant="h3"
                sx={{
                  fontWeight: 900,
                  fontSize: { xs: 32, md: 42 },
                  letterSpacing: "-0.04em",
                  color: "var(--text-primary)",
                  fontFamily: "var(--font-sans)"
                }}
              >
                Until next time.
              </Typography>
              <Typography
                sx={{
                  color: "var(--text-secondary)",
                  fontSize: { xs: 16, md: 18 },
                  maxWidth: 400,
                  mx: "auto",
                  fontFamily: "var(--font-sans)"
                }}
              >
                You've been successfully signed out. Have a great day!
              </Typography>
            </Stack>

            <Box sx={{ width: "100%", maxW: 300, py: 4, px: 3, bgcolor: "var(--bg-surface)", border: "1px dashed var(--border-subtle)", borderRadius: 1 }}>
              <Typography sx={{ 
                fontFamily: "var(--font-sans)", 
                fontSize: 12, 
                color: "var(--text-faint)", 
                textTransform: "uppercase", 
                letterSpacing: "0.1em",
                mb: 1,
                fontWeight: 700
              }}>
                Status
              </Typography>
              <Typography sx={{ 
                fontFamily: "var(--font-sans)", 
                fontSize: 14, 
                color: "var(--primary)",
                fontWeight: 700
              }}>
                Signed out successfully
              </Typography>
            </Box>

            <Button
              component={Link}
              href="/"
              variant="outlined"
              startIcon={<ArrowLeft size={18} />}
              sx={{
                borderRadius: 99,
                px: 4,
                py: 1.5,
                borderColor: "var(--border-subtle)",
                color: "var(--text-primary)",
                textTransform: "none",
                fontWeight: 600,
                fontFamily: "var(--font-sans)",
                "&:hover": {
                  borderColor: "var(--primary)",
                  bgcolor: "rgba(0, 255, 156, 0.05)"
                }
              }}
            >
              Back to home
            </Button>
          </Stack>
        </motion.div>
      </Container>
    </Box>
  );
}
