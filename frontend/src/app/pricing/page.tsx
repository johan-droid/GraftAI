"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/app/providers/auth-provider";
import { Box, Container, Typography, Stack, Grid, Button, alpha } from "@mui/material";
import { motion } from "framer-motion";
import { 
  Check, 
  Zap, 
  Crown, 
  Sparkles, 
  ShieldCheck, 
  Cpu, 
  Globe,
  ArrowRight,
  Loader2
} from "lucide-react";
import { apiClient } from "@/lib/api-client";

const TIERS = [
  {
    id: "free",
    name: "Standard",
    price: "$0",
    description: "Perfect for managing your personal schedule and trying out AI assistance.",
    features: [
      "10 AI Assistant Messages / Day",
      "Sync with Google & Outlook",
      "Standard Processing Speed",
      "Community Support"
    ],
    highlight: false,
    cta: "Get Started",
    icon: <Zap size={18} />
  },
  {
    id: "pro",
    name: "Professional",
    price: "$19",
    description: "The ultimate productivity engine for individuals and power users.",
    features: [
      "200 AI Assistant Messages / Day",
      "Priority Processing Speed",
      "Advanced Time Analytics",
      "Custom Meeting Templates",
      "Priority Support"
    ],
    highlight: true,
    cta: "Upgrade to Pro",
    icon: <Crown size={18} />
  },
  {
    id: "elite",
    name: "Enterprise",
    price: "$49",
    description: "Unbounded AI coordination for teams and high-level mastery.",
    features: [
      "Unlimited AI Messages",
      "Unlimited Tool Access",
      "Early Access to Features",
      "Dedicated Support",
      "Custom Privacy Controls"
    ],
    highlight: false,
    cta: "Contact Us",
    icon: <Sparkles size={18} />
  }
];

