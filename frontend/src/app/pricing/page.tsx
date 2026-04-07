"use client";

interface RazorpayInstance {
  open: () => void;
  on: (event: string, callback: (response: {
    razorpay_payment_id: string;
    razorpay_subscription_id: string;
    razorpay_signature: string;
  }) => void) => void;
}

interface RazorpayOptions {
  key?: string;
  subscription_id: string;
  name: string;
  description?: string;
  handler: (response: {
    razorpay_payment_id: string;
    razorpay_subscription_id: string;
    razorpay_signature: string;
  }) => void;
  prefill: {
    name?: string;
    email?: string;
    contact?: string;
  };
  theme: {
    color: string;
  };
}

"use client";

interface RazorpayGlobal {
  new (options: RazorpayOptions): RazorpayInstance;
}

declare global {
  interface Window {
    Razorpay: RazorpayGlobal;
  }
}

import { useState, useEffect } from "react";
import { useAuthContext } from "@/app/providers/auth-provider";
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
import Script from "next/script";

const TIERS = [
  {
    id: "free",
    name: "Standard",
    price: "$0",
    description: "Perfect for secondary calendar management and casual AI scheduling.",
    features: [
      "10 AI Copilot Messages / Day",
      "3 Manual Calendar Syncs / Day",
      "Google & Outlook Integration",
      "Standard LLM Processing",
      "Community Support"
    ],
    highlight: false,
    cta: "Get Started",
    icon: <Zap className="w-5 h-5" />
  },
  {
    id: "pro",
    name: "Professional",
    price: "$19",
    description: "The ultimate productivity engine for high-density power users.",
    features: [
      "200 AI Copilot Messages / Day",
      "50 Manual Calendar Syncs / Day",
      "Priority LLM Processing",
      "Advanced Time Analytics",
      "Custom Meeting Templates",
      "Priority Email Support"
    ],
    highlight: true,
    cta: "Upgrade to Pro",
    icon: <Crown className="w-5 h-5" />
  },
  {
    id: "elite",
    name: "Elite Sovereign",
    price: "$49",
    description: "Unbounded AI coordination for executive-level time mastery.",
    features: [
      "Unlimited AI Messages*",
      "Unlimited Calendar Syncs",
      "Early Access to AI Plugins",
      "24/7 Concierge Support",
      "Advanced RAG Search",
      "Zero-Data-Retention Option"
    ],
    highlight: false,
    cta: "Contact Sales",
    icon: <Sparkles className="w-5 h-5" />
  }
];

