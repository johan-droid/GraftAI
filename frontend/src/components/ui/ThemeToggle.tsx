"use client";

import { Box, IconButton, Menu, MenuItem } from "@mui/material";
import { useState } from "react";
import { motion } from "framer-motion";
import { Sun, Moon, Monitor, Check } from "lucide-react";
import { useTheme, ThemeMode } from "@/contexts/ThemeContext";

const themes: { value: ThemeMode; label: string; icon: typeof Sun }[] = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "auto", label: "System", icon: Monitor },
];

export function ThemeToggle() {
  const { mode, setMode } = useTheme();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleSelect = (newMode: ThemeMode) => {
    setMode(newMode);
    handleClose();
  };

  // Get current icon
  const CurrentIcon = themes.find((t) => t.value === mode)?.icon || Moon;

  return (
    <>
      <IconButton
        onClick={handleClick}
        sx={{
          width: 40,
          height: 40,
          borderRadius: "12px",
          background: "hsla(239, 84%, 67%, 0.1)",
          border: "1px solid hsla(239, 84%, 67%, 0.2)",
          color: "hsl(220, 20%, 98%)",
          transition: "all 0.2s ease",
          "&:hover": {
            background: "hsla(239, 84%, 67%, 0.2)",
            borderColor: "hsla(239, 84%, 67%, 0.4)",
            transform: "scale(1.05)",
          },
        }}
      >
        <motion.div
          key={mode}
          initial={{ rotate: -90, opacity: 0 }}
          animate={{ rotate: 0, opacity: 1 }}
          exit={{ rotate: 90, opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <CurrentIcon size={20} />
        </motion.div>
      </IconButton>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        PaperProps={{
          sx: {
            background: "hsl(240, 24%, 14%)",
            border: "1px solid hsla(239, 84%, 67%, 0.2)",
            borderRadius: "12px",
            boxShadow: "0 10px 30px -10px rgba(0,0,0,0.5)",
            minWidth: 160,
          },
        }}
      >
        {themes.map((theme) => (
          <MenuItem
            key={theme.value}
            onClick={() => handleSelect(theme.value)}
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1.5,
              py: 1,
              px: 2,
              color: mode === theme.value ? "hsl(239, 84%, 67%)" : "hsl(220, 20%, 98%)",
              fontWeight: mode === theme.value ? 600 : 400,
              background: mode === theme.value ? "hsla(239, 84%, 67%, 0.1)" : "transparent",
              "&:hover": {
                background: "hsla(239, 84%, 67%, 0.1)",
              },
            }}
          >
            <theme.icon size={16} />
            <span>{theme.label}</span>
            {mode === theme.value && <Check size={14} style={{ marginLeft: "auto" }} />}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
}
