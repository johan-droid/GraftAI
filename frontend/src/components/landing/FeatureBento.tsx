"use client";

import { Box, Typography, Container, Grid, Stack } from "@mui/material";
import { motion } from "framer-motion";
import { 
  MemoryStick, 
  Binary, 
  ShieldCheck, 
  Workflow, 
  Terminal, 
  Cpu,
  Unplug,
  Box as BoxIcon,
  Activity,
  Layers
} from "lucide-react";

const features = [
  {
    icon: MemoryStick,
    title: "AI_SEMANTIC_MEMORY",
    tag: "[VECTOR_STORE]",
    description: "Transforms calendar data into high-dimensional embeddings. GraftAI remembers context across platforms, allowing for truly intelligent scheduling decisions.",
    id: "01"
  },
  {
    icon: Workflow,
    title: "DISTRIBUTED_QUEUE",
    tag: "[REDIS_ARQ]",
    description: "Reliable background processing for syncs, notifications, and heavy lifting. Zero-latency UI with distributed worker nodes.",
    id: "02"
  },
  {
    icon: ShieldCheck,
    title: "HMAC_VALIDATION",
    tag: "[SEC_PROTOCOL]",
    description: "Enterprise-grade security for Google and MS Graph notifications. All incoming payloads are validated via cryptographic signatures.",
    id: "03"
  },
  {
    icon: Binary,
    title: "SLOT_FINDER_V3",
    tag: "[CACHE_LAYER]",
    description: "Optimized slot-finding algorithm with intelligent caching. Handles peak loads with <50ms response times for slot lookups.",
    id: "04"
  },
  {
    icon: Unplug,
    title: "EDGE_RESILIENCE",
    tag: "[PWA_PROTO]",
    description: "Full offline support via Serwist. Schedule while on a plane; we'll resync the moment you're back at the edge.",
    id: "05"
  },
  {
    icon: BoxIcon,
    title: "MICRO_INTEGRATIONS",
    tag: "[JSON_API]",
    description: "A developer-first API designed to be grafted onto any codebase. Simple, predictable, and fully typed.",
    id: "06"
  },
];

function FeatureCard({ feature, index }: { feature: typeof features[0], index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      transition={{ duration: 0.4, delay: index * 0.05 }}
      viewport={{ once: true }}
      style={{ height: "100%" }}
    >
      <Box
        sx={{
          height: "100%",
          p: 5,
          background: "rgba(255,255,255,0.01)",
          borderRight: "1px dashed var(--border-subtle)",
          borderBottom: "1px dashed var(--border-subtle)",
          position: "relative",
          overflow: "hidden",
          transition: "all 0.2s ease",
          "&:hover": {
            background: "rgba(0, 255, 156, 0.03)",
            "& .feature-icon": { color: "var(--primary)", transform: "scale(1.1)" },
            "& .feature-id": { color: "var(--primary)" }
          },
        }}
      >
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
           <Typography className="feature-id" sx={{ fontSize: "10px", fontFamily: "var(--font-mono)", color: "var(--text-faint)", fontWeight: 900 }}>
              [{feature.id}]
           </Typography>
           <feature.icon size={18} className="feature-icon text-[var(--text-faint)] transition-all" />
        </Stack>

        <Typography
          sx={{
            fontFamily: "var(--font-mono)",
            fontWeight: 900,
            mb: 2,
            fontSize: "14px",
            color: "#fff",
            textTransform: "uppercase",
            letterSpacing: "0.05em"
          }}
        >
          {feature.title}
        </Typography>

        <Typography sx={{ color: "var(--primary)", fontSize: "9px", fontFamily: "var(--font-mono)", fontWeight: 800, mb: 3, letterSpacing: "0.1em" }}>
           ID_TYPE: {feature.tag}
        </Typography>
        
        <Typography
          sx={{
            color: "var(--text-faint)",
            fontSize: "11px",
            fontFamily: "var(--font-mono)",
            lineHeight: 1.8,
            textTransform: "uppercase"
          }}
        >
          {feature.description}
        </Typography>

        {/* Decorative elements */}
        <Box sx={{ position: "absolute", bottom: 8, right: 8, opacity: 0.1 }}>
           <Layers size={40} />
        </Box>
      </Box>
    </motion.div>
  );
}

export function FeatureBento() {
  return (
    <Box sx={{ py: { xs: 10, md: 20 }, background: "#050505", borderTop: "1px dashed var(--border-subtle)" }}>
      <Container maxWidth="xl">
        {/* Header */}
        <Box sx={{ mb: 12 }}>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
          >
            <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
              <div className="w-4 h-[1px] bg-[var(--primary)]" />
              <Typography
                sx={{
                  fontSize: "11px",
                  fontFamily: "var(--font-mono)",
                  color: "var(--primary)",
                  letterSpacing: "0.4em",
                  fontWeight: 900,
                  textTransform: "uppercase",
                }}
              >
                Architecture_Overview
              </Typography>
            </Stack>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: "2.5rem", md: "4.5rem" },
                fontWeight: 900,
                fontFamily: "var(--font-mono)",
                maxWidth: "1000px",
                lineHeight: 0.9,
                letterSpacing: "-0.05em",
                color: "#fff",
                textTransform: "uppercase"
              }}
            >
              The Most <Box component="span" sx={{ color: "var(--primary)" }}>Aggressive</Box> <br />
              Scheduling Engine Ever Built.
            </Typography>
          </motion.div>
        </Box>

        {/* Technical Grid Overlay */}
        <Box sx={{ borderTop: "1px dashed var(--border-subtle)", borderLeft: "1px dashed var(--border-subtle)" }}>
            <Grid container spacing={0}>
              {features.map((feature, idx) => (
                <Grid item xs={12} sm={6} md={4} key={idx}>
                  <FeatureCard feature={feature} index={idx} />
                </Grid>
              ))}
            </Grid>
        </Box>

        <Box sx={{ mt: 12, p: 4, border: "1px dashed var(--border-subtle)", background: "rgba(255,255,255,0.01)" }}>
           <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" alignItems="center" spacing={4}>
              <Stack direction="row" spacing={3} alignItems="center">
                <Activity size={16} className="text-[var(--primary)] animate-pulse" />
                <Typography sx={{ color: "var(--text-faint)", fontSize: "10px", fontFamily: "var(--font-mono)", fontWeight: 900, letterSpacing: "0.1em" }}>
                  [ NODE_INTEGRITY: 100% // CLUSTER_STATUS: NOMINAL ]
                </Typography>
              </Stack>
              <Typography sx={{ color: "var(--text-faint)", fontSize: "9px", fontFamily: "var(--font-mono)", fontStyle: "italic", textTransform: "uppercase" }}>
                 // Distributed Execution Protocol v.3.0.82_STABLE
              </Typography>
           </Stack>
        </Box>
      </Container>
    </Box>
  );
}
