"use client";

import { useState } from "react";
import { Box, IconButton, Avatar, Menu, MenuItem, Badge, Divider, Tooltip } from "@mui/material";
import { motion } from "framer-motion";
import { Bell, Plus, Settings, LogOut, User, ChevronDown, MessageSquare, Sparkles } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { formatUserName } from "@/lib/theme";
import { cn } from "@/lib/utils";

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
      {/* Left side - Breadcrumbs or Contextual Title could go here */}
      <Box sx={{ display: { xs: "none", md: "block" } }} />

      {/* Right side actions */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, ml: "auto" }}>
        {showCopilotLink && (
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Box
              component={Link}
              href="/copilot"
              sx={{
                display: { xs: "none", sm: "flex" },
                alignItems: "center",
                gap: 1.5,
                px: 2.5,
                py: 1,
                background: "linear-gradient(135deg, #1a73e8 0%, #1557b0 100%)",
                color: "#fff",
                borderRadius: "24px",
                textDecoration: "none",
                fontWeight: 600,
                fontFamily: "var(--font-outfit)",
                fontSize: "13px",
                boxShadow: "0 4px 12px rgba(26, 115, 232, 0.2)",
                transition: "all 0.2s ease",
                "&:hover": {
                  boxShadow: "0 6px 16px rgba(26, 115, 232, 0.3)",
                  transform: "translateY(-1px)",
                },
              }}
            >
              <Sparkles size={14} />
              AI Copilot
            </Box>
          </motion.div>
        )}

        {/* New Session Button */}
        <Tooltip title="Create New Event">
          <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
            <Box
              component={Link}
              href="/dashboard/book"
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: 40,
                height: 40,
                background: "#E8F0FE",
                color: "#1a73e8",
                borderRadius: "50%",
                textDecoration: "none",
                transition: "all 0.2s ease",
                "&:hover": {
                  background: "#D2E3FC",
                },
              }}
            >
              <Plus size={20} />
            </Box>
          </motion.div>
        </Tooltip>

        <Divider orientation="vertical" flexItem sx={{ height: 24, alignSelf: "center", mx: 0.5, borderColor: "var(--border-subtle)" }} />

        {/* Notifications */}
        <IconButton
          sx={{
            width: 40,
            height: 40,
            borderRadius: "50%",
            background: "transparent",
            color: "var(--text-secondary)",
            "&:hover": {
              background: "var(--bg-hover)",
              color: "#1a73e8",
            },
          }}
        >
          <Badge
            badgeContent={notificationCount}
            sx={{
              "& .MuiBadge-badge": {
                background: "#ea4335",
                color: "white",
                fontSize: "10px",
                fontWeight: 700,
                minWidth: 16,
                height: 16,
                borderRadius: "50%",
              },
            }}
          >
            <Bell size={20} />
          </Badge>
        </IconButton>

        {/* User Profile Trigger */}
        <Box
          onClick={(e) => setAnchorEl(e.currentTarget)}
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1.5,
            cursor: "pointer",
            p: "4px 8px 4px 4px",
            borderRadius: "28px",
            background: "transparent",
            border: "1px solid var(--border-subtle)",
            transition: "all 0.2s ease",
            "&:hover": {
              background: "var(--bg-hover)",
              borderColor: "#1a73e8",
            },
          }}
        >
          <Avatar
            src={userAvatar}
            sx={{
              width: 32,
              height: 32,
              background: "#1a73e8",
              color: "#fff",
              fontSize: "12px",
              fontWeight: 700,
              fontFamily: "var(--font-outfit)",
            }}
          >
            {!userAvatar && initials}
          </Avatar>
          <Box sx={{ display: { xs: "none", sm: "block" }, pr: 1 }}>
            <Box
              sx={{
                fontSize: "13px",
                fontWeight: 600,
                color: "var(--text-primary)",
                fontFamily: "var(--font-outfit)",
              }}
            >
              {displayName}
            </Box>
          </Box>
          <ChevronDown size={14} className="text-slate-400" />
        </Box>

        {/* User Dropdown Menu */}
        <Menu
          anchorEl={anchorEl}
          open={menuOpen}
          onClose={() => setAnchorEl(null)}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          PaperProps={{
            sx: {
              mt: 1.5,
              background: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "16px",
              boxShadow: "0 10px 40px rgba(0,0,0,0.1)",
              minWidth: 220,
              p: 1,
            },
          }}
        >
          <Box sx={{ px: 2, py: 1.5, mb: 1 }}>
            <Box sx={{ fontSize: "14px", fontWeight: 700, color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
              {displayName}
            </Box>
            {userEmail && (
              <Box sx={{ fontSize: "12px", color: "var(--text-muted)", mt: 0.5, fontFamily: "var(--font-outfit)" }}>
                {userEmail}
              </Box>
            )}
          </Box>
          
          <Divider sx={{ my: 1, opacity: 0.5 }} />

          <MenuItem
            component={Link}
            href="/dashboard/settings"
            onClick={() => setAnchorEl(null)}
            sx={{
              borderRadius: "8px",
              py: 1.2,
              px: 2,
              fontSize: "13px",
              fontFamily: "var(--font-outfit)",
              color: "var(--text-primary)",
              gap: 2,
              "&:hover": { background: "#F1F3F4", color: "#1a73e8" },
            }}
          >
            <Settings size={18} />
            Account Settings
          </MenuItem>
          
          <MenuItem
            sx={{
              borderRadius: "8px",
              py: 1.2,
              px: 2,
              mt: 0.5,
              fontSize: "13px",
              fontFamily: "var(--font-outfit)",
              color: "#ea4335",
              gap: 2,
              "&:hover": { background: "rgba(234, 67, 53, 0.1)" },
            }}
          >
            <LogOut size={18} />
            Sign Out
          </MenuItem>
        </Menu>
      </Box>
    </Box>
  );
}
