"use client";

import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { 
  CreditCard, 
  Zap,
  Crown,
  CheckCircle2, 
  ArrowUpRight,
  Loader2,
} from "lucide-react";
import { useAuth } from "@/app/providers/auth-provider";
import { apiClient } from "@/lib/api-client";

export default function BillingPage() {
  const { user } = useAuth();
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [billingMessage, setBillingMessage] = useState<string | null>(null);
  const searchParams = useSearchParams();
  const router = useRouter();

  const stats = user ? {
    tier: user.tier || 'free',
    daily_ai_count: Number(user.daily_ai_count ?? 0),
    daily_sync_count: Number(user.daily_sync_count ?? 0),
    daily_ai_limit: Number(user.daily_ai_limit ?? (user.tier === 'elite' ? 2000 : (user.tier === 'pro' ? 200 : 10))),
    daily_sync_limit: Number(user.daily_sync_limit ?? (user.tier === 'elite' ? 500 : (user.tier === 'pro' ? 50 : 3))),
    ai_remaining: Number(user.ai_remaining ?? Math.max(0, (user.tier === 'elite' ? 2000 : (user.tier === 'pro' ? 200 : 10)) - Number(user.daily_ai_count ?? 0))),
    sync_remaining: Number(user.sync_remaining ?? Math.max(0, (user.tier === 'elite' ? 500 : (user.tier === 'pro' ? 50 : 3)) - Number(user.daily_sync_count ?? 0))),
    quota_reset_at: user.quota_reset_at ? String(user.quota_reset_at) : undefined,
    trial_days_left: Number(user.trial_days_left ?? 0),
    trial_expires_at: user.trial_expires_at ? String(user.trial_expires_at) : undefined,
    trial_active: Boolean(user.trial_active),
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

        await apiClient.post("/billing/razorpay/cancel-subscription");
        router.push(`${window.location.pathname}?canceled=true`);
        return;
      }
      // Without a portal, "Manage Billing" for non-Razorpay users just means upgrading.
      window.location.assign("/pricing");
    } catch (err) {
      console.error("Portal redirect failed:", err);
      setBillingMessage("Could not process request. Please contact support if this persists.");
    } finally {
      setActionLoading(null);
    }
  };

  const handleUpgrade = () => {
    window.location.assign("/pricing");
  };

  useEffect(() => {
    if (searchParams?.get("canceled") === "true") {
      setBillingMessage("Your Razorpay subscription was canceled. Your plan has been reverted to Free.");
      if (typeof window !== "undefined") {
        const url = new URL(window.location.href);
        url.searchParams.delete("canceled");
        window.history.replaceState({}, "", url.pathname + url.search);
      }
    }
  }, [searchParams]);

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


    </div>
  );
}
