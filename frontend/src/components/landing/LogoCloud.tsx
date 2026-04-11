"use client";

import { Box, Typography, Container } from "@mui/material";
import { motion } from "framer-motion";

const logos = [
  { name: "Notion", color: "#ffffff" },
  { name: "Linear", color: "#5e6ad2" },
  { name: "Figma", color: "#f24e1e" },
  { name: "Vercel", color: "#ffffff" },
  { name: "Stripe", color: "#635bff" },
  { name: "Slack", color: "#4a154b" },
  { name: "Discord", color: "#5865f2" },
  { name: "GitHub", color: "#ffffff" },
];

export function LogoCloud() {
  return (
    <Box sx={{ py: { xs: 6, md: 10 }, background: "rgba(26, 26, 46, 0.3)" }}>
      <Container maxWidth="lg">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          viewport={{ once: true }}
        >
          <Typography
            variant="body2"
            textAlign="center"
            sx={{ color: "#64748b", mb: 4, fontSize: "0.875rem", textTransform: "uppercase", letterSpacing: 1 }}
          >
            Trusted by teams at
          </Typography>
        </motion.div>

        <Box sx={{ position: "relative", overflow: "hidden" }}>
          {/* Gradient Masks */}
          <Box
            sx={{
              position: "absolute",
              left: 0,
              top: 0,
              bottom: 0,
              width: { xs: 40, md: 100 },
              background: "linear-gradient(to right, #0f0f1a, transparent)",
              zIndex: 2,
            }}
          />
          <Box
            sx={{
              position: "absolute",
              right: 0,
              top: 0,
              bottom: 0,
              width: { xs: 40, md: 100 },
              background: "linear-gradient(to left, #0f0f1a, transparent)",
              zIndex: 2,
            }}
          />

          {/* Scrolling Logos */}
          <Box
            sx={{
              display: "flex",
              animation: "scroll 30s linear infinite",
              "@keyframes scroll": {
                "0%": { transform: "translateX(0)" },
                "100%": { transform: "translateX(-50%)" },
              },
            }}
          >
            {[...logos, ...logos].map((logo, index) => (
              <Box
                key={index}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  px: { xs: 4, md: 6 },
                  opacity: 0.5,
                  transition: "opacity 0.3s",
                  "&:hover": { opacity: 0.8 },
                }}
              >
                <Typography
                  sx={{
                    fontSize: { xs: "1.25rem", md: "1.5rem" },
                    fontWeight: 700,
                    color: "#64748b",
                    whiteSpace: "nowrap",
                  }}
                >
                  {logo.name}
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>
      </Container>
    </Box>
  );
}
