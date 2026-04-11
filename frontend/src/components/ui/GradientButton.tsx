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
    small: { px: 2, py: 0.75, fontSize: "0.875rem" },
    medium: { px: 3, py: 1.25, fontSize: "1rem" },
    large: { px: 4, py: 1.75, fontSize: "1.125rem" }
  };

  const variantStyles = {
    primary: {
      background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
      color: "white",
      border: "none",
      "&:hover": {
        background: "linear-gradient(135deg, #5558e0 0%, #d63d8a 100%)",
        boxShadow: "0 4px 20px rgba(99, 102, 241, 0.4)"
      }
    },
    secondary: {
      background: "rgba(99, 102, 241, 0.1)",
      color: "#a5b4fc",
      border: "1px solid rgba(99, 102, 241, 0.3)",
      "&:hover": {
        background: "rgba(99, 102, 241, 0.2)",
        borderColor: "rgba(99, 102, 241, 0.5)"
      }
    },
    outline: {
      background: "transparent",
      color: "white",
      border: "1px solid rgba(255, 255, 255, 0.2)",
      "&:hover": {
        background: "rgba(255, 255, 255, 0.05)",
        borderColor: "rgba(255, 255, 255, 0.4)"
      }
    }
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      style={{ display: fullWidth ? "block" : "inline-block", width: fullWidth ? "100%" : "auto" }}
    >
      <Button
        {...props}
        fullWidth={fullWidth}
        sx={{
          textTransform: "none",
          borderRadius: "12px",
          fontWeight: 600,
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
