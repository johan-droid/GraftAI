"use client";

import { useState } from "react";
import { Box, Typography, Container, Grid, Stack, Button } from "@mui/material";
import { motion } from "framer-motion";
import { Check, Terminal, Percent, Calculator, Cpu, Shield, Globe, Activity } from "lucide-react";
import Link from "next/link";

const plans = [
  {
    name: "FREE_TIER",
    description: "ENTRY_LEVEL_CORE",
    monthlyPrice: 0,
    yearlyPrice: 0,
    features: [
      "100_EVENTS_PER_CYCLE",
      "BASIC_AI_CORE",
      "EMAIL_NOTIF_HANDLERS",
      "MOBILE_KERNEL_ACCESS",
      "G_CAL_SYNC_PROTOCOL",
    ],
    cta: "INIT_FREE_V1",
    nodeId: "NODE_01",
  },
  {
    name: "PRO_KERNEL",
    description: "DATA_DRIVEN_PROFESSIONAL",
    monthlyPrice: 19,
    yearlyPrice: 15,
    features: [
      "UNLIMITED_EVENT_STREAM",
      "ADVANCED_AI_SCHEDULER",
      "PRIORITY_STACK_SUPPORT",
      "GLOBAL_CAL_SYNC_v3",
      "TEAM_LAYER_UP_TO_5",
      "CUSTOM_WORKFLOW_ENGINE",
      "MEETING_METRIC_ANALYTICS",
      "FOCUS_PROTECTION_DAEMON",
    ],
    cta: "DEPLOY_PRO_STABLE",
    popular: true,
    nodeId: "NODE_02_OP",
  },
  {
    name: "ENTERPRISE_CORE",
    description: "SCALABLE_CLUSTER_LOGIC",
    monthlyPrice: null,
    yearlyPrice: null,
    features: [
      "ALL_PRO_FEATURES_LOADED",
      "UNLIMITED_NODE_CLUSTER",
      "SSO_SAML_AUTH_LAYER",
      "DEDICATED_OPS_SUPPORT",
      "CUSTOM_CLUSTER_INTEGRATION",
      "99.9%_SLA_HANDSHAKE",
      "ADVANCED_LOG_ANALYTICS",
      "API_MASTER_KEY_ACCESS",
    ],
    cta: "CONTACT_CORE_OPS",
    nodeId: "CLUSTER_ROOT",
  },
];

