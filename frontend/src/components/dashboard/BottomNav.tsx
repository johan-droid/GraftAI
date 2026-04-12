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
        background: "hsla(240, 24%, 10%, 0.95)",
        backdropFilter: "blur(20px)",
        borderTop: "1px solid hsla(239, 84%, 67%, 0.1)",
        px: 2,
        py: 1.5,
        justifyContent: "space-around",
        alignItems: "center",
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
            {/* Active Indicator */}
            {isActive && (
              <motion.div
                layoutId="bottomNavActive"
                style={{
                  position: "absolute",
                  top: -6,
                  width: 40,
                  height: 3,
                  borderRadius: "2px",
                  background: "linear-gradient(90deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                }}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              />
            )}

            {/* Icon */}
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: 24,
                height: 24,
                color: isActive ? "hsl(239, 84%, 67%)" : "hsl(215, 16%, 55%)",
                transition: "color 0.2s ease",
              }}
            >
              <item.icon size={22} strokeWidth={isActive ? 2.5 : 2} />
            </Box>

            {/* Label */}
            <Box
              component="span"
              sx={{
                fontSize: "0.6875rem",
                fontWeight: isActive ? 600 : 500,
                color: isActive ? "hsl(239, 84%, 67%)" : "hsl(215, 16%, 55%)",
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
