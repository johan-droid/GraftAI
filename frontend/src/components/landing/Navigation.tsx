"use client";

import { useEffect, useState } from "react";
import {
  AppBar,
  Box,
  Button,
  Container,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  Stack,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { ArrowRight, CalendarDays, LayoutDashboard, Menu, ShieldCheck, Sparkles, Workflow, X, LogOut, User } from "lucide-react";
import { useSession } from "next-auth/react";
import Link from "next/link";

const navLinks = [
  { label: "Product", href: "#product" },
  { label: "Workflow", href: "#workflow" },
  { label: "Security", href: "#security" },
  { label: "Pricing", href: "#pricing" },
];

function BrandMark() {
  return (
    <Stack direction="row" spacing={1.5} alignItems="center">
      <Box
        sx={{
          width: 38,
          height: 38,
          display: "grid",
          placeItems: "center",
          borderRadius: 2.5,
          border: "1px solid var(--border-subtle)",
          background: "linear-gradient(180deg, var(--bg-surface), var(--bg-base))",
          boxShadow: "var(--shadow-card)",
        }}
      >
        <Sparkles size={18} color="var(--brand-primary)" />
      </Box>
      <Box>
        <Typography
          sx={{
            fontFamily: "var(--font-jakarta)",
            fontSize: 15,
            fontWeight: 800,
            letterSpacing: "-0.03em",
            color: "var(--text-primary)",
          }}
        >
          GraftAI
        </Typography>
        <Typography sx={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-sans)", fontWeight: 500 }}>Smart scheduling for modern teams</Typography>
      </Box>
    </Stack>
  );
}

export function Navigation() {
  const { status } = useSession();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 12);
    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <>
      <AppBar
        position="fixed"
        elevation={0}
        className={`glass-nav ${scrolled ? "scrolled" : ""}`}
        sx={{
          zIndex: 1200,
          background: "transparent",
          backdropFilter: "none",
          borderBottom: "none",
        }}
      >
        <Toolbar sx={{ minHeight: { xs: 68, md: 76 }, px: { xs: 2, md: 4 } }}>
          <Container
            maxWidth="xl"
            disableGutters
            sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 2 }}
          >
            <Box component={Link} href="/" sx={{ textDecoration: "none", color: "inherit" }}>
              <BrandMark />
            </Box>

            {!isMobile && (
              <Stack direction="row" alignItems="center" spacing={1}>
                {navLinks.map((link) => (
                  <Button
                    key={link.href}
                    component={Link}
                    href={link.href}
                    variant="text"
                     sx={{
                      color: "var(--text-secondary)",
                      textTransform: "none",
                      fontSize: 14,
                      fontWeight: 500,
                      px: 2,
                      minWidth: "auto",
                      borderRadius: 99,
                      "&:hover": { color: "var(--brand-primary)", background: "var(--bg-surface)" },
                    }}
                  >
                    {link.label}
                  </Button>
                ))}

                 <Divider orientation="vertical" flexItem sx={{ mx: 1.5, borderColor: "var(--border-subtle)" }} />

                {status === "authenticated" ? (
                  <Stack direction="row" spacing={1}>
                    <Button
                      component={Link}
                      href="/dashboard"
                      variant="text"
                      startIcon={<LayoutDashboard size={14} />}
                      sx={{ color: "var(--text-secondary)", textTransform: "none", fontWeight: 600 }}
                    >
                      Dashboard
                    </Button>
                    <Button
                      component={Link}
                      href="/signout"
                      variant="text"
                      startIcon={<LogOut size={14} />}
                      sx={{ 
                        color: "var(--text-muted)", 
                        textTransform: "none", 
                        fontWeight: 500,
                        "&:hover": { color: "var(--accent)" }
                      }}
                    >
                      Log out
                    </Button>
                  </Stack>
                ) : (
                  <>
                    <Button
                      component={Link}
                      href="/login"
                      variant="text"
                      sx={{ color: "var(--text-secondary)", textTransform: "none", fontWeight: 600 }}
                    >
                      Log in
                    </Button>

                    <Button
                      component={Link}
                      href="/signup"
                      variant="contained"
                      endIcon={<ArrowRight size={16} />}
                      sx={{
                        background: "var(--brand-primary)",
                        color: "white",
                        fontWeight: 700,
                        textTransform: "none",
                        boxShadow: "none",
                        borderRadius: 99,
                        px: 3,
                        fontFamily: "var(--font-sans)",
                        transition: "all 0.2s ease",
                        "&:hover": { background: "var(--brand-primary-light)", boxShadow: "var(--shadow-glow)" },
                      }}
                    >
                      Get started
                    </Button>
                  </>
                )}
              </Stack>
            )}

            {isMobile && (
              <Stack direction="row" alignItems="center" spacing={1}>
                <Button
                  component={Link}
                  href="/signup"
                  variant="contained"
                  size="small"
                  sx={{
                    borderRadius: 999,
                    px: 1.8,
                    py: 0.95,
                    background: "linear-gradient(90deg, var(--primary), var(--secondary))",
                    color: "#04110b",
                    fontWeight: 800,
                    textTransform: "none",
                    minWidth: "auto",
                    fontFamily: "var(--font-sans)",
                  }}
                >
                  Start
                </Button>
                <IconButton
                  onClick={() => setMobileMenuOpen(true)}
                   sx={{
                    color: "var(--text-primary)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 2.5,
                    background: "var(--bg-surface)",
                  }}
                  aria-label="Open menu"
                >
                  <Menu size={18} />
                </IconButton>
              </Stack>
            )}
          </Container>
        </Toolbar>
      </AppBar>

      <Drawer
        anchor="right"
        open={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
        PaperProps={{
          sx: {
            width: "100%",
            maxWidth: 360,
             background: "var(--bg-base)",
            borderLeft: "1px solid var(--border-subtle)",
            p: 2.5,
          },
        }}
      >
        <Stack spacing={3} sx={{ height: "100%" }}>
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <BrandMark />
            <IconButton
              onClick={() => setMobileMenuOpen(false)}
              sx={{
                color: "var(--text-primary)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: 2,
              }}
              aria-label="Close menu"
            >
              <X size={18} />
            </IconButton>
          </Stack>

          <Typography sx={{ color: "var(--text-secondary)", fontSize: 14, lineHeight: 1.6 }}>
            One clean flow for profile setup, calendar sync, and booking links.
          </Typography>

          <List disablePadding sx={{ display: "grid", gap: 1 }}>
            {navLinks.map((link, index) => (
              <ListItemButton
                key={link.href}
                component={Link}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                sx={{
                  borderRadius: 3,
                  border: "1px solid rgba(255,255,255,0.06)",
                  background: "rgba(255,255,255,0.02)",
                  py: 1.4,
                  px: 1.8,
                  mb: 1,
                }}
              >
                <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ width: "100%" }}>
                  <Stack direction="row" spacing={1.25} alignItems="center">
                    {index === 0 ? <LayoutDashboard size={16} /> : index === 1 ? <Workflow size={16} /> : index === 2 ? <ShieldCheck size={16} /> : <CalendarDays size={16} />}
                    <Typography sx={{ fontWeight: 700, color: "var(--text-primary)" }}>{link.label}</Typography>
                  </Stack>
                  <ArrowRight size={15} color="var(--text-muted)" />
                </Stack>
              </ListItemButton>
            ))}
          </List>

          <Stack spacing={1.25} sx={{ mt: "auto" }}>
            <Button
              component={Link}
              href="/signup"
              variant="contained"
              fullWidth
              onClick={() => setMobileMenuOpen(false)}
              endIcon={<ArrowRight size={16} />}
              sx={{
                borderRadius: 999,
                py: 1.2,
                background: "linear-gradient(90deg, var(--primary), var(--secondary))",
                color: "#04110b",
                fontWeight: 800,
                textTransform: "none",
                fontFamily: "var(--font-sans)",
              }}
            >
              Get started
            </Button>
            <Button
              component={Link}
              href="/login"
              variant="outlined"
              fullWidth
              onClick={() => setMobileMenuOpen(false)}
              sx={{
                borderRadius: 999,
                py: 1.2,
                borderColor: "rgba(255,255,255,0.12)",
                color: "var(--text-primary)",
                textTransform: "none",
              }}
            >
              Log in
            </Button>
          </Stack>
        </Stack>
      </Drawer>
    </>
  );
}
