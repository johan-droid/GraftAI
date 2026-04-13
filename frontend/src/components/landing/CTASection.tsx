"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Box, Typography, Container, TextField, Stack } from "@mui/material";
import { motion } from "framer-motion";
import { ArrowRight, Terminal, Activity, Zap, ShieldAlert } from "lucide-react";

export function CTASection() {
  const router = useRouter();

  return (
    <Box
      sx={{
        py: { xs: 12, md: 24 },
        background: "#050505",
        position: "relative",
        overflow: "hidden",
        borderTop: "1px dashed var(--border-subtle)"
      }}
    >
      {/* Background grid line decoration */}
      <Box sx={{ position: "absolute", top: 0, left: "10%", width: "1px", height: "100%", background: "var(--border-subtle)", opacity: 0.2 }} />
      <Box sx={{ position: "absolute", top: 0, right: "10%", width: "1px", height: "100%", background: "var(--border-subtle)", opacity: 0.2 }} />

      <Container maxWidth="lg" sx={{ position: "relative", zIndex: 1 }}>
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <Box sx={{ border: "1px dashed var(--border-subtle)", p: { xs: 4, md: 10 }, background: "rgba(255,255,255,0.01)", position: "relative" }}>
             {/* Decorative Corner Trace */}
             <div className="absolute top-0 left-0 w-3 h-3 border-t-2 border-l-2 border-[var(--primary)]" />
             <div className="absolute bottom-0 right-0 w-3 h-3 border-b-2 border-r-2 border-[var(--primary)]" />
             
             <Stack direction={{ xs: "column", md: "row" }} spacing={8} alignItems="center">
                <Box sx={{ flex: 1, textAlign: { xs: "center", md: "left" } }}>
                   <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 4, justifyContent: { xs: "center", md: "flex-start" } }}>
                      <Zap size={16} className="text-[var(--primary)]" />
                      <Typography sx={{ color: "var(--primary)", fontSize: "10px", fontWeight: 900, fontFamily: "var(--font-mono)", letterSpacing: "0.3em" }}>
                         // FINAL_SYNC_PROTOCOL
                      </Typography>
                   </Stack>

                   <Typography
                     variant="h2"
                     sx={{
                       fontWeight: 900,
                       mb: 4,
                       fontSize: { xs: "2.5rem", md: "4.5rem" },
                       fontFamily: "var(--font-mono)",
                       lineHeight: 0.95,
                       letterSpacing: "-0.05em",
                       textTransform: "uppercase",
                       color: "#fff"
                     }}
                   >
                     Ready to <Box component="span" sx={{ color: "var(--primary)" }}>Hard-Fork</Box> Your Schedule?
                   </Typography>

                   <Typography sx={{ color: "var(--text-faint)", mb: 6, fontSize: "13px", fontFamily: "var(--font-mono)", textTransform: "uppercase", lineHeight: 1.8, maxWidth: 500 }}>
                     Join the distributed network of high-performance operators. Initializing session takes less than 30 seconds.
                   </Typography>

                   <Box sx={{ display: "flex", flexDirection: { xs: "column", sm: "row" }, gap: 3, justifyContent: { xs: "center", md: "flex-start" } }}>
                      <button
                        onClick={() => router.push("/onboarding")}
                        className="px-10 py-5 bg-[var(--primary)] text-black text-[11px] font-black font-mono tracking-[0.3em] uppercase hover:bg-white transition-all relative group overflow-hidden"
                      >
                         <span className="relative z-10 flex items-center justify-center gap-3">
                            INITIALIZE_SESSION() <ArrowRight size={18} />
                         </span>
                         <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                      </button>

                      <button
                        onClick={() => router.push("/contact")}
                        className="px-10 py-5 border border-dashed border-[var(--border-subtle)] text-[#fff] text-[11px] font-black font-mono tracking-[0.3em] uppercase hover:border-[var(--primary)] hover:text-[var(--primary)] transition-all bg-transparent"
                      >
                         TALK_TO_KERNEL_DEV
                      </button>
                   </Box>
                </Box>

                {/* Technical Sidebar decoration */}
                <Box sx={{ width: { xs: "100%", md: "300px" }, borderLeft: { md: "1px dashed var(--border-subtle)" }, pl: { md: 6 }, display: "flex", flexDirection: "column", gap: 4 }}>
                   {[
                      { icon: Activity, label: "SYS_UPTIME", val: "99.999%" },
                      { icon: Terminal, label: "SYNC_LAT", val: "< 50MS" },
                      { icon: ShieldAlert, label: "SEC_INDEX", val: "CRITICAL_MAX" }
                   ].map((item, i) => (
                      <Stack key={i} direction="row" spacing={3} alignItems="center">
                         <Box sx={{ width: 40, height: 40, border: "1px solid var(--border-subtle)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-faint)" }}>
                            <item.icon size={18} />
                         </Box>
                         <div>
                            <Typography sx={{ fontSize: "8px", color: "var(--text-faint)", fontWeight: 900, fontFamily: "var(--font-mono)" }}>{item.label}</Typography>
                            <Typography sx={{ fontSize: "13px", color: "#fff", fontWeight: 900, fontFamily: "var(--font-mono)" }}>{item.val}</Typography>
                         </div>
                      </Stack>
                   ))}
                </Box>
             </Stack>
          </Box>

          <Box sx={{ mt: 8, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
             <Typography sx={{ fontSize: "8px", color: "var(--text-faint)", fontFamily: "var(--font-mono)", fontWeight: 800 }}>
                NODE_ENCRYPTION_ACTIVE // GRAFT_0.82_BETA
             </Typography>
             <div className="flex gap-2">
                <div className="w-1 h-1 bg-[var(--primary)]" />
                <div className="w-1 h-1 bg-[var(--primary)] opacity-50" />
                <div className="w-1 h-1 bg-[var(--primary)] opacity-20" />
             </div>
          </Box>
        </motion.div>
      </Container>
    </Box>
  );
}
