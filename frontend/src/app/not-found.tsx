"use client";

import { Box, Container, Typography, Stack, Button } from "@mui/material";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowLeft, ShieldAlert } from "lucide-react";

export default function NotFound() {
  return (
    <Box sx={{ bgcolor: "var(--bg-base)", minHeight: "100vh", position: "relative", display: "grid", placeItems: "center" }}>
      <Container maxWidth="sm" sx={{ position: "relative", zIndex: 1, textAlign: "center" }}>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        >
          <Stack spacing={6} alignItems="center">
            <Box sx={{ 
              width: 120, 
              height: 120, 
              borderRadius: "50%", 
              bgcolor: "rgba(234, 67, 53, 0.05)", 
              border: "1px dashed rgba(234, 67, 53, 0.2)",
              display: "grid",
              placeItems: "center",
              position: "relative"
            }}>
              <ShieldAlert size={48} className="text-[#ea4335] animate-pulse" />
              <Box className="system-status-dot" sx={{ position: "absolute", top: 20, right: 20, bgcolor: "#ea4335" }} />
            </Box>

            <Stack spacing={2}>
              <Typography
                variant="h1"
                sx={{
                  fontWeight: 900,
                  fontSize: { xs: 80, md: 120 },
                  letterSpacing: "-0.08em",
                  color: "var(--text-primary)",
                  lineHeight: 1,
                  fontFamily: "var(--font-sans)"
                }}
              >
                404
              </Typography>
              <Typography
                sx={{
                  color: "var(--text-muted)",
                  fontSize: { xs: 18, md: 22 },
                  fontFamily: "var(--font-mono)",
                  textTransform: "uppercase",
                  letterSpacing: "0.2em",
                  fontWeight: 800
                }}
              >
                Protocol Connection Lost
              </Typography>
            </Stack>

            <Typography sx={{ color: "var(--text-faint)", fontSize: 14, maxWidth: 400 }}>
              The requested node address could not be resolved by the primary kernel. It may have been relocated or decommissioned.
            </Typography>

            <Box sx={{ 
              width: "100%", 
              py: 2, 
              px: 3, 
              bgcolor: "rgba(255,255,255,0.01)", 
              border: "1px dashed var(--border-subtle)", 
              borderRadius: 1,
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              color: "#ea4335"
            }}>
              [ ERROR: NULL_POINTER_EXCEPTION_AT_ROUTE_RESOLUTION ]
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
                "&:hover": {
                  borderColor: "var(--primary)",
                  bgcolor: "rgba(0, 255, 156, 0.05)"
                }
              }}
            >
              Back to Command Center
            </Button>
          </Stack>
        </motion.div>
      </Container>
    </Box>
  );
}
