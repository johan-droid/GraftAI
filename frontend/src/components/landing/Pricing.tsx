"use client";

import { useState } from "react";
import { Box, Typography, Container, Grid, Paper, Switch, Stack } from "@mui/material";
import { motion } from "framer-motion";
import { Check, Sparkles } from "lucide-react";
import Link from "next/link";
import { GradientButton } from "@/components/ui/GradientButton";

const plans = [
  {
    name: "Free",
    description: "Perfect for individuals getting started",
    monthlyPrice: 0,
    yearlyPrice: 0,
    features: [
      "Up to 100 scheduled events/month",
      "Basic AI assistance",
      "Email notifications",
      "Mobile app access",
      "Google Calendar sync",
    ],
    cta: "Get Started Free",
    ctaVariant: "secondary" as const,
    popular: false,
  },
  {
    name: "Pro",
    description: "For professionals who need more power",
    monthlyPrice: 19,
    yearlyPrice: 15,
    features: [
      "Unlimited scheduled events",
      "Advanced AI scheduling",
      "Priority support",
      "All calendar integrations",
      "Team collaboration (up to 5)",
      "Custom workflows",
      "Meeting analytics",
      "Focus time protection",
    ],
    cta: "Start Free Trial",
    ctaVariant: "primary" as const,
    popular: true,
  },
  {
    name: "Enterprise",
    description: "For organizations with advanced needs",
    monthlyPrice: null,
    yearlyPrice: null,
    features: [
      "Everything in Pro",
      "Unlimited team members",
      "SSO & SAML",
      "Dedicated support",
      "Custom integrations",
      "SLA guarantee",
      "Advanced analytics",
      "API access",
    ],
    cta: "Contact Sales",
    ctaVariant: "outline" as const,
    popular: false,
  },
];

export function Pricing() {
  const [isYearly, setIsYearly] = useState(false);

  return (
    <Box id="pricing" sx={{ py: { xs: 10, md: 16 } }}>
      <Container maxWidth="lg">
        {/* Header */}
        <Box sx={{ textAlign: "center", mb: { xs: 6, md: 8 } }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
          >
            <Typography
              variant="h2"
              sx={{ fontSize: { xs: "1.75rem", sm: "2.25rem", md: "3rem" }, fontWeight: 800, mb: 2 }}
            >
              Simple, Transparent{" "}
              <Box
                component="span"
                sx={{
                  background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Pricing
              </Box>
            </Typography>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            viewport={{ once: true }}
          >
            <Typography variant="body1" sx={{ color: "#94a3b8", mb: 4, maxWidth: 600, mx: "auto" }}>
              Choose the plan that fits your needs. All plans include core AI scheduling features.
            </Typography>
          </motion.div>

          {/* Toggle */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            viewport={{ once: true }}
          >
            <Stack
              direction="row"
              spacing={2}
              alignItems="center"
              justifyContent="center"
              sx={{ mb: 6 }}
            >
              <Typography variant="body1" sx={{ color: isYearly ? "#64748b" : "#f8fafc", fontWeight: 500 }}>
                Monthly
              </Typography>
              <Switch
                checked={isYearly}
                onChange={(e) => setIsYearly(e.target.checked)}
                sx={{
                  "& .MuiSwitch-switchBase.Mui-checked": {
                    color: "#6366f1",
                  },
                  "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": {
                    background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                  },
                }}
              />
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Typography variant="body1" sx={{ color: isYearly ? "#f8fafc" : "#64748b", fontWeight: 500 }}>
                  Yearly
                </Typography>
                <Box
                  sx={{
                    px: 1,
                    py: 0.5,
                    background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                    borderRadius: 1,
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: "white",
                  }}
                >
                  Save 20%
                </Box>
              </Box>
            </Stack>
          </motion.div>
        </Box>

        {/* Pricing Cards */}
        <Grid container spacing={3} alignItems="stretch">
          {plans.map((plan, index) => (
            <Grid item xs={12} md={4} key={index}>
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                style={{ height: "100%" }}
              >
                <Paper
                  sx={{
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                    p: { xs: 3, md: 4 },
                    background: plan.popular
                      ? "linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(236, 72, 153, 0.1) 100%)"
                      : "linear-gradient(135deg, rgba(26, 26, 46, 0.8) 0%, rgba(15, 15, 26, 0.9) 100%)",
                    border: plan.popular ? "2px solid #6366f1" : "1px solid rgba(99, 102, 241, 0.1)",
                    borderRadius: 3,
                    position: "relative",
                    overflow: "visible",
                    transition: "all 0.3s ease",
                    "&:hover": {
                      transform: "translateY(-8px)",
                      boxShadow: plan.popular
                        ? "0 25px 50px -12px rgba(99, 102, 241, 0.4)"
                        : "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
                    },
                  }}
                >
                  {/* Popular Badge */}
                  {plan.popular && (
                    <Box
                      sx={{
                        position: "absolute",
                        top: -12,
                        left: "50%",
                        transform: "translateX(-50%)",
                        background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                        color: "white",
                        px: 2,
                        py: 0.5,
                        borderRadius: 10,
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        display: "flex",
                        alignItems: "center",
                        gap: 0.5,
                      }}
                    >
                      <Sparkles size={14} />
                      MOST POPULAR
                    </Box>
                  )}

                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
                      {plan.name}
                    </Typography>
                    <Typography variant="body2" sx={{ color: "#94a3b8" }}>
                      {plan.description}
                    </Typography>
                  </Box>

                  {/* Price */}
                  <Box sx={{ mb: 3 }}>
                    {plan.monthlyPrice !== null ? (
                      <Box sx={{ display: "flex", alignItems: "baseline", gap: 0.5 }}>
                        <Typography variant="h3" sx={{ fontWeight: 800 }}>
                          ${isYearly ? plan.yearlyPrice : plan.monthlyPrice}
                        </Typography>
                        <Typography variant="body2" sx={{ color: "#64748b" }}>
                          /month
                        </Typography>
                      </Box>
                    ) : (
                      <Typography variant="h3" sx={{ fontWeight: 800 }}>
                        Custom
                      </Typography>
                    )}
                    {isYearly && plan.yearlyPrice !== null && plan.monthlyPrice !== null && (
                      <Typography variant="caption" sx={{ color: "#10b981", display: "block", mt: 0.5 }}>
                        Billed annually (${plan.yearlyPrice * 12}/year)
                      </Typography>
                    )}
                  </Box>

                  {/* Features */}
                  <Box sx={{ flexGrow: 1, mb: 3 }}>
                    {plan.features.map((feature, fIndex) => (
                      <Box key={fIndex} sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 1.5 }}>
                        <Box
                          sx={{
                            width: 20,
                            height: 20,
                            borderRadius: "50%",
                            background: plan.popular ? "rgba(99, 102, 241, 0.2)" : "rgba(16, 185, 129, 0.2)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            flexShrink: 0,
                          }}
                        >
                          <Check size={12} style={{ color: plan.popular ? "#6366f1" : "#10b981" }} />
                        </Box>
                        <Typography variant="body2" sx={{ color: "#e2e8f0" }}>
                          {feature}
                        </Typography>
                      </Box>
                    ))}
                  </Box>

                  {/* CTA */}
                  <GradientButton
                    component={Link}
                    href={plan.name === "Enterprise" ? "/contact" : "/register"}
                    gradientVariant={plan.ctaVariant}
                    fullWidth
                    size="large"
                  >
                    {plan.cta}
                  </GradientButton>
                </Paper>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
}
