"use client";

import { motion } from "framer-motion";
import { Check, Zap, Shield, Globe } from "lucide-react";

const PLANS = [
  {
    id: "free",
    name: "Free",
    price: "$0",
    description: "Perfect for exploring the power of GraftAI.",
    features: ["10 AI Messages/day", "3 Calendar Syncs/day", "Basic Analytics"],
    buttonText: "Current Plan",
    highlight: false,
    icon: Globe,
    color: "slate",
  },
  {
    id: "pro",
    name: "Professional",
    price: "$19",
    period: "/mo",
    description: "Unleash your productivity with higher limits.",
    features: ["200 AI Messages/day", "50 Calendar Syncs/day", "Team Management", "Advanced Analytics"],
    buttonText: "Upgrade to Pro",
    highlight: true,
    icon: Zap,
    color: "indigo",
  },
  {
    id: "elite",
    name: "Elite",
    price: "$49",
    period: "/mo",
    description: "Enterprise power for power users and small teams.",
    features: ["2000 AI Messages/day", "500 Calendar Syncs/day", "API Access", "Custom Branding"],
    buttonText: "Get Elite",
    highlight: false,
    icon: Shield,
    color: "violet",
  },
];

export function PricingSection({ currentTier = "free" }: { currentTier?: string }) {
  return (
    <div className="py-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {PLANS.map((plan) => {
          const isCurrent = currentTier.toLowerCase() === plan.id;
          const Icon = plan.icon;
          
          return (
            <motion.div
              key={plan.id}
              whileHover={{ y: -5 }}
              className={`relative rounded-3xl border ${
                plan.highlight 
                  ? "border-indigo-500/30 bg-indigo-500/5 shadow-2xl shadow-indigo-500/10" 
                  : "border-white/[0.07] bg-white/[0.02]"
              } p-8 overflow-hidden group`}
            >
              {plan.highlight && (
                <div className="absolute top-0 right-0 px-4 py-1 bg-indigo-500 text-[10px] font-black text-white uppercase tracking-[0.2em] rounded-bl-xl">
                  Most Popular
                </div>
              )}
              
              <div className="flex items-center gap-3 mb-6">
                <div className={`w-10 h-10 rounded-xl bg-${plan.color}-500/10 flex items-center justify-center`}>
                  <Icon className={`w-5 h-5 text-${plan.color}-400`} />
                </div>
                <div>
                  <h3 className="text-sm font-black text-white uppercase tracking-widest">{plan.name}</h3>
                  <p className="text-[11px] text-slate-500 font-medium">Subscription Tier</p>
                </div>
              </div>

              <div className="mb-6">
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-black text-white">{plan.price}</span>
                  {plan.period && <span className="text-sm text-slate-500 font-bold">{plan.period}</span>}
                </div>
                <p className="text-xs text-slate-400 mt-2 leading-relaxed">{plan.description}</p>
              </div>

              <div className="space-y-3 mb-8">
                {plan.features.map((feature, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="w-5 h-5 rounded-full bg-emerald-500/10 flex items-center justify-center shrink-0">
                      <Check className="w-3 h-3 text-emerald-400" />
                    </div>
                    <span className="text-xs text-slate-300 font-medium">{feature}</span>
                  </div>
                ))}
              </div>

              <button
                disabled={isCurrent}
                className={`w-full py-4 rounded-xl text-xs font-black uppercase tracking-[0.2em] transition-all ${
                  isCurrent
                    ? "bg-white/5 text-slate-500 cursor-not-allowed border border-white/5"
                    : plan.highlight
                    ? "bg-indigo-600 text-white hover:bg-indigo-500 shadow-xl shadow-indigo-600/20 active:scale-[0.98]"
                    : "bg-white/5 text-white hover:bg-white/10 border border-white/10 active:scale-[0.98]"
                }`}
              >
                {isCurrent ? "Current Plan" : plan.buttonText}
              </button>
              
              <div className={`absolute -bottom-12 -right-12 w-32 h-32 bg-${plan.color}-500/5 blur-3xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity`} />
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