export default function PricingPage() {
  const [loadingTier, setLoadingTier] = useState<string | null>(null);
  const [billingMessage, setBillingMessage] = useState<string | null>(null);
  const [region, setRegion] = useState<"US" | "IN">("US"); // Default to Global
  const { user } = useAuthContext();

  // IP-based Region Detection
  useEffect(() => {
    const detectRegion = async () => {
      try {
        const res = await fetch("https://ipapi.co/json/");
        const data = await res.json();
        if (data.country_code === "IN") {
          setRegion("IN");
        }
      } catch (err) {
        console.error("Region detection failed, defaulting to Global:", err);
      }
    };
    detectRegion();
  }, []);

  const getPrice = (tierId: string) => {
    if (tierId === 'free') return "$0";
    if (region === "IN") {
      return tierId === 'pro' ? "₹499" : "₹1499";
    }
    return tierId === 'pro' ? "$12" : "$28";
  };

  const handleSelectTier = async (tierId: string) => {
    if (tierId === 'free') {
      window.location.href = "/dashboard";
      return;
    }

    if (tierId === 'elite') {
      setBillingMessage("Elite plan onboarding is handled by our sales team. Please contact support for enterprise activation.");
      return;
    }

    setLoadingTier(tierId);
    setBillingMessage(null);

    try {
      const publicKeyResponse = await fetch("/api/v1/billing/razorpay/public-key");
      if (!publicKeyResponse.ok) {
        const err = await publicKeyResponse.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to load Razorpay public key");
      }

      const publicKeyPayload = await publicKeyResponse.json();
      const razorpayKey = process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID || publicKeyPayload?.key_id;

      if (!razorpayKey) {
        throw new Error("Razorpay key isn't configured. Please set NEXT_PUBLIC_RAZORPAY_KEY_ID or RAZORPAY_KEY_ID on the server.");
      }

      const res = await fetch(`/api/v1/billing/razorpay/create-subscription?tier=${tierId}`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(`Razorpay subscription create failed: ${err.detail || res.statusText}`);
      }

      const subscription = await res.json();
      if (!subscription?.id) {
        throw new Error("Invalid Razorpay subscription response.");
      }

      if (!window.Razorpay) {
        throw new Error("Razorpay checkout library failed to load.");
      }

      const options: RazorpayOptions = {
        key: razorpayKey,
        subscription_id: subscription.id,
        name: "GraftAI",
        description: `${tierId.toUpperCase()} Edition Subscription`,
        handler: function (response) {
          console.log("RZP payment successful:", response);
          window.location.assign("/dashboard/settings/billing?success=true");
        },
        prefill: {
          name: user?.name || user?.full_name || "",
          email: user?.email || "",
          contact: ""
        },
        theme: {
          color: "#4f46e5",
        },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (err) {
      console.error("Checkout failed:", err);
      setBillingMessage(typeof err === "string" ? err : (err as Error).message || "Checkout failed.");
    } finally {
      setLoadingTier(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#030712] text-white selection:bg-indigo-500/30 selection:text-white">
      <Script src="https://checkout.razorpay.com/v1/checkout.js" strategy="lazyOnload" />
      
      {/* Dynamic Sovereign Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[600px] h-[600px] rounded-full bg-indigo-500/10 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[400px] h-[400px] rounded-full bg-violet-600/10 blur-[100px]" />
      </div>

      <div className="page-with-floating-nav relative z-10 max-w-7xl mx-auto px-6 pb-24 lg:pb-32">
        <div className="text-center pt-20 mb-20 space-y-4">
          <div className="flex justify-center gap-2 mb-8">
            <button 
              onClick={() => setRegion("US")}
              className={`px-5 py-2 rounded-full text-[10px] font-black uppercase tracking-widest transition-all ${region === 'US' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25 ring-1 ring-white/20' : 'bg-white/5 text-slate-500 border border-white/5 hover:bg-white/10'}`}
            >
              $ Global
            </button>
            <button 
              onClick={() => setRegion("IN")}
              className={`px-5 py-2 rounded-full text-[10px] font-black uppercase tracking-widest transition-all ${region === 'IN' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25 ring-1 ring-white/20' : 'bg-white/5 text-slate-500 border border-white/5 hover:bg-white/10'}`}
            >
              ₹ India
            </button>
          </div>

          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-black uppercase tracking-widest"
          >
            <Sparkles className="w-3 h-3" /> {region === 'IN' ? 'Competitive Indian Pricing' : 'Global Premium SaaS'}
          </motion.div>
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="font-serif text-5xl md:text-8xl font-black tracking-tight mb-6 bg-gradient-to-b from-white via-white to-slate-500 bg-clip-text text-transparent leading-[1.1]"
          >
            Reclaim Your Time.
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-[17px] md:text-lg text-slate-400 font-medium max-w-2xl mx-auto leading-relaxed"
          >
            Simple, transparent pricing for power users. {region === 'IN' ? 'Optimized for the Indian market.' : 'No organizations, no seat minimums.'} Just pure productivity.
          </motion.p>
          {billingMessage && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mx-auto mt-8 max-w-2xl rounded-2xl border border-amber-400/20 bg-amber-500/5 p-4 text-sm text-amber-100"
            >
              {billingMessage}
            </motion.div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-24">
          {TIERS.map((tier, idx) => (
            <motion.div
              key={tier.id}
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * idx + 0.3 }}
              className={`relative flex flex-col p-8 rounded-[2.5rem] transition-all duration-700 group glass-panel ${
                tier.highlight 
                ? "bg-indigo-600/[0.04] border-indigo-500/40 shadow-2xl shadow-indigo-500/10 scale-105 z-20 hover:border-indigo-500 hover:shadow-indigo-500/30" 
                : "bg-white/[0.01] border-white/[0.06] hover:border-white/20 z-10"
              }`}
            >
              {tier.highlight && (
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 px-5 py-1.5 bg-indigo-600 text-white text-[10px] font-black uppercase tracking-[0.2em] rounded-full shadow-lg shadow-indigo-600/40 ring-1 ring-white/20">
                  Sovereign Choice
                </div>
              )}

              <div className="mb-10">
                <div className="flex items-center gap-3 mb-6">
                  <div className={`p-2.5 rounded-xl ${tier.highlight ? 'bg-indigo-500/20 text-indigo-400 ring-1 ring-indigo-500/30' : 'bg-white/5 text-slate-500'}`}>
                    {tier.icon}
                  </div>
                  <h3 className="text-2xl font-black text-white tracking-tight">{tier.name}</h3>
                </div>
                <div className="flex items-baseline gap-1 mb-4">
                  <span className="text-5xl font-black text-white">{getPrice(tier.id)}</span>
                  <span className="text-slate-500 font-medium">{tier.id !== 'free' && '/ month'}</span>
                </div>
                <p className="text-sm text-slate-400 leading-relaxed font-medium">
                  {tier.description}
                </p>
              </div>

              <div className="flex-grow space-y-4 mb-8">
                {tier.features.map(feature => (
                  <div key={feature} className="flex items-start gap-3">
                    <div className={`mt-1 p-0.5 rounded-full ${tier.highlight ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-500'}`}>
                      <Check className="w-3 h-3" />
                    </div>
                    <span className="text-xs font-semibold text-slate-300">{feature}</span>
                  </div>
                ))}
              </div>

              <button
                onClick={() => handleSelectTier(tier.id)}
                disabled={loadingTier === tier.id}
                className={`w-full py-4 rounded-2xl text-sm font-black uppercase tracking-widest transition-all active:scale-95 flex items-center justify-center gap-2 ${
                  tier.highlight
                  ? "bg-primary text-white shadow-xl shadow-primary/30 hover:bg-primary/90"
                  : "bg-slate-900 text-white border border-slate-800 hover:bg-slate-800"
                }`}
              >
                {loadingTier === tier.id ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    {tier.cta}
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </motion.div>
          ))}
        </div>

        {/* Feature Highlights Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mt-20">
          <div className="space-y-4">
            <ShieldCheck className="w-8 h-8 text-indigo-400" />
            <h4 className="text-lg font-bold">Privacy First</h4>
            <p className="text-xs text-slate-400 leading-relaxed">Your data is yours. We never sell your calendar context to third parties.</p>
          </div>
          <div className="space-y-4">
            <Cpu className="w-8 h-8 text-primary" />
            <h4 className="text-lg font-bold">Zero-Lag Sync</h4>
            <p className="text-xs text-slate-400 leading-relaxed">Proprietary sync engine designed for high-frequency individual updates.</p>
          </div>
          <div className="space-y-4">
            <Globe className="w-8 h-8 text-emerald-400" />
            <h4 className="text-lg font-bold">Global Presence</h4>
            <p className="text-xs text-slate-400 leading-relaxed">Seamless timezone handling across every continent and provider.</p>
          </div>
          <div className="space-y-4">
            <Sparkles className="w-8 h-8 text-amber-400" />
            <h4 className="text-lg font-bold">Smart Insights</h4>
            <p className="text-xs text-slate-400 leading-relaxed">AI that learns your scheduling preferences to proactively save you time.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
