"use client";

import { IconButton, Menu, MenuItem } from "@mui/material";
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
          background: "#FFFFFF",
          border: "1px solid #DADCE0",
          color: "#5F6368",
          transition: "all 0.2s ease",
          boxShadow: "0 1px 2px rgba(32,33,36,0.08)",
          "&:hover": {
            background: "#F1F3F4",
            borderColor: "#BDC1C6",
            transform: "scale(1.02)",
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
            background: "#FFFFFF",
            border: "1px solid #DADCE0",
            borderRadius: "20px",
            boxShadow: "0 24px 60px -38px rgba(32,33,36,0.28)",
            minWidth: 160,
            mt: 1,
            py: 0.5,
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
              py: 1.1,
              px: 1.5,
              mx: 0.5,
              borderRadius: "12px",
              color: mode === theme.value ? "#1967D2" : "#202124",
              fontWeight: mode === theme.value ? 600 : 400,
              background: mode === theme.value ? "#E8F0FE" : "transparent",
              "&:hover": {
                background: "#F1F3F4",
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
