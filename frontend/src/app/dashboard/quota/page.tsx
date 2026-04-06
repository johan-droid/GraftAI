"use client";

import { useAuthContext } from "@/app/providers/auth-provider";
import { motion } from "framer-motion";
import { 
  BarChart3, 
  Sparkles, 
  AlertCircle,
  Zap,
  Crown
} from "lucide-react";

export default function QuotaPage() {
  const { user } = useAuthContext();

  const stats = user ? {
    tier: user.tier || 'free',
    daily_ai_count: user.daily_ai_count || 0,
    daily_sync_count: user.daily_sync_count || 0,
    daily_ai_limit: user.daily_ai_limit ?? (user.tier === 'elite' ? 2000 : (user.tier === 'pro' ? 200 : 10)),
    daily_sync_limit: user.daily_sync_limit ?? (user.tier === 'elite' ? 500 : (user.tier === 'pro' ? 50 : 3)),
    quota_reset_at: user.quota_reset_at,
  } : null;

  const aiProgress = stats ? (stats.daily_ai_count / Math.max(1, stats.daily_ai_limit)) * 100 : 0;
  const syncProgress = stats ? (stats.daily_sync_count / Math.max(1, stats.daily_sync_limit)) * 100 : 0;
  const aiQuotaPercent = Math.min(100, Math.round(aiProgress));
  const syncQuotaPercent = Math.min(100, Math.round(syncProgress));
  const isQuotaWarning = stats?.tier === 'free' && (aiQuotaPercent >= 80 || syncQuotaPercent >= 80);

  return (
    <div className="max-w-4xl space-y-5 sm:space-y-8 px-4 sm:px-6 py-4">
      <header>
        <h1 className="text-xl sm:text-2xl md:text-3xl font-black text-white mb-1.5 sm:mb-2 bg-gradient-to-r from-white to-slate-500 bg-clip-text">
          Quota & Resource Usage
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 font-medium opacity-80 leading-relaxed">
          Monitor your daily API consumption and system integration limits.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <div className="bg-slate-950/40 backdrop-blur-xl border border-slate-800/60 rounded-xl sm:rounded-2xl p-5 sm:p-8 relative overflow-hidden">
            <h2 className="text-sm font-bold text-white mb-6 uppercase tracking-widest text-slate-300">Daily Resources</h2>
            
            {isQuotaWarning && (
              <div className="mb-6 rounded-xl sm:rounded-2xl border border-amber-400/20 bg-amber-500/5 p-4 text-sm text-amber-100">
                <p className="font-semibold flex items-center gap-2 mb-1">
                  <AlertCircle className="w-4 h-4" /> Quota pressure detected
                </p>
                <p className="text-amber-200/80">
                  Your free tier usage is approaching capacity. You have used {aiQuotaPercent}% of AI messages and {syncQuotaPercent}% of syncs today.
                  Upgrade to avoid service degradation.
                </p>
              </div>
            )}

            <div className="space-y-8">
              {/* AI Copilot Tracker */}
              <div>
                <div className="flex justify-between items-end mb-3">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Sparkles className="w-4 h-4 text-primary" />
                    </div>
                    <div>
                      <span className="text-xs sm:text-sm font-bold text-white block">AI Copilot Intelligence</span>
                      <span className="text-[10px] sm:text-xs text-slate-500 font-medium">Daily inference limit</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-xl sm:text-2xl font-black text-white">{stats?.daily_ai_count}</span>
                    <span className="text-slate-500 text-sm font-medium"> / {stats?.daily_ai_limit}</span>
                  </div>
                </div>
                <div className="h-2 sm:h-3 w-full bg-slate-800 rounded-full overflow-hidden shadow-inner">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(100, aiProgress)}%` }}
                    className={`h-full relative ${aiProgress > 80 ? 'bg-amber-500' : 'bg-primary'}`}
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent to-white/20" />
                  </motion.div>
                </div>
              </div>

              {/* Sync Tracker */}
              <div>
                <div className="flex justify-between items-end mb-3">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-emerald-500/10">
                      <BarChart3 className="w-4 h-4 text-emerald-400" />
                    </div>
                    <div>
                      <span className="text-xs sm:text-sm font-bold text-white block">Calendar Integrations</span>
                      <span className="text-[10px] sm:text-xs text-slate-500 font-medium">Manual network syncs</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-xl sm:text-2xl font-black text-white">{stats?.daily_sync_count}</span>
                    <span className="text-slate-500 text-sm font-medium"> / {stats?.daily_sync_limit}</span>
                  </div>
                </div>
                <div className="h-2 sm:h-3 w-full bg-slate-800 rounded-full overflow-hidden shadow-inner">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(100, syncProgress)}%` }}
                    className={`h-full relative ${syncProgress > 80 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent to-white/20" />
                  </motion.div>
                </div>
              </div>
            </div>
            
            <div className="mt-8 p-3 sm:p-4 rounded-xl bg-slate-900/40 border border-slate-800/40 flex items-start gap-3">
              <AlertCircle className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
              <p className="text-[11px] sm:text-xs font-medium text-slate-400/80 leading-relaxed">
                Daily usage counters automatically reset at midnight UTC.
                {stats?.quota_reset_at ? (
                  <> Your next refresh is scheduled for <strong className="text-slate-300">{new Date(stats.quota_reset_at).toLocaleString('en-US', { timeZone: 'UTC', hour12: false })} UTC</strong>.</>
                ) : null}
              </p>
            </div>

          </div>
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          <div className="p-5 rounded-xl sm:rounded-2xl bg-indigo-500/5 border border-indigo-500/10">
            <h3 className="text-xs font-black text-white uppercase tracking-widest mb-4 flex items-center gap-2">
              <Zap className="w-3.5 h-3.5 text-indigo-400" /> Need More Power?
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              Free tier accounts are designed for casual scheduling. Upgrading to a Professional tier multiplies your limits by 20x.
            </p>
            <a 
              href="/pricing"
              className="block w-full text-center px-4 py-2.5 rounded-lg bg-indigo-600 text-white text-xs font-bold uppercase tracking-wider hover:bg-indigo-500 transition-colors"
            >
              View Upgrades
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
