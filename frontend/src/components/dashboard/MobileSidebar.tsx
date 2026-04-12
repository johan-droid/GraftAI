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
  { label: "Settings", icon: Settings, href: "/settings" },
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
          background: "hsla(240, 24%, 14%, 0.9)",
          backdropFilter: "blur(10px)",
          border: "1px solid hsla(239, 84%, 67%, 0.2)",
          color: "hsl(220, 20%, 98%)",
          display: { xs: "flex", md: "none" },
          "&:hover": {
            background: "hsla(239, 84%, 67%, 0.2)",
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
            background: "hsl(240, 24%, 10%)",
            border: "none",
            borderRight: "1px solid hsla(239, 84%, 67%, 0.1)",
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
                  background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
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
                  background: "linear-gradient(135deg, hsl(220, 20%, 98%) 0%, hsl(215, 16%, 70%) 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  letterSpacing: "-0.02em",
                }}
              >
                GraftAI
              </Box>
            </Box>

            <IconButton
              onClick={() => setOpen(false)}
              sx={{
                color: "hsl(215, 16%, 55%)",
                "&:hover": { color: "hsl(220, 20%, 98%)" },
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
                      borderRadius: "12px",
                      mb: 1,
                      px: 2,
                      py: 1.5,
                      background: isActive
                        ? "linear-gradient(135deg, hsla(239, 84%, 67%, 0.2) 0%, hsla(239, 84%, 67%, 0.1) 100%)"
                        : "transparent",
                      border: isActive ? "1px solid hsla(239, 84%, 67%, 0.3)" : "1px solid transparent",
                      color: isActive ? "hsl(239, 84%, 67%)" : "hsl(215, 16%, 70%)",
                      transition: "all 0.2s ease",
                      "&:hover": {
                        background: "hsla(239, 84%, 67%, 0.1)",
                        color: "hsl(220, 20%, 98%)",
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

          <Divider sx={{ my: 2, borderColor: "hsla(239, 84%, 67%, 0.1)" }} />

          {/* Sign Out */}
          <ListItem
            sx={{
              borderRadius: "12px",
              px: 2,
              py: 1.5,
              color: "hsl(346, 84%, 61%)",
              cursor: "pointer",
              "&:hover": {
                background: "hsla(346, 84%, 61%, 0.1)",
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
