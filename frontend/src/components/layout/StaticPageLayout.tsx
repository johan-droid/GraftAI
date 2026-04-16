"use client";

import { Box, Container, Typography, alpha, Stack, Breadcrumbs } from "@mui/material";
import { motion } from "framer-motion";
import Link from "next/link";
import { ChevronRight, Home, ArrowLeft } from "lucide-react";
import { Navigation } from "@/components/landing/Navigation";
import { Footer } from "@/components/landing/Footer";
import DotField from "@/components/landing/DotField";
import "@/components/landing/DotField.css";

interface StaticPageLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
  lastUpdated?: string;
  breadcrumb?: { label: string; href: string }[];
}

export function StaticPageLayout({ 
  children, 
  title, 
  subtitle, 
  lastUpdated,
  breadcrumb = []
}: StaticPageLayoutProps) {
  return (
    <Box sx={{ bgcolor: "var(--bg-base)", minHeight: "100vh", position: "relative" }}>
      {/* Dynamic Background components from Landing */}
      <Box sx={{ position: "fixed", inset: 0, zIndex: 0, opacity: 0.4, pointerEvents: "none" }}>
        <DotField />
      </Box>
      
      <Box
        sx={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          height: "100vh",
          zIndex: 0,
          overflow: "hidden",
          pointerEvents: "none",
        }}
      >
        <motion.div
            animate={{
              x: [0, 40, 0],
              y: [0, 20, 0],
              opacity: [0.03, 0.05, 0.03]
            }}
            transition={{
              duration: 20,
              repeat: Infinity,
              ease: "linear",
            }}
            style={{
              position: "absolute",
              top: "-10%",
              left: "-10%",
              width: "40%",
              height: "40%",
              background: "radial-gradient(circle, var(--brand-primary) 0%, transparent 70%)",
              filter: "blur(100px)",
            }}
          />
       </Box>

      <Navigation />

      <Container maxWidth="md" sx={{ pt: { xs: 16, md: 24 }, pb: 20, position: "relative", zIndex: 1 }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        >
          {/* Breadcrumbs & Status Bar */}
          <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 6 }}>
             <Link href="/" style={{ 
                display: "flex", 
                alignItems: "center", 
                gap: 8, 
                color: "var(--text-muted)", 
                textDecoration: "none",
                fontSize: 12,
                fontFamily: "var(--font-mono)",
                textTransform: "uppercase",
                letterSpacing: "0.1em"
             }}>
                <ArrowLeft size={14} /> Back to Base
             </Link>
             <Divider orientation="vertical" flexItem sx={{ height: 12, my: "auto", borderColor: "var(--border-subtle)" }} />
             <Box sx={{ 
                px: 1.5, 
                py: 0.5, 
                bgcolor: "rgba(0, 255, 156, 0.05)", 
                border: "1px solid rgba(0, 255, 156, 0.1)",
                borderRadius: 1,
                fontSize: 10,
                color: "var(--primary)",
                fontFamily: "var(--font-mono)",
                fontWeight: 700
             }}>
                SECURE_DOC_v1.0
             </Box>
          </Stack>

          <Stack spacing={1} sx={{ mb: 8 }}>
            <Typography
              variant="h1"
              sx={{
                fontSize: { xs: 32, md: 48 },
                fontWeight: 900,
                letterSpacing: "-0.04em",
                color: "var(--text-primary)",
                fontFamily: "var(--font-sans)"
              }}
            >
              {title}
            </Typography>
            {subtitle && (
              <Typography
                sx={{
                  color: "var(--text-muted)",
                  fontSize: { xs: 16, md: 18 },
                  fontFamily: "var(--font-mono)",
                  textTransform: "uppercase",
                  letterSpacing: "0.1em"
                }}
              >
                {subtitle}
              </Typography>
            )}
            {lastUpdated && (
               <Typography
                sx={{
                  color: "var(--text-faint)",
                  fontSize: 12,
                  fontFamily: "var(--font-mono)",
                  mt: 2
                }}
              >
                Last Synchronized: {lastUpdated}
              </Typography>
            )}
          </Stack>

          <Box className="refined-glass" sx={{ 
            p: { xs: 4, md: 8 }, 
            borderRadius: 2,
            border: "1px solid var(--border-subtle)",
            position: "relative",
            overflow: "hidden"
          }}>
             {/* Technical Corner Tags */}
             <Box sx={{ position: "absolute", top: 0, left: 0, width: 20, height: 20, borderTop: "2px solid var(--primary)", borderLeft: "2px solid var(--primary)" }} />
             <Box sx={{ position: "absolute", bottom: 0, right: 0, width: 20, height: 20, borderBottom: "2px solid var(--primary)", borderRight: "2px solid var(--primary)" }} />

             <Box sx={{ 
                color: "var(--text-secondary)", 
                lineHeight: 1.8,
                "& h3": { 
                    color: "var(--text-primary)", 
                    fontSize: 20, 
                    mt: 6, 
                    mb: 3, 
                    fontFamily: "var(--font-sans)",
                    fontWeight: 700 
                },
                "& p": { mb: 3 },
                "& ul": { mb: 4, pl: 3, listStyle: "square" },
                "& li": { mb: 1.5 },
                "& strong": { color: "var(--text-primary)", fontWeight: 700 }
             }}>
                {children}
             </Box>
          </Box>
        </motion.div>
      </Container>
      
      <Footer />
    </Box>
  );
}

const Divider = ({ orientation = "horizontal", flexItem, sx }: any) => (
    <Box sx={{ ...sx, borderLeft: orientation === "vertical" ? "1px solid" : "none", borderTop: orientation === "horizontal" ? "1px solid" : "none" }} />
);
