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
  useMediaQuery,
  useTheme,
  Stack,
  Container
} from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { Menu, X, Terminal, Activity, Cpu, Globe, Database, Fingerprint, Clock as ClockIcon } from "lucide-react";

const navLinks = [
  { label: "// SYSTEMS", href: "#features" },
  { label: "// NODES", href: "/dashboard" },
  { label: "// PROTOCOLS", href: "#how-it-works" },
  { label: "// DEV_HUB", href: "/developers" },
];

function Clock() {
  const [time, setTime] = useState("");

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString("en-US", { hour12: false }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return <span>{time || "00:00:00"}</span>;
}

function TelemetryBar({ isMobile }: { isMobile: boolean }) {
  if (isMobile) return null;

  return (
    <Box
      sx={{
        py: 0.75,
        borderBottom: "1px dashed var(--border-subtle)",
        background: "rgba(0,0,0,0.8)",
        backdropFilter: "blur(4px)",
      }}
    >
      <Container maxWidth={false}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" spacing={4} alignItems="center">
            {[
              { label: "KERN_V", value: "3.0.82-BETA", icon: Cpu },
              { label: "PID", value: "2841-SYS", icon: Fingerprint },
              { label: "LOCAL_NODE", value: "GRAFT_PRIMARY", icon: Globe },
              { label: "SYS_TIME", value: <Clock />, icon: ClockIcon },
            ].map((stat, i) => (
              <Stack key={i} direction="row" spacing={1} alignItems="center">
                <stat.icon size={10} className="text-[var(--text-faint)]" />
                <Typography className="telemetry-text">
                  {stat.label}: <Box component="span" sx={{ color: "var(--primary)" }}>{stat.value}</Box>
                </Typography>
              </Stack>
            ))}
          </Stack>
          
          <Typography sx={{ fontSize: "8px", fontStyle: "italic", fontWeight: 900, color: "var(--text-faint)", fontFamily: "var(--font-mono)" }}>
             // SECURE_CONNECTION_ESTABLISHED
          </Typography>
        </Stack>
      </Container>
    </Box>
  );
}

export function Navigation() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          background: scrolled ? "rgba(5, 5, 5, 0.98)" : "rgba(5, 5, 5, 0.5)",
          borderBottom: "1px solid var(--border-subtle)",
          transition: "all 0.3s ease",
          zIndex: 1101,
        }}
      >
        <TelemetryBar isMobile={isMobile} />
        
        <Toolbar sx={{ justifyContent: "space-between", px: { xs: 2.5, md: 8 }, height: { xs: 70, md: 80 } }}>
          {/* Logo Section */}
          <Link href="/" style={{ textDecoration: "none" }}>
            <Stack direction="row" spacing={2} alignItems="center" sx={{ position: "relative" }}>
              <Box sx={{ 
                width: 36, 
                height: 36, 
                display: "flex", 
                alignItems: "center", 
                justifyContent: "center",
                border: "1px solid var(--primary)",
                background: "rgba(0, 255, 156, 0.05)",
                borderRadius: 0,
                position: "relative",
              }}>
                <Terminal size={20} className="text-[var(--primary)]" />
              </Box>
              <Typography
                sx={{
                  fontWeight: 900,
                  fontSize: "1.25rem",
                  fontFamily: "var(--font-mono)",
                  letterSpacing: "-0.05em",
                  color: "var(--text-primary)",
                  textTransform: "uppercase"
                }}
              >
                GraftAI<Box component="span" sx={{ color: "var(--text-faint)", fontWeight: 400 }}>_NODE</Box>
              </Typography>
            </Stack>
          </Link>

          {/* Desktop Nav */}
          {!isMobile && (
            <Stack direction="row" spacing={1} alignItems="center">
              {navLinks.map((link) => (
                <Button
                  key={link.href}
                  component={Link}
                  href={link.href}
                  sx={{
                    color: "var(--text-secondary)",
                    textTransform: "none",
                    fontSize: "10px",
                    fontWeight: 800,
                    fontFamily: "var(--font-mono)",
                    px: 3,
                    letterSpacing: "0.15em",
                    position: "relative",
                    "&:hover": {
                      color: "var(--primary)",
                      background: "rgba(255,255,255,0.02)",
                    },
                  }}
                >
                  {link.label}
                </Button>
              ))}
              
              <Box sx={{ width: "1px", height: "16px", background: "var(--border-subtle)", mx: 3 }} />
              
              <Button
                component={Link}
                href="/login"
                sx={{
                  background: "transparent",
                  border: "1px dashed var(--border-subtle)",
                  color: "var(--text-primary)",
                  fontFamily: "var(--font-mono)",
                  fontSize: "11px",
                  fontWeight: 900,
                  borderRadius: "0",
                  px: 4,
                  py: 1.5,
                  letterSpacing: "0.1em",
                  mr: 2,
                  "&:hover": {
                    borderColor: "var(--primary)",
                    background: "rgba(0, 255, 156, 0.05)"
                  }
                }}
              >
                // SIGN_IN
              </Button>

              <Button
                component={Link}
                href="/onboarding"
                sx={{
                  background: "var(--primary)",
                  color: "#000",
                  fontFamily: "var(--font-mono)",
                  fontSize: "11px",
                  fontWeight: 900,
                  borderRadius: "0",
                  px: 4,
                  py: 1.5,
                  letterSpacing: "0.1em",
                  textTransform: "uppercase",
                  transition: "all 0.2s ease",
                  "&:hover": {
                    background: "#fff",
                    boxShadow: "0 0 30px rgba(0, 255, 156, 0.3)"
                  }
                }}
              >
                ACCESS_TERMINAL
              </Button>
            </Stack>
          )}

          {/* Mobile Menu Toggle */}
          {isMobile && (
            <Stack direction="row" spacing={2} alignItems="center">
               <div className="flex items-center gap-1.5 px-2 py-1 border border-dashed border-[var(--border-subtle)] bg-black/50">
                  <Box sx={{ width: 4, height: 4, background: "var(--primary)", borderRadius: "50%", animation: "pulse 2s infinite" }} />
                  <span className="text-[10px] font-mono text-[var(--primary)]"><Clock /></span>
               </div>
               <IconButton onClick={() => setMobileMenuOpen(true)} sx={{ color: "var(--text-primary)", width: 40, height: 40, border: "1px solid var(--border-subtle)", borderRadius: 0 }}>
                 <Menu size={20} />
               </IconButton>
            </Stack>
          )}
        </Toolbar>
      </AppBar>

      <Drawer
        anchor="right"
        open={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
        PaperProps={{
          sx: {
            width: "100%",
            maxWidth: "100%",
            background: "#050505",
            borderRadius: 0,
            backgroundImage: "none"
          },
        }}
      >
        <Box sx={{ p: 4, height: "100%", display: "flex", flexDirection: "column" }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 8 }}>
             <Stack direction="row" spacing={1.5} alignItems="center">
                <Terminal size={20} className="text-[var(--primary)]" />
                <Typography sx={{ fontFamily: "var(--font-mono)", fontWeight: 900, letterSpacing: "0.1em", fontSize: "14px", color: "#fff" }}>
                   GRAFT_MENU
                </Typography>
             </Stack>
             <IconButton onClick={() => setMobileMenuOpen(false)} sx={{ color: "var(--text-primary)", border: "1px solid var(--border-subtle)", borderRadius: 0 }}>
               <X size={20} />
             </IconButton>
          </Stack>

          <List sx={{ mb: 6, flex: 1 }}>
            {navLinks.map((link, idx) => (
              <ListItem key={link.href} sx={{ px: 0, py: 2.5, borderBottom: "1px dashed rgba(255,255,255,0.05)" }}>
                <Link href={link.href} onClick={() => setMobileMenuOpen(false)} style={{ textDecoration: "none", width: "100%" }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography sx={{ color: "var(--text-primary)", fontSize: "16px", fontWeight: 800, fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.1em" }}>
                      {link.label}
                    </Typography>
                    <Box sx={{ color: "var(--text-faint)", fontSize: "10px", fontFamily: "var(--font-mono)" }}>0{idx + 1}</Box>
                  </Stack>
                </Link>
              </ListItem>
            ))}
          </List>

          <Box sx={{ p: 3, border: "1px dashed var(--border-subtle)", background: "rgba(255,255,255,0.02)", mb: 4 }}>
             <Typography sx={{ fontSize: "9px", color: "var(--primary)", fontFamily: "var(--font-mono)", fontWeight: 900, mb: 1.5, letterSpacing: "0.2em" }}>
                // KERNEL_STATS
             </Typography>
             <Stack spacing={1}>
                <Typography sx={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>NODE: GRAFT_PRIMARY</Typography>
                <Typography sx={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>LATENCY: 0.12MS</Typography>
                <Typography sx={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>LOAD: OPTIMIZED</Typography>
             </Stack>
          </Box>

          <Button
            component={Link}
            href="/login"
            fullWidth
            onClick={() => setMobileMenuOpen(false)}
            sx={{
              background: "var(--primary)",
              color: "#000",
              fontFamily: "var(--font-mono)",
              fontWeight: 900,
              fontSize: "13px",
              borderRadius: "0",
              py: 2,
              letterSpacing: "0.1em"
            }}
          >
            INITIATE_SESSION()
          </Button>
        </Box>
      </Drawer>
    </>
  );
}
