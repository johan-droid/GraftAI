"use client";

import { Button, ButtonProps, SxProps, Theme } from "@mui/material";
import { motion } from "framer-motion";
import { ReactNode } from "react";

interface GradientButtonProps extends Omit<ButtonProps, "sx" | "variant"> {
  children: ReactNode;
  gradientVariant?: "primary" | "secondary" | "outline";
  size?: "small" | "medium" | "large";
  fullWidth?: boolean;
  sx?: SxProps<Theme>;
}

export function GradientButton({
  children,
  gradientVariant = "primary",
  size = "medium",
  fullWidth = false,
  sx = {},
  ...props
}: GradientButtonProps) {
  const sizeStyles = {
    small: { px: 2, py: 0.75, fontSize: "10px" },
    medium: { px: 3, py: 1, fontSize: "11px" },
    large: { px: 4, py: 1.5, fontSize: "12px" }
  };

  const variantStyles = {
    primary: {
      background: "var(--primary)",
      color: "#000",
      border: "1px solid var(--primary)",
      "&:hover": {
        background: "transparent",
        color: "var(--primary)",
        boxShadow: "0 0 15px rgba(0, 255, 156, 0.3)"
      }
    },
    secondary: {
      background: "rgba(0, 255, 156, 0.05)",
      color: "var(--primary)",
      border: "1px solid rgba(0, 255, 156, 0.2)",
      "&:hover": {
        background: "rgba(0, 255, 156, 0.1)",
        borderColor: "var(--primary)"
      }
    },
    outline: {
      background: "transparent",
      color: "var(--text-primary)",
      border: "1px dashed var(--border-subtle)",
      "&:hover": {
        background: "rgba(255, 255, 255, 0.02)",
        borderColor: "var(--primary)",
        color: "var(--primary)"
      }
    }
  };

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      style={{ display: fullWidth ? "block" : "inline-block", width: fullWidth ? "100%" : "auto" }}
    >
      <Button
        {...props}
        fullWidth={fullWidth}
        sx={{
          textTransform: "uppercase",
          fontFamily: "var(--font-mono)",
          letterSpacing: "0.1em",
          borderRadius: "0",
          fontWeight: 800,
          transition: "all 0.2s ease",
          ...sizeStyles[size],
          ...variantStyles[gradientVariant],
          ...sx
        }}
      >
        {children}
      </Button>
    </motion.div>
  );
}