export function Pricing() {
  const [isYearly, setIsYearly] = useState(false);

  return (
    <Box id="pricing" sx={{ py: { xs: 10, md: 20 }, background: "var(--bg-base)", borderTop: "1px dashed var(--border-subtle)" }}>
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
               <Cpu size={14} className="text-[var(--primary)]" />
               <Typography className="telemetry-text">[ SYSTEM_ACCESS_PROTOCOLS ]</Typography>
            </Stack>
            <Typography
              variant="h2"
              sx={{ 
                fontSize: { xs: "2.5rem", sm: "3.5rem", md: "4.5rem" }, 
                fontWeight: 900, 
                fontFamily: "var(--font-mono)",
                letterSpacing: "-0.05em",
                color: "var(--text-primary)",
                textTransform: "uppercase",
                lineHeight: 1
              }}
            >
              Licensing <Box component="span" sx={{ color: "var(--text-faint)" }}>Modules</Box>.
            </Typography>
          </motion.div>

          {/* Terminal Toggle */}
          <Box sx={{ mt: 6 }}>
            <Stack
              direction={{ xs: "column", sm: "row" }}
              spacing={4}
              alignItems={{ xs: "flex-start", sm: "center" }}
            >
              <Box 
                onClick={() => setIsYearly(false)}
                sx={{ 
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 1.5,
                  color: !isYearly ? "var(--primary)" : "var(--text-faint)",
                  fontFamily: "var(--font-mono)",
                  fontSize: "12px",
                  fontWeight: 900,
                  transition: "all 0.2s"
                }}
              >
                {!isYearly ? "[X]" : "[ ]"} MONTHLY_BILLING_CYCLE
              </Box>
              <Box 
                onClick={() => setIsYearly(true)}
                sx={{ 
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 1.5,
                  color: isYearly ? "var(--primary)" : "var(--text-faint)",
                  fontFamily: "var(--font-mono)",
                  fontSize: "12px",
                  fontWeight: 900,
                  transition: "all 0.2s"
                }}
              >
                {isYearly ? "[X]" : "[ ]"} YEARLY_NODE_RESERVE
                {isYearly && (
                  <Box sx={{ ml: 2, px: 1, py: 0.2, border: "1px dashed var(--primary)", fontSize: "9px", color: "var(--primary)" }}>
                    EFFICIENCY: +20%
                  </Box>
                )}
              </Box>
            </Stack>
          </Box>
        </Box>

        {/* Pricing Matrix */}
        <Grid container spacing={4}>
          {plans.map((plan, index) => (
            <Grid item xs={12} md={4} key={index}>
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                style={{ height: "100%" }}
              >
                <Box
                  sx={{
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                    p: { xs: 4, md: 5 },
                    background: "var(--bg-base)",
                    border: "1px dashed var(--border-subtle)",
                    position: "relative",
                    transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                    "&:hover": {
                      borderColor: "var(--primary)",
                      background: "rgba(0, 255, 156, 0.02)",
                      "& .price-box": { borderColor: "var(--primary)" }
                    },
                  }}
                >
                  <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 6 }}>
                    <Box>
                      <Typography sx={{ fontWeight: 900, mb: 1, fontFamily: "var(--font-mono)", fontSize: "20px", color: "var(--text-primary)" }}>
                        {plan.name}
                      </Typography>
                      <Typography className="telemetry-text" sx={{ opacity: 0.6 }}>
                        ID: {plan.nodeId}
                      </Typography>
                    </Box>
                    {plan.popular && (
                      <Box sx={{ px: 1.5, py: 0.75, background: "var(--primary)", color: "#000", fontSize: "10px", fontWeight: 900, fontFamily: "var(--font-mono)" }}>
                        RECOMMENDED
                      </Box>
                    )}
                  </Stack>

                  {/* Price & Calculation */}
                  <Box 
                    className="price-box"
                    sx={{ 
                      mb: 6, 
                      p: 3, 
                      border: "1px dashed var(--border-subtle)", 
                      background: "rgba(0,0,0,0.3)",
                      transition: "border-color 0.3s"
                    }}
                  >
                    {plan.monthlyPrice !== null ? (
                      <Stack spacing={2}>
                        <Stack direction="row" alignItems="baseline" spacing={1}>
                          <Typography sx={{ fontSize: "3rem", fontWeight: 900, fontFamily: "var(--font-mono)", color: "var(--text-primary)", lineHeight: 1 }}>
                            ${isYearly ? plan.yearlyPrice : plan.monthlyPrice}
                          </Typography>
                          <Typography className="telemetry-text">/ CYCLE</Typography>
                        </Stack>
                        {isYearly && plan.monthlyPrice > 0 && (
                          <Box sx={{ pt: 2, borderTop: "1px dashed rgba(255,255,255,0.05)" }}>
                             <Typography sx={{ fontSize: "10px", color: "var(--primary)", fontFamily: "var(--font-mono)", fontWeight: 800 }}>
                               SAVINGS_DELTA: -${(plan.monthlyPrice - plan.yearlyPrice) * 12}/YR
                             </Typography>
                          </Box>
                        )}
                      </Stack>
                    ) : (
                      <Typography sx={{ fontSize: "2rem", fontWeight: 900, fontFamily: "var(--font-mono)", color: "var(--primary)" }}>
                        NEGOTIATE_OPS
                      </Typography>
                    )}
                  </Box>

                  {/* Feature Terminal */}
                  <Box sx={{ flexGrow: 1, mb: 6 }}>
                    <Typography className="telemetry-text" sx={{ mb: 3, opacity: 0.4 }}>// ENABLED_CAPABILITIES</Typography>
                    {plan.features.map((feature, fIndex) => (
                      <Box key={fIndex} sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1.5 }}>
                        <Box sx={{ width: 4, height: 4, background: "var(--primary)", borderRadius: "50%" }} />
                        <Typography sx={{ color: "var(--text-secondary)", fontSize: "11px", fontFamily: "var(--font-mono)", fontWeight: 700 }}>
                          {feature}
                        </Typography>
                      </Box>
                    ))}
                  </Box>

                  {/* CTA */}
                  <Button
                    component={Link}
                    href={plan.name === "ENTERPRISE_CORE" ? "/contact" : "/login"}
                    fullWidth
                    sx={{
                      py: 2,
                      background: plan.popular ? "var(--primary)" : "var(--bg-elevated)",
                      border: "1px dashed var(--border-subtle)",
                      color: plan.popular ? "#000" : "var(--text-primary)",
                      fontFamily: "var(--font-mono)",
                      fontSize: "12px",
                      fontWeight: 900,
                      borderRadius: 0,
                      letterSpacing: "0.15em",
                      "&:hover": {
                        background: "var(--primary)",
                        color: "#000",
                        borderColor: "var(--primary)",
                        boxShadow: "0 0 30px rgba(0,255,156,0.3)"
                      }
                    }}
                  >
                    {plan.cta}();
                  </Button>
                </Box>
              </motion.div>
            </Grid>
          ))}
        </Grid>

        <Box sx={{ mt: 15, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 6 }}>
           {[
             { label: "SOC2_TYPE_II", icon: Shield },
             { label: "GLOBAL_RESILIENCE", icon: Globe },
             { label: "SLA_99.99%", icon: Activity }
           ].map((cert, i) => (
             <Stack key={i} direction="row" spacing={1.5} alignItems="center">
                <cert.icon size={16} className="text-[var(--text-faint)]" />
                <Typography className="telemetry-text">{cert.label}</Typography>
             </Stack>
           ))}
        </Box>
      </Container>
    </Box>
  );
}
