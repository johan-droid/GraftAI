"use client";

import { Box, SxProps, Theme } from "@mui/material";
import { motion } from "framer-motion";
import { ReactNode } from "react";

interface GlowCardProps {
  children: ReactNode;
  glowColor?: string;
  intensity?: "low" | "medium" | "high";
  sx?: SxProps<Theme>;
}

const intensityMap = {
  low: "0 0 20px",
  medium: "0 0 40px",
  high: "0 0 60px"
};

export function GlowCard({ 
  children, 
  glowColor = "rgba(99, 102, 241, 0.3)", 
  intensity = "medium",
  sx = {}
}: GlowCardProps) {
  return (
    <motion.div
      whileHover={{ 
        y: -4,
        transition: { duration: 0.3, ease: "easeOut" }
      }}
      style={{ height: "100%" }}
    >
      <Box
        sx={{
          height: "100%",
          background: "linear-gradient(135deg, rgba(26, 26, 46, 0.8) 0%, rgba(15, 15, 26, 0.9) 100%)",
          backdropFilter: "blur(10px)",
          border: "1px solid rgba(99, 102, 241, 0.1)",
          borderRadius: 2,
          transition: "all 0.3s ease",
          position: "relative",
          overflow: "hidden",
          "&:hover": {
            borderColor: glowColor,
            boxShadow: `${intensityMap[intensity]} ${glowColor}`,
          },
          ...sx
        }}
      >
        {children}
      </Box>
    </motion.div>
  );
}
