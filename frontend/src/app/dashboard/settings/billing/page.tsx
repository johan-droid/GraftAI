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

export default function BillingPage() {
  const { user } = useAuthContext();
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [billingMessage, setBillingMessage] = useState<string | null>(null);

  const stats = user ? {
    tier: user.tier || 'free',
    daily_ai_count: user.daily_ai_count || 0,
    daily_sync_count: user.daily_sync_count || 0,
    daily_ai_limit: user.daily_ai_limit ?? (user.tier === 'elite' ? 2000 : (user.tier === 'pro' ? 200 : 10)),
    daily_sync_limit: user.daily_sync_limit ?? (user.tier === 'elite' ? 500 : (user.tier === 'pro' ? 50 : 3)),
    ai_remaining: user.ai_remaining ?? Math.max(0, (user.tier === 'elite' ? 2000 : (user.tier === 'pro' ? 200 : 10)) - (user.daily_ai_count || 0)),
    sync_remaining: user.sync_remaining ?? Math.max(0, (user.tier === 'elite' ? 500 : (user.tier === 'pro' ? 50 : 3)) - (user.daily_sync_count || 0)),
    quota_reset_at: user.quota_reset_at,
    trial_days_left: user.trial_days_left || 0,
    trial_expires_at: user.trial_expires_at,
    trial_active: user.trial_active || false,
    subscription_status: user.subscription_status || 'inactive'
  } : null;

  const handleManageSubscription = async () => {
    setActionLoading("portal");
    try {
      if (user?.razorpay_subscription_id) {
        const confirmed = window.confirm("Cancel your current Razorpay subscription and revert to the Free plan?");
        if (!confirmed) {
          return;
        }

        const res = await fetch("/api/v1/billing/razorpay/cancel-subscription", { method: "POST" });
        const result = await res.json();
        if (!res.ok) {
          throw new Error(result.detail || "Cancellation failed");
        }

        setBillingMessage("Your Razorpay subscription was canceled. Your plan has been reverted to Free.");
        window.location.reload();
        return;
      }

      const res = await fetch("/api/v1/billing/portal-session", { method: "POST" });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      console.error("Portal redirect failed:", err);
      setBillingMessage("Could not open billing management. Please contact support if this persists.");
    } finally {
      setActionLoading(null);
    }
  };

  const handleUpgrade = () => {
    window.location.assign("/pricing");
  };


  const aiProgress = stats ? (stats.daily_ai_count / stats.daily_ai_limit) * 100 : 0;
  const syncProgress = stats ? (stats.daily_sync_count / stats.daily_sync_limit) * 100 : 0;
  const aiQuotaPercent = stats ? Math.min(100, Math.round((stats.daily_ai_count / Math.max(1, stats.daily_ai_limit)) * 100)) : 0;
  const syncQuotaPercent = stats ? Math.min(100, Math.round((stats.daily_sync_count / Math.max(1, stats.daily_sync_limit)) * 100)) : 0;
  const isQuotaWarning = stats?.tier === 'free' && (aiQuotaPercent >= 80 || syncQuotaPercent >= 80);

  return (
    <div className="max-w-4xl space-y-5 sm:space-y-8 px-1 sm:px-0">
      <header>
        <h1 className="text-xl sm:text-2xl md:text-3xl font-black text-white mb-1.5 sm:mb-2 bg-gradient-to-r from-white to-slate-500 bg-clip-text">
          Billing & Usage
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 font-medium opacity-80 leading-relaxed">
          Manage your individual SaaS subscription and monitor real-time resource allocation.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
        {/* Current Plan Card */}
        <div className="md:col-span-2 bg-slate-950/40 backdrop-blur-xl border border-slate-800/60 rounded-xl sm:rounded-2xl p-4 sm:p-8 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-3 sm:p-6">
            {stats?.tier === 'free' ? (
              <Zap className="w-8 h-8 sm:w-12 sm:h-12 text-slate-800 rotate-12" />
            ) : (
              <Crown className="w-8 h-8 sm:w-12 sm:h-12 text-primary/20 rotate-12" />
            )}
          </div>

          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">Current Plan</span>
              {stats?.subscription_status === 'active' && (
                <span className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[8px] font-bold uppercase">
                  <CheckCircle2 className="w-2.5 h-2.5" /> Verified
                </span>
              )}
            </div>
            <h2 className="text-2xl sm:text-4xl font-black text-white mb-4 sm:mb-6 capitalize">{stats?.tier} Edition</h2>

            {stats?.trial_active && (
              <div className="mb-4 sm:mb-6 rounded-xl sm:rounded-2xl border border-amber-400/20 bg-amber-500/5 p-3 sm:p-4 text-xs sm:text-sm text-amber-100">
                <p className="font-semibold tracking-tight">Free trial active</p>
                <p className="text-[12px] text-amber-200/90 leading-relaxed">
                  You have <span className="font-bold text-white">{stats.trial_days_left} day{stats.trial_days_left === 1 ? '' : 's'}</span> left in your trial. Trial expires {stats.trial_expires_at ? new Date(stats.trial_expires_at).toLocaleDateString('en-US', { timeZone: 'UTC', month: 'short', day: 'numeric', year: 'numeric' }) : 'soon'}.
                </p>
              </div>
            )}

            <div className="flex flex-col sm:flex-row sm:flex-wrap gap-2.5 sm:gap-4 mb-4 sm:mb-8">
              <button 
                onClick={handleManageSubscription}
                disabled={actionLoading === 'portal'}
                aria-label={user?.razorpay_subscription_id ? 'Cancel subscription' : 'Manage billing'}
                className="w-full sm:w-auto min-h-11 px-4 sm:px-6 py-2.5 sm:py-3 rounded-xl bg-slate-900 border border-slate-800 text-white text-xs font-black uppercase tracking-widest hover:bg-slate-800 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading === 'portal' ? <Loader2 className="w-3 h-3 animate-spin" /> : <CreditCard className="w-3.5 h-3.5" />}
                {user?.razorpay_subscription_id ? 'Cancel Subscription' : 'Manage Billing'}
              </button>
              
              {stats?.tier === 'free' && (
                <button 
                  onClick={handleUpgrade}
                  aria-label="Upgrade to pro"
                  className="w-full sm:w-auto min-h-11 px-4 sm:px-6 py-2.5 sm:py-3 rounded-xl bg-primary text-white text-xs font-black uppercase tracking-widest shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all flex items-center justify-center gap-2"
                >
                  Upgrade to Pro
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
            {billingMessage && (
              <div className="mb-4 sm:mb-6 rounded-xl sm:rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-3 sm:p-4 text-xs sm:text-sm text-emerald-100">
                {billingMessage}
              </div>
            )}
            {isQuotaWarning && (
              <div className="mb-4 sm:mb-6 rounded-xl sm:rounded-2xl border border-amber-400/20 bg-amber-500/5 p-3 sm:p-4 text-xs sm:text-sm text-amber-100">
                <p className="font-semibold">Quota pressure detected</p>
                <p>
                  Your free tier usage is approaching capacity. You have used {aiQuotaPercent}% of AI messages and {syncQuotaPercent}% of syncs today.
                  Upgrade now to avoid hitting the hard daily cap.
                </p>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
               <div className="p-3 sm:p-4 rounded-xl bg-slate-900/50 border border-slate-800/40">
                  <div className="flex justify-between items-end mb-2">
                    <span className="text-[9px] sm:text-[10px] font-bold text-slate-500 uppercase tracking-tighter flex items-center gap-1.5">
                      <Sparkles className="w-3 h-3 text-primary" /> AI Copilot Messages
                    </span>
                    <span className="text-xs font-black text-white">{stats?.daily_ai_count} / {stats?.daily_ai_limit}</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${aiProgress}%` }}
                      className={`h-full ${aiProgress > 80 ? 'bg-amber-500' : 'bg-primary'}`}
                    />
                  </div>
               </div>

               <div className="p-3 sm:p-4 rounded-xl bg-slate-900/50 border border-slate-800/40">
                  <div className="flex justify-between items-end mb-2">
                    <span className="text-[9px] sm:text-[10px] font-bold text-slate-500 uppercase tracking-tighter flex items-center gap-1.5">
                      <BarChart3 className="w-3 h-3 text-primary" /> Calendar Syncs
                    </span>
                    <span className="text-xs font-black text-white">{stats?.daily_sync_count} / {stats?.daily_sync_limit}</span>
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

            <div className="mt-5 sm:mt-8 rounded-2xl sm:rounded-3xl border border-slate-800/60 bg-slate-950/60 p-4 sm:p-6">
              <h3 className="text-xs sm:text-sm font-bold uppercase tracking-[0.2em] sm:tracking-[0.24em] text-slate-400 mb-3">Billing Cycle</h3>
              <ul className="space-y-2.5 sm:space-y-3 text-xs sm:text-sm text-slate-300 leading-5 sm:leading-6">
                <li>1. Pick a plan and complete Razorpay checkout from the pricing page.</li>
                <li>2. Razorpay securely processes the payment and confirms the subscription.</li>
                <li>3. Razorpay sends a webhook to our backend at <code>/api/v1/billing/razorpay/webhook</code>.</li>
                <li>4. The backend updates your user record, activates the plan, and stores subscription info.</li>
                <li>5. Renewals happen automatically monthly until you cancel.</li>
                <li>6. Cancel anytime from this dashboard and the system will revert you to Free.</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Info Sidebar */}
        <div className="space-y-6">
          <div className="p-4 sm:p-6 rounded-xl sm:rounded-2xl bg-indigo-500/5 border border-indigo-500/10">
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
                <li key={item} className="flex items-center gap-2 text-[10px] sm:text-[11px] font-medium text-slate-400">
                  <div className="w-1 h-1 rounded-full bg-indigo-500" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="p-4 sm:p-6 rounded-xl sm:rounded-2xl bg-primary/5 border border-primary/10">
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
                <li key={item} className="flex items-center gap-2 text-[10px] sm:text-[11px] font-medium text-slate-300">
                  <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="p-3 sm:p-4 rounded-xl bg-amber-500/5 border border-amber-500/10 flex items-start sm:items-center gap-2.5 sm:gap-3">
        <AlertCircle className="w-4 h-4 text-amber-500 shrink-0" />
        <p className="text-[10px] sm:text-[11px] font-medium text-amber-200/60 leading-relaxed">
          Daily usage counters reset at midnight UTC.
          {stats?.quota_reset_at ? (
            <> Next reset: {new Date(stats.quota_reset_at).toLocaleString('en-US', { timeZone: 'UTC', hour12: false })} UTC.</>
          ) : null}
        </p>
      </div>
    </div>
  );
}
