"use client";

import { useState, ReactNode, useRef, useEffect } from "react";
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
  const [anchorEl, setAnchorEl] = useState<HTMLDivElement | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleMouseEnter = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setOpen(true), delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setOpen(false), delay);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, []);

  return (
    <Box
      ref={setAnchorEl}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      sx={{ position: "relative", display: "inline-flex" }}
    >
      {children}
      
      <Popper
        open={open}
        anchorEl={anchorEl}
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
              background: "#3C4043",
              border: "1px solid rgba(255,255,255,0.06)",
              borderRadius: "8px",
              px: 2,
              py: 1,
              color: "#FFFFFF",
              fontSize: "0.8125rem",
              fontWeight: 500,
              maxWidth: 250,
              boxShadow: "0 12px 28px -12px rgba(32,33,36,0.55)",
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
