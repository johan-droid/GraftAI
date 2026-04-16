"use client";

import { Box, Typography, useMediaQuery, useTheme } from "@mui/material";
import { motion } from "framer-motion";
import { ReactNode } from "react";
import { Sparkles } from "lucide-react";
import Link from "next/link";

interface AuthLayoutProps {
  children: ReactNode;
  title: string;
  subtitle?: string;
}

export function AuthLayout({ children, title, subtitle }: AuthLayoutProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        background: "var(--bg-base)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Technical Grid Overlay */}
      <Box 
        sx={{
          position: "absolute",
          inset: 0,
          background: `
            linear-gradient(rgba(0, 255, 156, 0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 156, 0.02) 1px, transparent 1px)
          `,
          backgroundSize: "48px 48px",
          pointerEvents: "none",
        }}
      />

      {/* Left Side - Visual Showcase (hidden on mobile) */}
      {!isMobile && (
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            padding: 80,
            borderRight: "1px dashed var(--border-subtle)",
            position: "relative",
            background: "rgba(0, 0, 0, 0.4)",
            backdropFilter: "blur(4px)",
          }}
        >
          {/* Scanline Effect */}
          <Box className="scanline" sx={{ opacity: 0.05 }} />

          <Box sx={{ position: "relative", zIndex: 1 }}>
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.5 }}
            >
              <div className="flex items-center gap-4 mb-8">
                <Box
                  sx={{
                    width: 64,
                    height: 64,
                    borderRadius: 0,
                    background: "var(--bg-elevated)",
                    border: "1px solid var(--primary)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    boxShadow: "0 0 20px rgba(0, 255, 156, 0.15)",
                  }}
                >
                  <Sparkles size={32} className="text-primary" />
                </Box>
                <div className="flex flex-col">
                   <div className="text-[10px] font-black text-[var(--primary)] uppercase tracking-[0.3em]">System_Core_v0.1</div>
                   <div className="text-[24px] font-black text-white uppercase tracking-tighter">GRAFT_AI</div>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.5 }}
            >
              <Typography
                className="handwriting-heading"
                sx={{
                  fontSize: { xs: "2.25rem", md: "3.5rem" },
                  fontWeight: 900,
                  color: "var(--text-primary)",
                  textTransform: "uppercase",
                  letterSpacing: "-0.04em",
                  mb: 4,
                  lineHeight: 1,
                  maxWidth: "540px"
                }}
              >
                SECURE_GATEWAY_ACCESS
              </Typography>
              <div className="handwriting-underline" aria-hidden="true" />
            </motion.div>

            <div className="space-y-6 max-w-md">
              <div className="p-4 border border-dashed border-[var(--border-subtle)] bg-black/50 font-mono text-[11px] leading-relaxed text-[var(--text-muted)]">
                <div className="text-[var(--primary)] mb-2 font-black tracking-widest uppercase">{"// SYS_INITIALIZATION"}</div>
                &gt; BOOTING_CORTEX_MODULES... [OK]<br/>
                &gt; ESTABLISHING_VECTOR_PIPELINES... [OK]<br/>
                &gt; AUTHENTICATING_AUTH_NODE_07... [PENDING]
              </div>

              <div className="flex flex-wrap gap-3">
                {["AES_256", "OAUTH_2.0", "RSA_GEN"].map((tag) => (
                  <div key={tag} className="px-3 py-1 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[9px] font-black text-[var(--text-faint)] tracking-widest uppercase">
                    {tag}
                  </div>
                ))}
              </div>
            </div>
          </Box>

          <div className="absolute bottom-12 left-12 font-mono text-[9px] text-[var(--text-faint)] tracking-widest uppercase opacity-40">
            <span>{`[ GRAFT_OS_X // KERNEL: 5.4.0-HARDENED // REG_NODE: ${title.toUpperCase()} ]`}</span>
                <Box
                  component="h2"
                  className="handwriting-heading"
                  sx={{
                    fontSize: { xs: "1.5rem", md: "2rem" },
                    fontWeight: 900,
                    color: "var(--text-primary)",
                    textTransform: "uppercase",
                    mb: 1.5,
                    letterSpacing: "-0.02em",
                  }}
                >
                  {title.replace(/ /g, "_")}
                </Box>
          </div>
        </motion.div>
      )}

      {/* Right Side - Form */}
      <Box
        sx={{
          flex: isMobile ? 1 : 0.6,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          p: { xs: 3, sm: 4, md: 6 },
          position: "relative",
          zIndex: 1,
        }}
      >
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          style={{ width: "100%", maxWidth: 1000 }}
        >
          <Box sx={{ maxWidth: 440, mx: "auto" }}>
            {/* Form Header */}
            <Box sx={{ mb: 8 }}>
              <div className="flex items-center gap-3 mb-4">
                 <div className="w-8 h-[1px] bg-[var(--primary)]" />
                 <div className="text-[9px] font-black text-primary tracking-[.4em] uppercase font-mono">Permission_Protocol</div>
              </div>
              <Box
                component="h2"
                sx={{
                  fontSize: "2rem",
                  fontWeight: 900,
                  color: "var(--text-primary)",
                  fontFamily: "var(--font-mono)",
                  textTransform: "uppercase",
                  mb: 1.5,
                  letterSpacing: "-0.02em",
                }}
              >
                {title.replace(/ /g, "_")}
              </Box>
              {subtitle && (
                <Box
                  component="p"
                  sx={{
                    fontSize: "12px",
                    color: "var(--text-muted)",
                    fontFamily: "var(--font-mono)",
                    textTransform: "uppercase",
                    fontWeight: 600,
                    letterSpacing: "0.05em",
                  }}
                >
                  {subtitle}
                </Box>
              )}
            </Box>

            <Box className="refined-glass" sx={{ 
              p: { xs: 4, md: 8 }, 
              position: "relative",
              borderRadius: 2,
              border: "1px solid var(--border-subtle)",
              overflow: "hidden"
            }}>
               {/* Decorative corner tags */}
               <Box 
                sx={{ 
                  position: "absolute", top: 0, left: 0, width: 12, height: 12, 
                  borderTop: "2px solid var(--primary)", borderLeft: "2px solid var(--primary)" 
                }} 
              />
               <Box 
                sx={{ 
                  position: "absolute", bottom: 0, right: 0, width: 12, height: 12, 
                  borderBottom: "2px solid var(--primary)", borderRight: "2px solid var(--primary)" 
                }} 
              />
               
              {children}
            </Box>

            {/* Footer */}
            <Box sx={{ mt: 8, textAlign: "center", pt: 6, borderTop: "1px dashed var(--border-subtle)" }}>
              <Box
                component="p"
                sx={{
                  fontSize: "9px",
                  color: "var(--text-faint)",
                  fontFamily: "var(--font-mono)",
                  textTransform: "uppercase",
                  letterSpacing: "0.2em",
                }}
              >
                [ SYS_INTEGRITY_VERIFIED ]
              </Box>
              <div className="mt-4 flex justify-center gap-6 opacity-60">
                <Link
                  href="/terms"
                  style={{
                    fontSize: "9px",
                    color: "var(--text-muted)",
                    textDecoration: "none",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 800,
                  }}
                >
                  PROTOCOL_A
                </Link>
                <Link
                  href="/privacy"
                  style={{
                    fontSize: "9px",
                    color: "var(--text-muted)",
                    textDecoration: "none",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 800,
                  }}
                >
                  PROTOCOL_B
                </Link>
              </div>
            </Box>
          </Box>
        </motion.div>
      </Box>
    </Box>
  );
}
