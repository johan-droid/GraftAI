"use client";

import { Box, Typography, Container, Stack } from "@mui/material";
import { motion } from "framer-motion";

const logos = [
  "NOTION", "LINEAR", "FIGMA", "VERCEL", "STRIPE", "SLACK", "DISCORD", "GITHUB"
];

export function LogoCloud() {
  return (
    <Box sx={{ py: 6, borderBottom: "1px solid var(--border-dotted)", background: "rgba(0,0,0,0.2)" }}>
      <Container maxWidth="lg">
        <Typography
          textAlign="center"
          sx={{ 
            color: "var(--text-faint)", 
            mb: 4, 
            fontSize: "10px", 
            fontFamily: "var(--font-mono)",
            letterSpacing: "0.2em"
          }}
        >
          // TRUSTED_BY_NODES
        </Typography>

        <Stack 
          direction="row" 
          spacing={6} 
          justifyContent="center" 
          alignItems="center" 
          sx={{ 
            opacity: 0.3,
            flexWrap: "wrap",
            gap: 4
          }}
        >
          {logos.map((name) => (
            <Typography
              key={name}
              sx={{
                fontSize: "14px",
                fontWeight: 800,
                color: "var(--text-muted)",
                fontFamily: "var(--font-mono)",
                transition: "color 0.2s",
                "&:hover": { color: "var(--primary)" }
              }}
            >
              {name}
            </Typography>
          ))}
        </Stack>
      </Container>
    </Box>
  );
}
