"use client";

import { useState, ReactNode, useRef } from "react";
import { Box, Fade, Paper, Popper } from "@mui/material";

interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
  placement?: "top" | "bottom" | "left" | "right";
  delay?: number;
}

export function Tooltip({
  content,
  children,
  placement = "top",
  delay = 200,
}: TooltipProps) {
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleMouseEnter = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setOpen(true), delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setOpen(false), delay);
  };

  const getPlacementStyles = () => {
    switch (placement) {
      case "top":
        return { bottom: "100%", left: "50%", transform: "translateX(-50%)", mb: 1 };
      case "bottom":
        return { top: "100%", left: "50%", transform: "translateX(-50%)", mt: 1 };
      case "left":
        return { right: "100%", top: "50%", transform: "translateY(-50%)", mr: 1 };
      case "right":
        return { left: "100%", top: "50%", transform: "translateY(-50%)", ml: 1 };
    }
  };

  return (
    <Box
      ref={anchorRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      sx={{ position: "relative", display: "inline-flex" }}
    >
      {children}
      
      <Popper
        open={open}
        anchorEl={anchorRef.current}
        placement={placement}
        sx={{ zIndex: 9999 }}
        modifiers={[
          {
            name: "offset",
            options: {
              offset: [0, 8],
            },
          },
        ]}
      >
        <Fade in={open} timeout={150}>
          <Paper
            elevation={0}
            sx={{
              background: "hsl(240, 24%, 14%)",
              border: "1px solid hsla(239, 84%, 67%, 0.2)",
              borderRadius: "8px",
              px: 2,
              py: 1,
              color: "hsl(220, 20%, 98%)",
              fontSize: "0.8125rem",
              fontWeight: 500,
              maxWidth: 250,
              boxShadow: "0 10px 30px -10px rgba(0,0,0,0.5)",
              ...getPlacementStyles(),
            }}
          >
            {content}
          </Paper>
        </Fade>
      </Popper>
    </Box>
  );
}

// Simple version with just text
export function SimpleTooltip({ text, children }: { text: string; children: ReactNode }) {
  return (
    <Tooltip content={text}>
      {children}
    </Tooltip>
  );
}
