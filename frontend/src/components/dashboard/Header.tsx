"use client";

import { useState } from "react";
import { Box, IconButton, Avatar, Menu, MenuItem, Badge, Divider } from "@mui/material";
import { motion } from "framer-motion";
import { Bell, Plus, Settings, LogOut, User, ChevronDown, MessageSquare } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { formatUserName } from "@/lib/theme";

interface HeaderProps {
  userName?: string;
  userEmail?: string;
  userAvatar?: string;
  notificationCount?: number;
}

export function Header({ userName, userEmail, userAvatar, notificationCount = 0 }: HeaderProps) {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const menuOpen = Boolean(anchorEl);
  const pathname = usePathname();
  const showCopilotLink = pathname !== "/copilot" && !pathname.startsWith("/dashboard/ai");

  const displayName = userName || (userEmail ? formatUserName(userEmail) : "User");
  const initials = displayName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 2,
        mb: { xs: 2, md: 4 },
        flexWrap: { xs: "wrap", md: "nowrap" },
      }}
    >
      {/* Left side - hidden on mobile */}
      <Box sx={{ display: { xs: "none", md: "block" } }} />

      {/* Right side actions */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, ml: "auto" }}>
        {showCopilotLink && (
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Box
              component={Link}
              href="/copilot"
              sx={{
                display: { xs: "none", sm: "flex" },
                alignItems: "center",
                gap: 1,
                px: 2,
                py: 0.5,
                background: "rgba(0, 255, 156, 0.06)",
                color: "var(--primary)",
                borderRadius: "0",
                textDecoration: "none",
                fontWeight: 700,
                fontFamily: "var(--font-mono)",
                fontSize: "9px",
                textTransform: "none",
                letterSpacing: "0.05em",
                border: "1px solid var(--border-subtle)",
                "&:hover": {
                  background: "rgba(0, 255, 156, 0.12)",
                  color: "var(--primary)",
                },
              }}
            >
              <MessageSquare size={12} />
              AI_COPILOT
            </Box>
          </motion.div>
        )}

        {/* New Session Button (compact) */}
        <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
          <Box
            component={Link}
            href="/dashboard/book"
            sx={{
              display: { xs: "none", sm: "flex" },
              alignItems: "center",
              gap: 1,
              px: 2,
              py: 0.5,
              background: "var(--primary)",
              color: "#000",
              borderRadius: "4px",
              textDecoration: "none",
              fontWeight: 700,
              fontFamily: "var(--font-mono)",
              fontSize: "9px",
              textTransform: "none",
              letterSpacing: "0.05em",
              border: "1px solid var(--primary)",
              "&:hover": {
                background: "transparent",
                color: "var(--primary)",
              },
            }}
          >
            <Plus size={12} />
          </Box>
        </motion.div>

        {/* Notifications */}
        <IconButton
          sx={{
            width: 36,
            height: 36,
            borderRadius: "0",
            background: "transparent",
            border: "1px solid var(--border-subtle)",
            color: "var(--text-primary)",
            "&:hover": {
              borderColor: "var(--primary)",
              color: "var(--primary)",
            },
          }}
        >
          <Badge
            badgeContent={notificationCount}
            sx={{
              "& .MuiBadge-badge": {
                background: "var(--accent)",
                color: "white",
                fontSize: "8px",
                minWidth: 14,
                height: 14,
                borderRadius: "0",
              },
            }}
          >
            <Bell size={16} />
          </Badge>
        </IconButton>

        {/* User Menu */}
        <Box
          onClick={(e) => setAnchorEl(e.currentTarget)}
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1.5,
            cursor: "pointer",
            p: "4px 12px 4px 4px",
            borderRadius: "0",
            background: "rgba(255,255,255,0.03)",
            border: "1px solid var(--border-subtle)",
            "&:hover": {
              borderColor: "var(--primary)",
            },
          }}
        >
          <Avatar
            src={userAvatar}
            sx={{
              width: 28,
              height: 28,
              background: "var(--bg-elevated)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "0",
              fontSize: "10px",
              fontWeight: 700,
              fontFamily: "var(--font-mono)",
              color: "var(--primary)",
            }}
          >
            {!userAvatar && initials}
          </Avatar>
          <Box sx={{ display: { xs: "none", sm: "block" } }}>
            <Box
              sx={{
                fontSize: "12px",
                fontWeight: 700,
                color: "var(--text-primary)",
                fontFamily: "var(--font-mono)",
                textTransform: "none",
              }}
            >
              {displayName}
            </Box>
          </Box>
        </Box>

        {/* User Dropdown Menu */}
        <Menu
          anchorEl={anchorEl}
          open={menuOpen}
          onClose={() => setAnchorEl(null)}
          PaperProps={{
            sx: {
              background: "var(--bg-elevated)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "0",
              boxShadow: "none",
              minWidth: 180,
            },
          }}
        >
          <Box sx={{ px: 2, py: 1.5, borderBottom: "1px solid var(--border-subtle)" }}>
            <Box sx={{ fontSize: "12px", fontWeight: 700, color: "var(--text-primary)", fontFamily: "var(--font-mono)", textTransform: "none" }}>
              {displayName}
            </Box>
            {userEmail && (
              <Box sx={{ fontSize: "11px", color: "var(--text-muted)", mt: 0.5, fontFamily: "var(--font-mono)" }}>
                {userEmail}
              </Box>
            )}
          </Box>
          
          <MenuItem
            component={Link}
            href="/settings"
            onClick={() => setAnchorEl(null)}
            sx={{
              py: 1,
              fontSize: "10px",
              fontFamily: "var(--font-mono)",
              color: "var(--text-primary)",
              "&:hover": { background: "rgba(0, 255, 156, 0.1)", color: "var(--primary)" },
            }}
          >
            <Settings size={14} style={{ marginRight: 12 }} />
            SETTINGS_CONFIG
          </MenuItem>
          
          <MenuItem
            sx={{
              py: 1,
              fontSize: "10px",
              fontFamily: "var(--font-mono)",
              color: "var(--accent)",
              "&:hover": { background: "rgba(255, 0, 122, 0.1)" },
            }}
          >
            <LogOut size={14} style={{ marginRight: 12 }} />
            TERMINATE_SESSION
          </MenuItem>
        </Menu>
      </Box>
    </Box>
  );
}
