"use client";

import { Box } from "@mui/material";
import { motion } from "framer-motion";

export function FloatingOrbs() {
  return (
    <Box
      sx={{
        position: "fixed",
        inset: 0,
        pointerEvents: "none",
        zIndex: 0,
        overflow: "hidden",
      }}
    >
      {/* Orb 1 - Neon Green */}
      <motion.div
        animate={{
          x: [0, 40, 0],
          y: [0, -40, 0],
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        style={{
          position: "absolute",
          top: "5%",
          right: "5%",
          width: 500,
          height: 500,
          background: "radial-gradient(circle, rgba(0, 255, 156, 0.08) 0%, transparent 70%)",
          borderRadius: "50%",
          filter: "blur(100px)",
        }}
      />

      {/* Orb 2 - Cyan */}
      <motion.div
        animate={{
          x: [0, -30, 0],
          y: [0, 30, 0],
          scale: [1, 1.2, 1],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 2,
        }}
        style={{
          position: "absolute",
          bottom: "15%",
          left: "2%",
          width: 600,
          height: 600,
          background: "radial-gradient(circle, rgba(0, 229, 255, 0.05) 0%, transparent 70%)",
          borderRadius: "50%",
          filter: "blur(120px)",
        }}
      />

      {/* Orb 3 - Magenta (very subtle) */}
      <motion.div
        animate={{
          x: [0, 15, 0],
          y: [0, -15, 0],
        }}
        transition={{
          duration: 30,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 5,
        }}
        style={{
          position: "absolute",
          top: "40%",
          left: "40%",
          transform: "translate(-50%, -50%)",
          width: 700,
          height: 700,
          background: "radial-gradient(circle, rgba(255, 0, 255, 0.03) 0%, transparent 70%)",
          borderRadius: "50%",
          filter: "blur(150px)",
        }}
      />
    </Box>
  );
}
