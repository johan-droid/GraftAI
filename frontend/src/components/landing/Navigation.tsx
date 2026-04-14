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
import Link from "next/link";
import { ArrowRight, CalendarDays, LayoutDashboard, Menu, ShieldCheck, Sparkles, Workflow, X } from "lucide-react";

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
          borderRadius: 2,
          border: "1px solid rgba(255,255,255,0.08)",
          background: "linear-gradient(180deg, rgba(0,255,156,0.12), rgba(255,255,255,0.02))",
          boxShadow: "0 12px 36px rgba(0,0,0,0.28)",
        }}
      >
        <Sparkles size={18} color="var(--primary)" />
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
        <Typography sx={{ fontSize: 11, color: "var(--text-muted)" }}>Scheduling that stays readable</Typography>
      </Box>
    </Stack>
  );
}

export function Navigation() {
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
        sx={{
          zIndex: 1200,
          background: scrolled ? "rgba(7, 10, 14, 0.92)" : "rgba(7, 10, 14, 0.72)",
          backdropFilter: "blur(18px)",
          borderBottom: "1px solid rgba(255,255,255,0.08)",
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
                      fontSize: 13,
                      fontWeight: 600,
                      px: 1.5,
                      minWidth: "auto",
                      "&:hover": { color: "var(--text-primary)", background: "rgba(255,255,255,0.04)" },
                    }}
                  >
                    {link.label}
                  </Button>
                ))}

                <Divider orientation="vertical" flexItem sx={{ mx: 1.5, borderColor: "rgba(255,255,255,0.08)" }} />

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
                  href="/profile/setup"
                  variant="contained"
                  endIcon={<ArrowRight size={16} />}
                  sx={{
                    borderRadius: 999,
                    px: 2.25,
                    py: 1.1,
                    background: "linear-gradient(90deg, var(--primary), var(--secondary))",
                    color: "#04110b",
                    fontWeight: 800,
                    textTransform: "none",
                    boxShadow: "none",
                    "&:hover": { boxShadow: "0 10px 24px rgba(0,255,156,0.14)" },
                  }}
                >
                  Start setup
                </Button>
              </Stack>
            )}

            {isMobile && (
              <Stack direction="row" alignItems="center" spacing={1}>
                <Button
                  component={Link}
                  href="/profile/setup"
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
                  }}
                >
                  Start
                </Button>
                <IconButton
                  onClick={() => setMobileMenuOpen(true)}
                  sx={{
                    color: "var(--text-primary)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: 2,
                    background: "rgba(255,255,255,0.03)",
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
            background: "#070A0F",
            borderLeft: "1px solid rgba(255,255,255,0.08)",
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
              href="/profile/setup"
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
              }}
            >
              Continue setup
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
