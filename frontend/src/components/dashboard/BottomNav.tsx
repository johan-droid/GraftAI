"use client";

import { Box } from "@mui/material";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { LayoutDashboard, Calendar, MessageSquare, User } from "lucide-react";

const navItems = [
  { label: "Home", icon: LayoutDashboard, href: "/dashboard" },
  { label: "Calendar", icon: Calendar, href: "/calendar" },
  { label: "Copilot", icon: MessageSquare, href: "/copilot" },
  { label: "Profile", icon: User, href: "/settings" },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <Box
      sx={{
        position: "fixed",
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        display: { xs: "flex", md: "none" },
        background: "var(--bg-surface)",
        backdropFilter: "none",
        borderTop: "1px solid var(--border-subtle)",
        px: 2,
        py: 1.5,
        justifyContent: "space-around",
        alignItems: "center",
        boxShadow: "0 -4px 16px rgba(0,0,0,0.04)",
      }}
    >
      {navItems.map((item) => {
        const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
        
        return (
          <Link
            key={item.label}
            href={item.href}
            style={{
              textDecoration: "none",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 4,
              position: "relative",
              padding: "8px 16px",
            }}
          >
            {/* Active Indicator Container */}
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: 64,
                height: 32,
                borderRadius: 16,
                background: isActive ? "var(--primary-glow)" : "transparent",
                color: isActive ? "var(--primary)" : "var(--text-secondary)",
                transition: "all 0.2s ease",
              }}
            >
              <item.icon size={22} strokeWidth={isActive ? 2.5 : 2} />
            </Box>

            {/* Label */}
            <Box
              component="span"
              sx={{
                fontSize: "0.7rem",
                fontWeight: isActive ? 600 : 500,
                color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                transition: "color 0.2s ease",
              }}
            >
              {item.label}
            </Box>
          </Link>
        );
      })}
    </Box>
  );
}
