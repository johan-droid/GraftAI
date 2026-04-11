"use client";

import { useState, useEffect } from "react";
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Box, 
  Button, 
  IconButton, 
  Drawer, 
  List, 
  ListItem, 
  ListItemText,
  useMediaQuery,
  useTheme
} from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { Menu, X, Sparkles } from "lucide-react";
import { GradientButton } from "@/components/ui/GradientButton";

const navLinks = [
  { label: "Features", href: "#features" },
  { label: "Pricing", href: "#pricing" },
  { label: "How it Works", href: "#how-it-works" },
  { label: "Docs", href: "/docs" },
];

export function Navigation() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleNavClick = () => {
    setMobileMenuOpen(false);
  };

  return (
    <>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          background: scrolled 
            ? "rgba(15, 15, 26, 0.95)" 
            : "transparent",
          backdropFilter: scrolled ? "blur(20px)" : "none",
          borderBottom: scrolled ? "1px solid rgba(99, 102, 241, 0.1)" : "none",
          transition: "all 0.3s ease",
        }}
      >
        <Toolbar sx={{ justifyContent: "space-between", px: { xs: 2, md: 4 } }}>
          {/* Logo */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Link href="/" style={{ textDecoration: "none" }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Sparkles size={28} style={{ color: "#6366f1" }} />
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 800,
                    background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    letterSpacing: "-0.02em",
                  }}
                >
                  GraftAI
                </Typography>
              </Box>
            </Link>
          </motion.div>

          {/* Desktop Navigation */}
          {!isMobile && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                {navLinks.map((link) => (
                  <Button
                    key={link.href}
                    component={Link}
                    href={link.href}
                    sx={{
                      color: "#94a3b8",
                      textTransform: "none",
                      fontSize: "0.9rem",
                      px: 2,
                      position: "relative",
                      "&::after": {
                        content: '""',
                        position: "absolute",
                        bottom: 6,
                        left: "50%",
                        width: 0,
                        height: 2,
                        background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                        transition: "all 0.3s ease",
                        transform: "translateX(-50%)",
                      },
                      "&:hover": {
                        color: "#f8fafc",
                        "&::after": {
                          width: "60%",
                        },
                      },
                    }}
                  >
                    {link.label}
                  </Button>
                ))}
                <GradientButton
                  component={Link}
                  href="/register"
                  gradientVariant="primary"
                  size="small"
                  sx={{ ml: 2 }}
                >
                  Get Started
                </GradientButton>
              </Box>
            </motion.div>
          )}

          {/* Mobile Menu Button */}
          {isMobile && (
            <IconButton
              onClick={() => setMobileMenuOpen(true)}
              sx={{ color: "#f8fafc" }}
            >
              <Menu size={24} />
            </IconButton>
          )}
        </Toolbar>
      </AppBar>

      {/* Mobile Drawer */}
      <Drawer
        anchor="right"
        open={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
        PaperProps={{
          sx: {
            width: "100%",
            maxWidth: 320,
            background: "linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%)",
            borderLeft: "1px solid rgba(99, 102, 241, 0.2)",
          },
        }}
      >
        <Box sx={{ p: 3 }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 4 }}>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 800,
                background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              GraftAI
            </Typography>
            <IconButton onClick={() => setMobileMenuOpen(false)} sx={{ color: "#f8fafc" }}>
              <X size={24} />
            </IconButton>
          </Box>

          <List>
            {navLinks.map((link, index) => (
              <motion.div
                key={link.href}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <ListItem sx={{ px: 0 }}>
                  <Link
                    href={link.href}
                    onClick={handleNavClick}
                    style={{ textDecoration: "none", width: "100%" }}
                  >
                    <ListItemText
                      primary={link.label}
                      sx={{
                        color: "#94a3b8",
                        "& .MuiListItemText-primary": {
                          fontSize: "1.1rem",
                          fontWeight: 500,
                        },
                        "&:hover": {
                          color: "#f8fafc",
                        },
                      }}
                    />
                  </Link>
                </ListItem>
              </motion.div>
            ))}
          </List>

          <Box sx={{ mt: 4 }}>
            <GradientButton
              component={Link}
              href="/register"
              gradientVariant="primary"
              fullWidth
              size="large"
              onClick={handleNavClick}
            >
              Get Started Free
            </GradientButton>
            <Button
              component={Link}
              href="/login"
              fullWidth
              sx={{
                mt: 2,
                color: "#94a3b8",
                textTransform: "none",
                fontSize: "1rem",
              }}
              onClick={handleNavClick}
            >
              Sign In
            </Button>
          </Box>
        </Box>
      </Drawer>
    </>
  );
}