export default function PricingPage() {
  const [loadingTier, setLoadingTier] = useState<string | null>(null);
  const [billingMessage, setBillingMessage] = useState<string | null>(null);
  const [region, setRegion] = useState<"US" | "IN">("US");
  const { user } = useAuth();

  useEffect(() => {
    const detectRegion = async () => {
      try {
        const res = await fetch("https://ipapi.co/json/");
        const data = await res.json();
        if (data.country_code === "IN") setRegion("IN");
      } catch {
      }
    };
    detectRegion();
  }, []);

  const getPrice = (tierId: string) => {
    if (tierId === 'free') return "$0";
    if (region === "IN") return tierId === 'pro' ? "₹499" : "₹1499";
    return tierId === 'pro' ? "$19" : "$49";
  };

  const handleSelectTier = async (tierId: string) => {
    if (tierId === 'free') {
      window.location.href = "/dashboard";
      return;
    }
    if (tierId === 'elite') {
      setBillingMessage("Enterprise onboarding requires a quick chat with our team. Reaching out...");
      return;
    }
    if (!user) {
      window.location.href = `/login?redirect=${encodeURIComponent('/pricing')}`;
      return;
    }

    setLoadingTier(tierId);
    try {
      await apiClient.post("/billing/razorpay/checkout");
      await apiClient.post("/billing/razorpay/verify-simulation", { 
        razorpay_payment_id: "pay_sim_" + Date.now() 
      });
      setBillingMessage("Account upgraded. Taking you to your dashboard...");
      setTimeout(() => window.location.href = "/dashboard", 1500);
    } catch (error: unknown) {
      const err = error instanceof Error ? error : new Error("Connection issue during checkout. Please try again.");
      setBillingMessage(err.message);
    } finally {
      setLoadingTier(null);
    }
  };

  return (
    <Box sx={{ bgcolor: "var(--bg-base)", minHeight: "100vh", position: "relative" }}>
      <Container maxWidth="lg" sx={{ pt: { xs: 20, md: 24 }, pb: 20, position: "relative", zIndex: 1 }}>
        <Stack spacing={2} sx={{ mb: 12, textAlign: "center" }}>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Box sx={{ 
              display: "inline-flex", 
              gap: 1, 
              mb: 4, 
              p: 0.5, 
              bgcolor: "rgba(255,255,255,0.03)", 
              borderRadius: 99, 
              border: "1px solid var(--border-subtle)" 
            }}>
              <Button 
                onClick={() => setRegion("US")}
                sx={{ 
                  borderRadius: 99, px: 3, py: 0.5, fontSize: 10, fontFamily: "var(--font-mono)", 
                  color: region === "US" ? "var(--primary)" : "var(--text-muted)",
                  bgcolor: region === "US" ? "rgba(0, 255, 156, 0.05)" : "transparent",
                  "&:hover": { bgcolor: "rgba(255,255,255,0.05)" }
                }}
              >
                Global
              </Button>
              <Button 
                onClick={() => setRegion("IN")}
                sx={{ 
                  borderRadius: 99, px: 3, py: 0.5, fontSize: 10, fontFamily: "var(--font-mono)", 
                  color: region === "IN" ? "var(--primary)" : "var(--text-muted)",
                  bgcolor: region === "IN" ? "rgba(0, 255, 156, 0.05)" : "transparent",
                  "&:hover": { bgcolor: "rgba(255,255,255,0.05)" }
                }}
              >
                India
              </Button>
            </Box>
          </motion.div>

          <Typography
            variant="h1"
            className="text-gradient-neon"
            sx={{
              fontWeight: 900,
              fontSize: { xs: 42, md: 72 },
              letterSpacing: "-0.04em",
              lineHeight: 1,
              fontFamily: "var(--font-sans)"
            }}
          >
            Simple Pricing
          </Typography>
          <Typography
            sx={{
              color: "var(--text-muted)",
              fontSize: { xs: 16, md: 18 },
              maxWidth: 600,
              mx: "auto",
              fontFamily: "var(--font-sans)"
            }}
          >
            Choose the plan that fits your workflow. From personal use to scaling teams, we&apos;ve got you covered.
          </Typography>
          {billingMessage && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <Box sx={{ 
                mt: 4, px: 3, py: 1.5, borderRadius: 1, border: "1px solid rgba(0, 255, 156, 0.2)", 
                bgcolor: "rgba(0, 255, 156, 0.05)", color: "var(--primary)", fontSize: "12px", 
                fontFamily: "var(--font-mono)", display: "inline-block" 
              }}>
                [ STATUS: {billingMessage} ]
              </Box>
            </motion.div>
          )}
        </Stack>

        <Grid container spacing={4} sx={{ mb: 16 }}>
          {TIERS.map((tier, idx) => (
            <Grid item xs={12} md={4} key={tier.id}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                style={{ height: "100%" }}
              >
                <Box className="refined-glass" sx={{ 
                  p: 4, 
                  height: "100%", 
                  display: "flex", 
                  flexDirection: "column",
                  borderRadius: 2,
                  border: tier.highlight ? "1px solid var(--primary)" : "1px solid var(--border-subtle)",
                  position: "relative",
                  "&:hover": { borderColor: "var(--primary)", transition: "0.3s" }
                }}>
                  {tier.highlight && (
                    <Box sx={{ 
                      position: "absolute", top: -12, left: "50%", transform: "translateX(-50%)", 
                      bgcolor: "var(--primary)", color: "var(--bg-base)", px: 2, py: 0.5, 
                      borderRadius: 1, fontSize: 10, fontWeight: 900, letterSpacing: "0.1em",
                      fontFamily: "var(--font-sans)"
                    }}>
                      MOST POPULAR
                    </Box>
                  )}

                  <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
                    <Box sx={{ p: 1, bgcolor: "rgba(0, 255, 156, 0.1)", borderRadius: 1 }}>
                      {tier.icon}
                    </Box>
                  </Stack>

                  <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, color: "var(--text-primary)" }}>
                    {tier.name}
                  </Typography>
                  <Stack direction="row" alignItems="baseline" spacing={1} sx={{ mb: 3 }}>
                    <Typography variant="h3" sx={{ fontWeight: 900, color: "var(--text-primary)" }}>
                      {getPrice(tier.id)}
                    </Typography>
                    <Typography sx={{ color: "var(--text-faint)", fontSize: 14 }}>/ month</Typography>
                  </Stack>
                  <Typography sx={{ color: "var(--text-muted)", fontSize: 13, mb: 4, minHeight: 40 }}>
                    {tier.description}
                  </Typography>

                  <Stack spacing={2} sx={{ mb: 6, flexGrow: 1 }}>
                    {tier.features.map(f => (
                      <Stack key={f} direction="row" spacing={1.5} alignItems="center">
                        <Check size={14} className="text-primary" />
                        <Typography sx={{ fontSize: 12, color: "var(--text-secondary)", fontWeight: 500 }}>{f}</Typography>
                      </Stack>
                    ))}
                  </Stack>

                  <Button
                    onClick={() => handleSelectTier(tier.id)}
                    disabled={!!loadingTier}
                    fullWidth
                    variant={tier.highlight ? "contained" : "outlined"}
                    endIcon={loadingTier === tier.id ? <Loader2 size={16} className="animate-spin" /> : <ArrowRight size={16} />}
                    sx={{
                      borderRadius: 1,
                      py: 1.5,
                      textTransform: "none",
                      fontWeight: 700,
                      fontFamily: "var(--font-sans)",
                      bgcolor: tier.highlight ? "var(--primary)" : "transparent",
                      color: tier.highlight ? "var(--bg-base)" : "var(--text-primary)",
                      borderColor: "var(--primary)",
                      "&:hover": {
                        bgcolor: tier.highlight ? alpha("#00ff9c", 0.9) : "rgba(0, 255, 156, 0.05)",
                        borderColor: "var(--primary)"
                      }
                    }}
                  >
                    {tier.cta}
                  </Button>
                </Box>
              </motion.div>
            </Grid>
          ))}
        </Grid>

        <Stack 
          direction={{ xs: "column", md: "row" }} 
          spacing={8} 
          sx={{ 
            p: 6, 
            borderRadius: 2, 
            bgcolor: "rgba(255,255,255,0.01)", 
            border: "1px dashed var(--border-subtle)" 
          }}
        >
          <Stack spacing={2} sx={{ flex: 1 }}>
            <ShieldCheck size={32} className="text-primary" />
            <Typography variant="h6" sx={{ fontWeight: 800, fontFamily: "var(--font-sans)" }}>Privacy First</Typography>
            <Typography sx={{ color: "var(--text-muted)", fontSize: 13, fontFamily: "var(--font-sans)" }}>Your data never leaves your context. Fully encrypted at rest and in transit.</Typography>
          </Stack>
          <Stack spacing={2} sx={{ flex: 1 }}>
            <Cpu size={32} className="text-primary" />
            <Typography variant="h6" sx={{ fontWeight: 800, fontFamily: "var(--font-sans)" }}>Fast Sync</Typography>
            <Typography sx={{ color: "var(--text-muted)", fontSize: 13, fontFamily: "var(--font-sans)" }}>High-frequency sync engine for real-time calendar updates without the wait.</Typography>
          </Stack>
          <Stack spacing={2} sx={{ flex: 1 }}>
            <Globe size={32} className="text-primary" />
            <Typography variant="h6" sx={{ fontWeight: 800, fontFamily: "var(--font-sans)" }}>Works Everywhere</Typography>
            <Typography sx={{ color: "var(--text-muted)", fontSize: 13, fontFamily: "var(--font-sans)" }}>Seamless synchronization across all continents with 99.9% uptime reliability.</Typography>
          </Stack>
        </Stack>
      </Container>
    </Box>
  );
}
