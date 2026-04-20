"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/app/providers/auth-provider";
import { Box, Container, Typography, Stack, Grid, Button, alpha, ToggleButton, ToggleButtonGroup } from "@mui/material";
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
import { enhancedApiClient } from "@/lib/api-client-enhanced";

type Tier = {
  id: string;
  name: string;
  price: string;
  amount?: number;
  currency?: string;
  description: string;
  features: string[];
  highlight: boolean;
  cta: string;
  icon: React.ReactNode;
};

interface BillingPlan {
  id: string;
  name?: string;
  price?: number | string;
  currency?: string;
  description?: string;
  features?: string[];
}

interface RazorpayCheckoutResponse {
  mode?: string;
  message?: string;
  order_id?: string;
  key?: string;
  amount?: number;
  currency?: string;
  [k: string]: any;
}

const TIERS: Tier[] = [
  {
    id: "free",
    name: "Standard",
    price: "$0",
    amount: 0,
    currency: "USD",
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
    amount: 19,
    currency: "USD",
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
    amount: 49,
    currency: "USD",
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
  const [tiers, setTiers] = useState<Tier[]>(TIERS);
    const [billingInterval, setBillingInterval] = useState<'monthly' | 'yearly'>('monthly');
    const [billingMode, setBillingMode] = useState<null | { payment_mode?: string; can_simulate?: boolean; gateways?: any }>(null);

  

  const getIconFor = (id: string) => {
    if (id === "free") return <Zap size={18} />;
    if (id === "pro") return <Crown size={18} />;
    return <Sparkles size={18} />;
  };
  
  const getPrice = useCallback((tierId: string) => {
    if (tierId === 'free') return "$0";
    if (region === "IN") return tierId === 'pro' ? "₹499" : "₹1499";
    return tierId === 'pro' ? "$19" : "$49";
  }, [region]);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const data = await enhancedApiClient.get<BillingPlan[]>('/billing/plans');
        if (Array.isArray(data) && data.length) {
          const mapped = data.map((p) => ({
            id: p.id,
            name: p.name,
            amount: typeof p.price === 'number' ? p.price : undefined,
            currency: p.currency || 'USD',
            price: typeof p.price === 'number' && p.currency ? (p.currency.toUpperCase() === 'INR' ? `₹${p.price}` : `$${p.price}`) : getPrice(p.id),
            description: p.description || '',
            features: Array.isArray(p.features) ? p.features : [],
            highlight: p.id === 'pro',
            cta: p.id === 'elite' ? 'Contact Us' : (p.id === 'free' ? 'Get Started' : 'Upgrade to Pro'),
            icon: getIconFor(p.id),
          } as Tier));
          setTiers(mapped);
        }
      } catch (e) {
        // keep fallback TIERS
        console.warn('Failed to fetch plans from backend, using fallback', e);
      }
    };

    fetchPlans();
  }, [getPrice]);

  const currencySymbol = (c?: string) => {
    if (!c) return '$';
    if (c.toUpperCase() === 'INR') return '₹';
    if (c.toUpperCase() === 'USD') return '$';
    return c + ' ';
  };

  const formatPrice = (tier: Tier) => {
    const amt = (tier.amount ?? Number(String(tier.price).replace(/[^0-9.]/g, ''))) || 0;
    const cur = tier.currency ?? 'USD';
    if (billingInterval === 'monthly') {
      return `${currencySymbol(cur)}${amt}`;
    }
    const yearly = Math.round(amt * 12 * 0.83); // ~17% discount for yearly
    return `${currencySymbol(cur)}${yearly}`;
  };

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
    // Fetch server-side billing mode (test/disabled/production)
    const fetchBillingMode = async () => {
      try {
        const res = await fetch('/billing/mode');
        if (res.ok) {
          const data = await res.json();
          setBillingMode(data);
        }
      } catch {
        // ignore
      }
    };
    fetchBillingMode();
  }, []);

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
      // Use Razorpay for India region
      if (region === "IN") {
        const payload = { tier: tierId };
        const response = await enhancedApiClient.post<RazorpayCheckoutResponse>("/billing/razorpay/checkout", payload);

        if (response?.mode === "disabled" || response?.mode === "manual") {
          setBillingMessage(response?.message || "Payments are not available for this deployment.");
          return;
        }

        // Development / simulation mode
        if (response?.mode === "simulation") {
          // Optionally call verify simulation endpoint to flip user tier in dev
            try {
            await enhancedApiClient.post("/billing/razorpay/verify", {
              razorpay_payment_id: response.order_id + "_sim_pay",
              razorpay_order_id: response.order_id,
              razorpay_signature: "sim_signature",
            });
            window.location.assign("/dashboard/settings/billing?success=true");
            return;
          } catch {
            setBillingMessage("Simulation verification failed. Please refresh and try again.");
            return;
          }
        }

        // Load Razorpay checkout script
        const loadRzp = () => new Promise<boolean>((resolve, reject) => {
          if (typeof window === 'undefined') return reject(false);
          if ((window as any).Razorpay) return resolve(true);
          const existing = document.getElementById('razorpay-sdk');
          if (existing) return resolve(true);
          const script = document.createElement('script');
          script.id = 'razorpay-sdk';
          script.src = 'https://checkout.razorpay.com/v1/checkout.js';
          script.onload = () => resolve(true);
          script.onerror = () => reject(false);
          document.body.appendChild(script);
        });

        await loadRzp();

        const options = {
          key: response.key,
          amount: response.amount,
          currency: response.currency || 'INR',
          name: 'GraftAI',
          description: tierId === 'pro' ? 'Professional Subscription' : 'Enterprise Subscription',
          order_id: response.order_id,
            handler: async function (res: any) {
            try {
              // Verify payment on server
              await enhancedApiClient.post('/billing/razorpay/verify', res);
              window.location.assign('/dashboard/settings/billing?success=true');
            } catch {
              setBillingMessage('Payment verification failed. Contact support.');
            }
          },
          prefill: { name: user?.full_name || user?.email, email: user?.email },
          theme: { color: 'var(--primary)' },
        } as any;

        const rzp = new (window as any).Razorpay(options);
        rzp.on('payment.failed', function () {
          setBillingMessage('Payment failed or cancelled.');
        });
        rzp.open();
        return;
      }

      // Fallback: Stripe for other regions
      const response = await enhancedApiClient.post<{ checkout_url: string; session_id: string }>("/billing/stripe/create-checkout-session");
      if (!response.checkout_url) {
        throw new Error("Stripe checkout is not available right now.");
      }
      window.location.assign(response.checkout_url);
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

            <Typography
              variant="h1"
              className="text-gradient-neon"
              sx={{
                fontWeight: 800,
                fontSize: { xs: 36, md: 56 },
                letterSpacing: "-0.02em",
                lineHeight: 1.02,
                fontFamily: "var(--font-sans)",
                mb: 1
              }}
            >
              Simple Pricing
            </Typography>

            <Typography
              sx={{
                color: "var(--text-muted)",
                fontSize: { xs: 14, md: 16 },
                maxWidth: 720,
                mx: "auto",
                fontFamily: "var(--font-sans)",
                mb: 2
              }}
            >
              Choose the plan that fits your workflow. From personal use to scaling teams, we’ve got you covered.
            </Typography>

            {billingMode && billingMode.payment_mode === 'test' && (
              <Box sx={{ mt: 2, px: 3, py: 1.5, borderRadius: 1, border: '1px solid rgba(255,255,255,0.06)', bgcolor: 'rgba(255,255,255,0.02)', color: 'var(--text-muted)', fontSize: 13 }}>
                Sandbox / Demo mode enabled — no real charges will be processed. Use this mode to test checkout and webhooks.
              </Box>
            )}
            {billingMode && billingMode.payment_mode === 'disabled' && (
              <Box sx={{ mt: 2, px: 3, py: 1.5, borderRadius: 1, border: '1px solid rgba(255,0,96,0.06)', bgcolor: 'rgba(255,0,96,0.02)', color: 'var(--text-muted)', fontSize: 13 }}>
                Payments are disabled for this deployment. You can request a manual upgrade from the account owner.
              </Box>
            )}
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
          </motion.div>

          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
            <ToggleButtonGroup
              value={billingInterval}
              exclusive
              onChange={(e, val) => { if (val === 'monthly' || val === 'yearly') setBillingInterval(val); }}
              size="small"
              sx={{ borderRadius: 99, bgcolor: 'rgba(255,255,255,0.02)', px: 1 }}
            >
              <ToggleButton value="monthly">Monthly</ToggleButton>
              <ToggleButton value="yearly">Yearly — Save 2 months</ToggleButton>
            </ToggleButtonGroup>
          </Box>
        </Stack>

        <Grid container spacing={4} sx={{ mb: 16 }}>
          {tiers.map((tier, idx) => (
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
                  background: tier.highlight ? 'linear-gradient(135deg, rgba(0,255,156,0.04), rgba(255,255,255,0.01))' : undefined,
                  boxShadow: tier.highlight ? '0 10px 30px rgba(0,255,156,0.06)' : undefined,
                  position: "relative",
                  "&:hover": { borderColor: "var(--primary)", transform: 'translateY(-4px)', transition: "0.25s" }
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
                      {formatPrice(tier)}
                    </Typography>
                    <Typography sx={{ color: "var(--text-faint)", fontSize: 14 }}>
                      {billingInterval === 'monthly' ? '/ month' : '/ year'}
                    </Typography>
                    {billingInterval === 'yearly' && tier.amount && tier.amount > 0 && (
                      <Typography sx={{ color: "var(--text-muted)", fontSize: 12, ml: 1 }}>(billed annually)</Typography>
                    )}
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

      <Container maxWidth="lg" sx={{ pb: 20 }}>
        <Box sx={{ mt: 4, p: 4, borderRadius: 2, border: '1px solid var(--border-subtle)', bgcolor: 'var(--bg-card)' }}>
          <Typography variant="h5" sx={{ mb: 2, fontWeight: 800 }}>Market comparison</Typography>
          <Typography sx={{ color: 'var(--text-muted)', mb: 3 }}>Competitive pricing vs typical market offerings (illustrative).</Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 3, border: '1px solid var(--border-subtle)', borderRadius: 2 }}>
                <Typography sx={{ fontWeight: 800 }}>GraftAI Pro</Typography>
                <Typography sx={{ color: 'var(--text-muted)' }}>$19 / month</Typography>
                <Typography sx={{ mt: 1, fontSize: 13 }}>200 AI messages / day, priority processing, analytics, integrations.</Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 3, border: '1px solid var(--border-subtle)', borderRadius: 2 }}>
                <Typography sx={{ fontWeight: 800 }}>Competitor A</Typography>
                <Typography sx={{ color: 'var(--text-muted)' }}>$29 / month</Typography>
                <Typography sx={{ mt: 1, fontSize: 13 }}>Similar AI features, higher price for comparable usage.</Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 3, border: '1px solid var(--border-subtle)', borderRadius: 2 }}>
                <Typography sx={{ fontWeight: 800 }}>Competitor B</Typography>
                <Typography sx={{ color: 'var(--text-muted)' }}>$24 / month</Typography>
                <Typography sx={{ mt: 1, fontSize: 13 }}>Mid-range offering, lower AI quota for the price.</Typography>
              </Box>
            </Grid>
          </Grid>
          <Typography sx={{ mt: 3, color: 'var(--text-muted)' }}>Links: Real checkout links are used above to start subscriptions. For India customers, Razorpay checkout is used; other regions use Stripe.</Typography>
        </Box>
      </Container>
    </Box>
  );
}
