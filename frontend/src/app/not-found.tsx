"use client";

import { Box, Container, Typography, Stack, Button } from "@mui/material";
import { motion } from "framer-motion";
import Link from "next/link";
import { ShieldAlert } from "lucide-react";

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
              display: "grid",
              placeItems: "center",
              position: "relative"
            }}>
              <ShieldAlert size={64} className="text-[#ea4335]" />
            </Box>

            <Stack spacing={1}>
              <Typography
                variant="h1"
                sx={{
                  fontWeight: 400,
                  fontSize: { xs: 48, md: 56 },
                  color: "var(--text-primary)",
                  lineHeight: 1.2,
                  fontFamily: "var(--font-outfit)",
                  letterSpacing: "-0.02em",
                }}
              >
                Page not found
              </Typography>
              <Typography
                sx={{
                  color: "var(--text-secondary)",
                  fontSize: { xs: 16, md: 18 },
                  fontFamily: "var(--font-sans)",
                }}
              >
                The page you&apos;re looking for doesn&apos;t exist or has been moved.
              </Typography>
            </Stack>

            <Button
              component={Link}
              href="/"
              variant="contained"
              disableElevation
              sx={{
                borderRadius: 99,
                px: 4,
                py: 1.5,
                bgcolor: "var(--primary)",
                color: "#fff",
                textTransform: "none",
                fontWeight: 500,
                fontSize: "0.95rem",
                "&:hover": {
                  bgcolor: "var(--primary-hover, rgba(26, 115, 232, 0.9))",
                }
              }}
            >
              Back to Home
            </Button>
          </Stack>
        </motion.div>
      </Container>
    </Box>
  );
}
