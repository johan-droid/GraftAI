"use client";

import { useState } from "react";
import { Box, Drawer, IconButton, List, ListItem, ListItemIcon, ListItemText, Divider } from "@mui/material";
import { motion } from "framer-motion";
import { Menu, X, LayoutDashboard, Calendar, MessageSquare, Zap, Settings, LogOut, ChevronRight } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkles } from "lucide-react";

const navItems = [
  { label: "Overview", icon: LayoutDashboard, href: "/dashboard" },
  { label: "Calendar", icon: Calendar, href: "/calendar" },
  { label: "AI Copilot", icon: MessageSquare, href: "/copilot" },
  { label: "Integrations", icon: Zap, href: "/integrations" },
  { label: "Settings", icon: Settings, href: "/dashboard/settings" },
];

export function MobileSidebar() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  const toggleDrawer = () => setOpen(!open);

  return (
    <>
      {/* Mobile Menu Button */}
      <IconButton
        onClick={toggleDrawer}
        sx={{
          position: "fixed",
          top: 16,
          left: 16,
          zIndex: 1000,
          width: 44,
          height: 44,
          borderRadius: "12px",
          background: "rgba(255,255,255,0.92)",
          backdropFilter: "blur(12px)",
          border: "1px solid #DADCE0",
          color: "#1A73E8",
          display: { xs: "flex", md: "none" },
          boxShadow: "0 12px 28px -18px rgba(32, 33, 36, 0.24)",
          "&:hover": {
            background: "#F8F9FA",
          },
        }}
      >
        <Menu size={22} />
      </IconButton>

      {/* Mobile Drawer */}
      <Drawer
        anchor="left"
        open={open}
        onClose={() => setOpen(false)}
        PaperProps={{
          sx: {
            width: 280,
            background: "#F8F9FA",
            border: "none",
            borderRight: "1px solid #DADCE0",
          },
        }}
      >
        <Box sx={{ p: 3 }}>
          {/* Close Button */}
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 4 }}>
            {/* Logo */}
            <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
              <Box
                sx={{
                  width: 40,
                  height: 40,
                  borderRadius: "10px",
                  background: "#1A73E8",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Sparkles size={22} color="white" />
              </Box>
              <Box
                component="span"
                sx={{
                  fontSize: "1.25rem",
                  fontWeight: 800,
                  color: "#202124",
                  letterSpacing: "-0.02em",
                }}
              >
                GraftAI
              </Box>
            </Box>

            <IconButton
              onClick={() => setOpen(false)}
              sx={{
                color: "#5F6368",
                "&:hover": { color: "#202124" },
              }}
            >
              <X size={22} />
            </IconButton>
          </Box>

          {/* Navigation */}
          <List sx={{ px: 0 }}>
            {navItems.map((item, index) => {
              const isActive = pathname === item.href;
              return (
                <motion.div
                  key={item.label}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <ListItem
                    component={Link}
                    href={item.href}
                    onClick={() => setOpen(false)}
                    sx={{
                      borderRadius: "16px",
                      mb: 1,
                      px: 2,
                      py: 1.5,
                      background: isActive
                        ? "#E8F0FE"
                        : "transparent",
                      border: isActive ? "1px solid #D2E3FC" : "1px solid transparent",
                      color: isActive ? "#1967D2" : "#5F6368",
                      transition: "all 0.2s ease",
                      "&:hover": {
                        background: "#F1F3F4",
                        color: "#202124",
                      },
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        minWidth: 40,
                        color: "inherit",
                      }}
                    >
                      <item.icon size={20} />
                    </ListItemIcon>
                    <ListItemText
                      primary={item.label}
                      sx={{
                        "& .MuiListItemText-primary": {
                          fontWeight: isActive ? 600 : 500,
                          fontSize: "0.9375rem",
                        },
                      }}
                    />
                    {isActive && <ChevronRight size={16} />}
                  </ListItem>
                </motion.div>
              );
            })}
          </List>

          <Divider sx={{ my: 2, borderColor: "#DADCE0" }} />

          {/* Sign Out */}
          <ListItem
            sx={{
              borderRadius: "16px",
              px: 2,
              py: 1.5,
              color: "#D93025",
              cursor: "pointer",
              "&:hover": {
                background: "#FCE8E6",
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 40, color: "inherit" }}>
              <LogOut size={20} />
            </ListItemIcon>
            <ListItemText
              primary="Sign Out"
              sx={{
                "& .MuiListItemText-primary": {
                  fontWeight: 500,
                  fontSize: "0.9375rem",
                },
              }}
            />
          </ListItem>
        </Box>
      </Drawer>
    </>
  );
}
