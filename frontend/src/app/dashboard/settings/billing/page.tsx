"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { 
  CreditCard, 
  Zap, 
  Crown, 
  CheckCircle2, 
  AlertCircle,
  ArrowUpRight,
  Loader2,
  Sparkles,
  BarChart3
} from "lucide-react";
import { useAuthContext } from "@/app/providers/auth-provider";

// In a real implementation, usage would come from the API

export default function BillingPage() {
  const { user } = useAuthContext();
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const stats = user ? {
    tier: user.tier || 'free',
    daily_ai_count: user.daily_ai_count || 0,
    daily_sync_count: user.daily_sync_count || 0,
    ai_limit: user.tier === 'elite' ? 2000 : (user.tier === 'pro' ? 200 : 10),
    sync_limit: user.tier === 'elite' ? 500 : (user.tier === 'pro' ? 50 : 3),
    subscription_status: user.subscription_status || 'inactive'
  } : null;

  const handleManageSubscription = async () => {
    setActionLoading("portal");
    try {
      if (user?.razorpay_subscription_id) {
         // Redirect to Razorpay management or show info
         alert("Please manage your subscription via the Razorpay dashboard or your email link.");
         return;
      }
      
      const res = await fetch("/api/v1/billing/portal-session", { method: "POST" });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      console.error("Portal redirect failed:", err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleUpgrade = () => {
    window.location.assign("/pricing");
  };


  const aiProgress = stats ? (stats.daily_ai_count / stats.ai_limit) * 100 : 0;
  const syncProgress = stats ? (stats.daily_sync_count / stats.sync_limit) * 100 : 0;

  return (
    <div className="max-w-4xl space-y-8">
      <header>
        <h1 className="text-2xl md:text-3xl font-black text-white mb-2 bg-gradient-to-r from-white to-slate-500 bg-clip-text">
          Billing & Usage
        </h1>
        <p className="text-sm text-slate-400 font-medium opacity-80">
          Manage your individual SaaS subscription and monitor real-time resource allocation.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Current Plan Card */}
        <div className="md:col-span-2 bg-slate-950/40 backdrop-blur-xl border border-slate-800/60 rounded-2xl p-8 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-6">
            {stats?.tier === 'free' ? (
              <Zap className="w-12 h-12 text-slate-800 rotate-12" />
            ) : (
              <Crown className="w-12 h-12 text-primary/20 rotate-12" />
            )}
          </div>

          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">Current Plan</span>
              {stats?.subscription_status === 'active' && (
                <span className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[8px] font-bold uppercase">
                  <CheckCircle2 className="w-2.5 h-2.5" /> Verified
                </span>
              )}
            </div>
            <h2 className="text-4xl font-black text-white mb-6 capitalize">{stats?.tier} Edition</h2>
            
            <div className="flex flex-wrap gap-4 mb-8">
              <button 
                onClick={handleManageSubscription}
                disabled={stats?.tier === 'free' || actionLoading === 'portal'}
                className="px-6 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white text-xs font-black uppercase tracking-widest hover:bg-slate-800 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading === 'portal' ? <Loader2 className="w-3 h-3 animate-spin" /> : <CreditCard className="w-3.5 h-3.5" />}
                Manage Billing
              </button>
              
              {stats?.tier === 'free' && (
                <button 
                  onClick={handleUpgrade}
                  className="px-6 py-3 rounded-xl bg-primary text-white text-xs font-black uppercase tracking-widest shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all flex items-center gap-2"
                >
                  Upgrade to Pro
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
               <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/40">
                  <div className="flex justify-between items-end mb-2">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter flex items-center gap-1.5">
                      <Sparkles className="w-3 h-3 text-primary" /> AI Copilot Messages
                    </span>
                    <span className="text-xs font-black text-white">{stats?.daily_ai_count} / {stats?.ai_limit}</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${aiProgress}%` }}
                      className={`h-full ${aiProgress > 80 ? 'bg-amber-500' : 'bg-primary'}`}
                    />
                  </div>
               </div>

               <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/40">
                  <div className="flex justify-between items-end mb-2">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter flex items-center gap-1.5">
                      <BarChart3 className="w-3 h-3 text-primary" /> Calendar Syncs
                    </span>
                    <span className="text-xs font-black text-white">{stats?.daily_sync_count} / {stats?.sync_limit}</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${syncProgress}%` }}
                      className={`h-full ${syncProgress > 80 ? 'bg-amber-500' : 'bg-primary'}`}
                    />
                  </div>
               </div>
            </div>
          </div>
        </div>

        {/* Info Sidebar */}
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-indigo-500/5 border border-indigo-500/10">
            <h3 className="text-xs font-black text-white uppercase tracking-widest mb-4 flex items-center gap-2">
              <Zap className="w-3.5 h-3.5 text-indigo-400" /> Free Limits
            </h3>
            <ul className="space-y-3">
              {[
                "10 AI Requests / Day",
                "3 Manual Syncs / Day",
                "Standard Response Time",
                "Basic Analytics"
              ].map(item => (
                <li key={item} className="flex items-center gap-2 text-[10px] font-medium text-slate-400">
                  <div className="w-1 h-1 rounded-full bg-indigo-500" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="p-6 rounded-2xl bg-primary/5 border border-primary/10">
            <h3 className="text-xs font-black text-white uppercase tracking-widest mb-4 flex items-center gap-2">
              <Crown className="w-3.5 h-3.5 text-primary" /> Pro Benefits
            </h3>
            <ul className="space-y-3">
              {[
                "200 AI Requests / Day",
                "50 Manual Syncs / Day",
                "Priority LLM Processing",
                "Advanced Insights",
                "Early access to plugins"
              ].map(item => (
                <li key={item} className="flex items-center gap-2 text-[10px] font-medium text-slate-300">
                  <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/10 flex items-center gap-3">
        <AlertCircle className="w-4 h-4 text-amber-500 shrink-0" />
        <p className="text-[10px] font-medium text-amber-200/60 leading-relaxed">
          Daily usage counters reset every 24 hours at 00:00 UTC. Unused requests do not roll over to the next day.
        </p>
      </div>
    </div>
  );
}
