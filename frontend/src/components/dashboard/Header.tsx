"use client";

import { useState } from "react";
import { Box, IconButton, Avatar, Menu, MenuItem, Badge, Divider } from "@mui/material";
import { motion } from "framer-motion";
import { Bell, Plus, Settings, LogOut, User, ChevronDown } from "lucide-react";
import Link from "next/link";
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
      {/* Left side - hidden on mobile (shown in MobileSidebar) */}
      <Box sx={{ display: { xs: "none", md: "block" } }} />

      {/* Right side actions */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, ml: "auto" }}>
        {/* New Booking Button */}
        <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
          <Box
            component={Link}
            href="/book"
            sx={{
              display: { xs: "none", sm: "flex" },
              alignItems: "center",
              gap: 1,
              px: 3,
              py: 1.5,
              background: "linear-gradient(135deg, hsl(25, 95%, 53%) 0%, hsl(25, 95%, 63%) 100%)",
              color: "white",
              borderRadius: "12px",
              textDecoration: "none",
              fontWeight: 600,
              fontSize: "0.9375rem",
              boxShadow: "0 4px 15px hsla(25, 95%, 53%, 0.3)",
              transition: "all 0.2s ease",
              "&:hover": {
                boxShadow: "0 6px 20px hsla(25, 95%, 53%, 0.4)",
                transform: "translateY(-1px)",
              },
            }}
          >
            <Plus size={18} />
            New Booking
          </Box>
        </motion.div>

        {/* Mobile New Booking FAB */}
        <IconButton
          component={Link}
          href="/book"
          sx={{
            display: { xs: "flex", sm: "none" },
            background: "linear-gradient(135deg, hsl(25, 95%, 53%) 0%, hsl(25, 95%, 63%) 100%)",
            color: "white",
            width: 40,
            height: 40,
            borderRadius: "12px",
            "&:hover": {
              background: "linear-gradient(135deg, hsl(25, 95%, 48%) 0%, hsl(25, 95%, 58%) 100%)",
            },
          }}
        >
          <Plus size={20} />
        </IconButton>

        {/* Theme Toggle */}
        <ThemeToggle />

        {/* Notifications */}
        <IconButton
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
            },
          }}
        >
          <Badge
            badgeContent={notificationCount}
            color="error"
            sx={{
              "& .MuiBadge-badge": {
                background: "hsl(346, 84%, 61%)",
                fontSize: "0.625rem",
                minWidth: 18,
                height: 18,
              },
            }}
          >
            <Bell size={20} />
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
            p: 1,
            borderRadius: "12px",
            background: "hsla(239, 84%, 67%, 0.05)",
            border: "1px solid hsla(239, 84%, 67%, 0.1)",
            transition: "all 0.2s ease",
            "&:hover": {
              background: "hsla(239, 84%, 67%, 0.1)",
              borderColor: "hsla(239, 84%, 67%, 0.2)",
            },
          }}
        >
          <Avatar
            src={userAvatar}
            sx={{
              width: 36,
              height: 36,
              background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
              fontSize: "0.875rem",
              fontWeight: 600,
            }}
          >
            {!userAvatar && initials}
          </Avatar>
          <Box sx={{ display: { xs: "none", sm: "block" } }}>
            <Box
              sx={{
                fontSize: "0.875rem",
                fontWeight: 600,
                color: "hsl(220, 20%, 98%)",
                lineHeight: 1.2,
              }}
            >
              {displayName}
            </Box>
            <Box
              sx={{
                fontSize: "0.75rem",
                color: "hsl(215, 16%, 55%)",
                display: "flex",
                alignItems: "center",
                gap: 0.5,
              }}
            >
              Account
              <ChevronDown size={14} />
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
              background: "hsl(240, 24%, 14%)",
              border: "1px solid hsla(239, 84%, 67%, 0.2)",
              borderRadius: "12px",
              boxShadow: "0 10px 30px -10px rgba(0,0,0,0.5)",
              minWidth: 200,
            },
          }}
        >
          <Box sx={{ px: 2, py: 1.5 }}>
            <Box sx={{ fontWeight: 600, color: "hsl(220, 20%, 98%)" }}>{displayName}</Box>
            {userEmail && (
              <Box sx={{ fontSize: "0.75rem", color: "hsl(215, 16%, 55%)", mt: 0.5 }}>
                {userEmail}
              </Box>
            )}
          </Box>
          
          <Divider sx={{ borderColor: "hsla(239, 84%, 67%, 0.1)" }} />
          
          <MenuItem
            component={Link}
            href="/settings"
            onClick={() => setAnchorEl(null)}
            sx={{
              py: 1.5,
              color: "hsl(220, 20%, 98%)",
              "&:hover": { background: "hsla(239, 84%, 67%, 0.1)" },
            }}
          >
            <Settings size={16} style={{ marginRight: 12 }} />
            Settings
          </MenuItem>
          
          <MenuItem
            sx={{
              py: 1.5,
              color: "hsl(346, 84%, 61%)",
              "&:hover": { background: "hsla(346, 84%, 61%, 0.1)" },
            }}
          >
            <LogOut size={16} style={{ marginRight: 12 }} />
            Sign Out
          </MenuItem>
        </Menu>
      </Box>
    </Box>
  );
}
