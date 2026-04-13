"use client";

import { Box, Typography, Container, Grid, Stack } from "@mui/material";
import Link from "next/link";
import { 
  Terminal,
  Activity,
  ShieldAlert,
  Globe,
  Cpu,
  Fingerprint
} from "lucide-react";

const GithubIcon = ({ size = 18 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
  </svg>
);

const footerLinks = {
  engine: {
    title: "// KERNEL_MODULES",
    links: [
      { label: "CORE_API", href: "#" },
      { label: "VECTOR_CACHE", href: "#" },
      { label: "SCHEDULER_V1", href: "#" },
      { label: "SYNC_PIPELINES", href: "#" },
    ],
  },
  dev_hub: {
    title: "// DEVELOPER_ROOT",
    links: [
      { label: "OS_DOCUMENTATION", href: "/docs" },
      { label: "API_SPEC_V3", href: "#" },
      { label: "BUILD_CHANGELOG", href: "#" },
      { label: "SDK_REGISTRY", href: "#" },
    ],
  },
  legal: {
    title: "// SECURITY_PROTOCOLS",
    links: [
      { label: "GDPR_ENFORCEMENT", href: "/privacy" },
      { label: "TERMS_OF_SERVICE", href: "/terms" },
      { label: "SYNC_COMPLIANCE", href: "#" },
    ],
  },
};

export function Footer() {
  return (
    <Box sx={{ background: "#050505", borderTop: "1px dashed var(--border-subtle)", pt: { xs: 8, md: 12 }, pb: 6 }}>
      <Container maxWidth="xl">
        <Grid container spacing={0} sx={{ border: "1px dashed var(--border-subtle)", borderRight: "none", borderBottom: "none" }}>
          {/* Brand Info */}
          <Grid item xs={12} lg={4} sx={{ borderRight: "1px dashed var(--border-subtle)", borderBottom: "1px dashed var(--border-subtle)" }}>
            <Box sx={{ p: 5, background: "rgba(255,255,255,0.01)", height: "100%", position: "relative" }}>
               {/* Decorative corners */}
               <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-[var(--primary)]" />
               <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-[var(--primary)]" />
               
               <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 4 }}>
                 <Box sx={{ p: 1, border: "1px solid var(--primary)", background: "rgba(0, 255, 156, 0.05)" }}>
                   <Terminal size={24} className="text-[var(--primary)]" />
                 </Box>
                 <Typography sx={{ fontWeight: 900, fontFamily: "var(--font-mono)", fontSize: "1.5rem", letterSpacing: "-0.05em", color: "#fff" }}>
                   GRAFT_AI<Box component="span" sx={{ color: "var(--primary)" }}>_</Box>
                 </Typography>
               </Stack>
               <Typography sx={{ color: "var(--text-faint)", mb: 6, fontSize: "10px", fontFamily: "var(--font-mono)", lineHeight: 1.8, textTransform: "uppercase" }}>
                 High-performance scheduling infrastructure. Built for distributed teams and programmable availability. Integrated via kernel-level API protocols.
               </Typography>
               
               <Stack direction="row" spacing={4} alignItems="center">
                  <Link href="https://github.com" target="_blank" style={{ color: "var(--text-faint)" }}>
                    <GithubIcon />
                  </Link>
                  <Stack direction="row" spacing={1} alignItems="center">
                     <Box sx={{ width: 8, height: 8, border: "1px solid var(--primary)", background: "rgba(0,255,156,0.2)" }} />
                     <Typography sx={{ fontSize: "9px", fontFamily: "var(--font-mono)", color: "var(--primary)", fontWeight: 900 }}>SYSTEM_READY</Typography>
                  </Stack>
               </Stack>
            </Box>
          </Grid>

          {/* Link Columns */}
          <Grid item xs={12} lg={8} sx={{ borderRight: "1px dashed var(--border-subtle)", borderBottom: "1px dashed var(--border-subtle)" }}>
            <Grid container spacing={0}>
              {Object.entries(footerLinks).map(([key, section]) => (
                <Grid item xs={12} sm={4} key={key} sx={{ borderRight: { sm: "1px dashed var(--border-subtle)" }, borderBottom: { xs: "1px dashed var(--border-subtle)", sm: "none" } }}>
                  <Box sx={{ p: 5, height: "100%", "&:hover": { background: "rgba(255,255,255,0.01)" } }}>
                    <Typography sx={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--primary)", mb: 4, fontWeight: 900, letterSpacing: "0.2em" }}>
                      {section.title}
                    </Typography>
                    <Stack spacing={2}>
                      {section.links.map((link) => (
                        <Link 
                          key={link.label} 
                          href={link.href} 
                          style={{ textDecoration: "none" }}
                        >
                          <Typography sx={{ 
                            color: "var(--text-faint)", 
                            fontSize: "10px", 
                            fontFamily: "var(--font-mono)",
                            fontWeight: 700,
                            letterSpacing: "0.05em",
                            transition: "all 0.1s ease",
                            display: "flex",
                            alignItems: "center",
                            gap: 1.5,
                            "&:hover": { color: "#fff", transform: "translateX(2px)" }
                          }}>
                            <span className="text-[var(--primary)] opacity-50">{">"}</span> {link.label}
                          </Typography>
                        </Link>
                      ))}
                    </Stack>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </Grid>
        </Grid>

        <Box sx={{ mt: 10, p: 5, border: "1px dashed var(--border-subtle)", background: "rgba(0,0,0,0.5)" }}>
          <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" alignItems={{ xs: "flex-start", md: "center" }} spacing={4}>
            <Stack spacing={1.5}>
              <Typography sx={{ color: "var(--text-faint)", fontSize: "8px", fontFamily: "var(--font-mono)", fontWeight: 900, letterSpacing: "0.2em" }}>
                © 2026 GRAFT_SYSTEMS_INTL // [ LICENSE: ENTERPRISE_PRO ]
              </Typography>
              <div className="flex gap-4">
                <Typography sx={{ color: "var(--text-faint)", fontSize: "8px", fontFamily: "var(--font-mono)", fontWeight: 900 }}>
                  BUILD: <Box component="span" sx={{ color: "var(--primary)" }}>0x82F1A9</Box>
                </Typography>
                <Typography sx={{ color: "var(--text-faint)", fontSize: "8px", fontFamily: "var(--font-mono)", fontWeight: 900 }}>
                  KERNEL: <Box component="span" sx={{ color: "#fff" }}>v.3.0.82</Box>
                </Typography>
              </div>
            </Stack>
            
            <Stack direction={{ xs: "column", sm: "row" }} spacing={5} alignItems={{ xs: "flex-start", sm: "center" }}>
              <Stack direction="row" spacing={1.5} alignItems="center">
                <Activity size={12} className="text-[var(--primary)] animate-pulse" />
                <Typography sx={{ color: "var(--primary)", fontSize: "9px", fontFamily: "var(--font-mono)", fontWeight: 900, letterSpacing: "0.1em" }}>
                  STAT: OPERATIONAL
                </Typography>
              </Stack>
              <Stack direction="row" spacing={1.5} alignItems="center">
                <Fingerprint size={12} className="text-[var(--text-faint)]" />
                <Typography sx={{ color: "var(--text-faint)", fontSize: "9px", fontFamily: "var(--font-mono)", fontWeight: 800 }}>
                  INTEGRITY_INDEX: 1.00
                </Typography>
              </Stack>
              <Stack direction="row" spacing={1.5} alignItems="center">
                <ShieldAlert size={12} className="text-[var(--text-faint)]" />
                <Typography sx={{ color: "var(--text-faint)", fontSize: "9px", fontFamily: "var(--font-mono)", fontWeight: 800 }}>
                  ENCRYPTION: AES_256
                </Typography>
              </Stack>
            </Stack>
          </Stack>
        </Box>
      </Container>
    </Box>
  );
}
