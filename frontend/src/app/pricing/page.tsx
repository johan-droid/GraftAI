"use client";

import { useState, useEffect } from "react";
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
  Loader2,
  MapPin
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
  const [region, setRegion] = useState<"US" | "IN">("US"); // Default to Global

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
    
    setLoadingTier(tierId);
    try {
      if (region === 'IN') {
        // Initialize Razorpay
        const res = await fetch("/api/v1/billing/razorpay/create-subscription?tier=" + tierId, { method: "POST" });
        const subscription = await res.json();
        
        const options = {
          key: process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID,
          subscription_id: subscription.id,
          name: "GraftAI",
          description: `${tierId.toUpperCase()} Edition Subscription`,
          handler: function (response: any) {
            console.log("RZP Payment Successful:", response);
            window.location.href = "/dashboard/settings/billing?success=true";
          },
          prefill: {
            name: "GraftAI User",
          },
          theme: {
            color: "#4f46e5",
          },
        };
        // @ts-expect-error
        const rzp = new window.Razorpay(options);
        rzp.open();
      } else {
        // Stripe Path
        console.log(`Starting Stripe checkout for ${tierId}...`);
      }
    } catch (err) {
      console.error("Checkout failed:", err);
    } finally {
      setLoadingTier(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white selection:bg-primary/30">
      <Script src="https://checkout.razorpay.com/v1/checkout.js" />
      
      {/* Dynamic Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 blur-[120px] rounded-full animate-pulse" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-500/10 blur-[120px] rounded-full" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 py-24 lg:py-32">
        <div className="text-center mb-20 space-y-4">
          <div className="flex justify-center gap-4 mb-4">
            <button 
              onClick={() => setRegion("US")}
              className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase transition-all ${region === 'US' ? 'bg-primary text-white' : 'bg-slate-900 text-slate-500 border border-slate-800'}`}
            >
              $ Global
            </button>
            <button 
              onClick={() => setRegion("IN")}
              className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase transition-all ${region === 'IN' ? 'bg-primary text-white border-primary shadow-[0_0_15px_rgba(79,70,229,0.2)]' : 'bg-slate-900 text-slate-500 border border-slate-800'}`}
            >
              ₹ India
            </button>
          </div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-[10px] font-black uppercase tracking-widest"
          >
            <Sparkles className="w-3 h-3" /> {region === 'IN' ? 'Competitive Indian Pricing' : 'Global Premium SaaS'}
          </motion.div>
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-5xl md:text-7xl font-black tracking-tight mb-6 bg-gradient-to-b from-white to-slate-500 bg-clip-text text-transparent"
          >
            Reclaim Your Time.
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-lg md:text-xl text-slate-400 font-medium max-w-2xl mx-auto leading-relaxed"
          >
            Simple, transparent pricing for power users. {region === 'IN' ? 'Optimized for the Indian market.' : 'No organizations, no seat minimums.'} Just pure productivity.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-24">
          {TIERS.map((tier, idx) => (
            <motion.div
              key={tier.id}
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * idx + 0.3 }}
              className={`relative flex flex-col p-8 rounded-3xl border transition-all duration-500 group ${
                tier.highlight 
                ? "bg-slate-900/60 border-primary/40 shadow-2xl shadow-primary/10 scale-105 z-20" 
                : "bg-slate-950/40 border-slate-800/60 hover:border-slate-700 hover:bg-slate-900/40 z-10"
              }`}
            >
              {tier.highlight && (
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 px-4 py-1 bg-primary text-white text-[10px] font-black uppercase tracking-widest rounded-full shadow-lg shadow-primary/40">
                  Most Popular
                </div>
              )}

              <div className="mb-8">
                <div className="flex items-center gap-2 mb-4">
                  <div className={`p-2 rounded-lg ${tier.highlight ? 'bg-primary/20 text-primary' : 'bg-slate-900 text-slate-400'}`}>
                    {tier.icon}
                  </div>
                  <h3 className="text-xl font-bold text-white">{tier.name}</h3>
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
