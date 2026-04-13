"use client";

import { Box, Typography, Container, Grid, Stack, useMediaQuery, useTheme } from "@mui/material";
import { motion } from "framer-motion";
import { Check, X, Shield, Zap, Target, Database, Activity } from "lucide-react";

const features = [
  { name: "AI_SCHEDULING_ENGINE", graftai: true, calendly: false, reclaim: true, motion: true },
  { name: "NL_INPUT_PARSER", graftai: true, calendly: false, reclaim: false, motion: false },
  { name: "FOCUS_TIME_PROTOCOL", graftai: true, calendly: false, reclaim: true, motion: true },
  { name: "VECTOR_SYNC_V3", graftai: true, calendly: true, reclaim: true, motion: true },
  { name: "NODE_COORDINATION", graftai: true, calendly: true, reclaim: true, motion: true },
  { name: "METRIC_ANALYTICS", graftai: true, calendly: false, reclaim: true, motion: false },
  { name: "CUSTOM_KERNEL_LOGS", graftai: true, calendly: false, reclaim: false, motion: false },
  { name: "OPEN_API_ACCESS", graftai: true, calendly: false, reclaim: false, motion: false },
];

function FeatureStatus({ value }: { value: boolean | string }) {
  if (typeof value === "string") {
    return (
      <Typography sx={{ color: "var(--primary)", fontSize: "10px", fontFamily: "var(--font-mono)", fontWeight: 900 }}>
        {value}
      </Typography>
    );
  }
  return value ? (
    <Check size={16} className="text-[var(--primary)]" />
  ) : (
    <X size={16} className="text-[var(--text-faint)] opacity-30" />
  );
}

export function Comparison() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  return (
    <Box sx={{ py: { xs: 10, md: 20 }, background: "var(--bg-base)" }}>
      <Container maxWidth="xl">
        {/* Header */}
        <Box sx={{ mb: { xs: 8, md: 12 } }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
          >
             <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
               <Target size={14} className="text-[var(--primary)]" />
               <Typography className="telemetry-text">[ CAPABILITY_REGISTRY_V2 ]</Typography>
            </Stack>
            <Typography
              variant="h2"
              sx={{ 
                fontSize: { xs: "2rem", sm: "3rem", md: "4rem" }, 
                fontWeight: 900, 
                fontFamily: "var(--font-mono)",
                letterSpacing: "-0.05em",
                color: "var(--text-primary)",
                textTransform: "uppercase",
                maxWidth: 900
              }}
            >
              Outperform Legacy <Box component="span" sx={{ color: "var(--text-faint)" }}>Infrastructures</Box>.
            </Typography>
          </motion.div>
        </Box>

        {isMobile ? (
          /* Mobile View: Vertical Stacking Modules */
          <Stack spacing={3}>
            {features.map((feature, idx) => (
              <Box 
                key={idx}
                sx={{ 
                  p: 3, 
                  background: "rgba(255,255,255,0.02)", 
                  border: "1px dashed var(--border-subtle)",
                }}
              >
                <Typography sx={{ color: "var(--primary)", fontSize: "11px", fontFamily: "var(--font-mono)", fontWeight: 900, mb: 3 }}>
                  // {feature.name}
                </Typography>
                <Grid container spacing={2}>
                  {[
                    { label: "GRAFT_AI", value: feature.graftai, primary: true },
                    { label: "LEGACY_S1", value: feature.calendly },
                    { label: "LEGACY_S2", value: feature.reclaim },
                    { label: "LEGACY_S3", value: feature.motion },
                  ].map((sys, sysIdx) => (
                    <Grid item xs={6} key={sysIdx}>
                      <Stack direction="row" spacing={1.5} alignItems="center">
                        <FeatureStatus value={sys.value} />
                        <Typography sx={{ color: sys.primary ? "var(--text-primary)" : "var(--text-faint)", fontSize: "9px", fontFamily: "var(--font-mono)", fontWeight: sys.primary ? 900 : 500 }}>
                          {sys.label}
                        </Typography>
                      </Stack>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            ))}
          </Stack>
        ) : (
          /* Desktop View: Technical Table Manifest */
          <Box sx={{ border: "1px dashed var(--border-subtle)", background: "rgba(255,255,255,0.01)" }}>
            {/* Table Header */}
            <Grid container sx={{ borderBottom: "1px dashed var(--border-subtle)", background: "rgba(0,0,0,0.5)" }}>
              <Grid item md={4} sx={{ p: 3 }}>
                <Typography className="telemetry-text">SYSTEM_CAPABILITY</Typography>
              </Grid>
              {[
                { label: "GRAFT_AI", primary: true },
                { label: "CALENDLY" },
                { label: "RECLAIM" },
                { label: "MOTION" }
              ].map((col, i) => (
                <Grid item md={2} key={i} sx={{ p: 3, textAlign: "center", borderLeft: "1px dashed var(--border-subtle)", background: col.primary ? "rgba(0,255,156,0.03)" : "transparent" }}>
                  <Typography className="telemetry-text" sx={{ color: col.primary ? "var(--primary)" : "var(--text-faint)" }}>
                    {col.label}
                  </Typography>
                </Grid>
              ))}
            </Grid>

            {/* Table Rows */}
            {features.map((feature, idx) => (
              <Grid 
                key={idx} 
                container 
                sx={{ 
                  borderBottom: idx < features.length - 1 ? "1px dashed var(--border-subtle)" : "none",
                  "&:hover": { background: "rgba(255,255,255,0.02)" }
                }}
              >
                <Grid item md={4} sx={{ p: 3 }}>
                  <Typography sx={{ color: "var(--text-primary)", fontSize: "12px", fontFamily: "var(--font-mono)", fontWeight: 800 }}>
                    <span className="text-[var(--primary)] mr-3">#</span> {feature.name}
                  </Typography>
                </Grid>
                {[feature.graftai, feature.calendly, feature.reclaim, feature.motion].map((val, i) => (
                  <Grid item md={2} key={i} sx={{ p: 3, textAlign: "center", borderLeft: "1px dashed var(--border-subtle)", background: i === 0 ? "rgba(0,255,156,0.01)" : "transparent" }}>
                    <FeatureStatus value={val} />
                  </Grid>
                ))}
              </Grid>
            ))}
          </Box>
        )}

        <Box sx={{ mt: 10, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
           <Stack direction="row" spacing={3} alignItems="center">
             <Shield size={14} className="text-[var(--text-faint)]" />
             <Typography className="telemetry-text" sx={{ color: "var(--text-faint)" }}>[ BENCHMARK_VERIFIED_BY_EXTERNAL_AUDIT ]</Typography>
           </Stack>
           <Typography sx={{ fontSize: "10px", color: "var(--primary)", fontFamily: "var(--font-mono)", fontWeight: 900 }}>
             GRAFT_SCORE: 9.8/10
           </Typography>
        </Box>
      </Container>
    </Box>
  );
}
