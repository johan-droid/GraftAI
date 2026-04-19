"use client";

import { useState, useEffect, useMemo } from "react";
import { 
  CreditCard, 
  Zap,
  Crown,
  CheckCircle2, 
  ArrowUpRight,
  Loader2,
  Search,
  Filter,
  DownloadCloud,
  X,
} from "lucide-react";
import { useAuth } from "@/app/providers/auth-provider";
import { apiClient } from "@/lib/api-client";
import Charts from "@/components/Analytics/Charts";

type UsageItem = { date: string; ai_count: number; sync_count: number; storage_bytes?: number | null };
type TransactionItem = { id: string; timestamp: string; method: string; amount?: number | null; currency?: string | null; status: string; description?: string | null };

export default function BillingPage() {
  const { user } = useAuth();
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [billingMessage, setBillingMessage] = useState<string | null>(null);

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
    try {
      setActionLoading("portal");
      if (stats?.subscription_status !== "active") {
        window.location.assign("/pricing");
        return;
      }

      const response = await apiClient.post<{ portal_url: string }>("/billing/stripe/create-portal-session");
      if (!response.portal_url) {
        throw new Error("Stripe billing portal is not available right now.");
      }

      window.location.assign(response.portal_url);
    } catch (err) {
      console.error("Portal redirect failed:", err);
      setBillingMessage(err instanceof Error ? err.message : "Could not process request. Please contact support if this persists.");
    } finally {
      setActionLoading(null);
    }
  };

  const handleUpgrade = () => {
    window.location.assign("/pricing");
  };

  // Usage + Transactions state
  const [usage, setUsage] = useState<UsageItem[] | null>(null);
  const [transactions, setTransactions] = useState<TransactionItem[] | null>(null);
  const [loadingUsage, setLoadingUsage] = useState(false);
  const [loadingTransactions, setLoadingTransactions] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        setLoadingUsage(true);
        setLoadingTransactions(true);
        const u = await apiClient.get<UsageItem[]>('/billing/usage/history', { params: { days: 30 } });
        const t = await apiClient.get<TransactionItem[]>('/billing/transactions/history', { params: { limit: 20 } });
        if (!mounted) return;
        setUsage(Array.isArray(u) ? u : []);
        setTransactions(Array.isArray(t) ? t : []);
      } catch (e) {
        console.warn('Failed to load billing usage/transactions', e);
        if (mounted) {
          setUsage([]);
          setTransactions([]);
        }
      } finally {
        if (mounted) {
          setLoadingUsage(false);
          setLoadingTransactions(false);
        }
      }
    };
    load();
    return () => { mounted = false; };
  }, []);

  const aiSeries = useMemo(() => (usage || []).map(u => ({ day: u.date, count: u.ai_count })), [usage]);
  const syncSeries = useMemo(() => (usage || []).map(u => ({ day: u.date, count: u.sync_count })), [usage]);

  const totalAi = useMemo(() => (usage || []).reduce((s, u) => s + (u.ai_count || 0), 0), [usage]);
  const aiPeak = useMemo(() => {
    if (!usage || usage.length === 0) return null;
    const max = usage.reduce((m, u) => (u.ai_count > m.ai_count ? u : m), usage[0]);
    return { day: max.date, value: max.ai_count };
  }, [usage]);

  const syncPeak = useMemo(() => {
    if (!usage || usage.length === 0) return null;
    const max = usage.reduce((m, u) => (u.sync_count > m.sync_count ? u : m), usage[0]);
    return { day: max.date, value: max.sync_count };
  }, [usage]);

  const formatCurrency = (amount?: number | null, currency?: string | null) => {
    if (amount == null) return "-";
    try {
      // If currency looks like a 3-letter code, use Intl, otherwise prefix
      if (currency && currency.length === 3) {
        return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(amount);
      }
    } catch (e) {
      // fall through
    }
    return `${currency ?? '$'}${amount}`;
  };

  const formatBytes = (n?: number | null) => {
    if (!n && n !== 0) return '-';
    const v = Number(n || 0);
    if (v < 1024) return `${v} B`;
    if (v < 1024 * 1024) return `${Math.round(v / 1024)} KB`;
    if (v < 1024 * 1024 * 1024) return `${Math.round(v / (1024 * 1024))} MB`;
    return `${Math.round(v / (1024 * 1024 * 1024))} GB`;
  };

  const filteredTransactions = useMemo(() => {
    if (!transactions) return [] as TransactionItem[];
    let arr = transactions.slice();
    if (statusFilter && statusFilter !== 'all') {
      const sf = statusFilter.toLowerCase();
      arr = arr.filter(t => (t.status ?? '').toLowerCase().includes(sf));
    }
    if (searchQuery && searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase();
      arr = arr.filter(t => ((t.description ?? t.method ?? '') as string).toLowerCase().includes(q) || (t.id ?? '').toLowerCase().includes(q));
    }
    return arr;
  }, [transactions, statusFilter, searchQuery]);

  const exportTransactionsCSV = () => {
    const rows = (transactions || []).map(tx => ({
      id: tx.id,
      timestamp: tx.timestamp,
      method: tx.method,
      amount: tx.amount ?? '',
      currency: tx.currency ?? '',
      status: tx.status,
      description: tx.description ?? '',
    }));
    const header = Object.keys(rows[0] || { id: 'id' });
    const csv = [header.join(','), ...rows.map(r => header.map(h => `"${String((r as any)[h] ?? '').replace(/"/g, '""')}"`).join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transactions-${new Date().toISOString().slice(0,10)}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

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
                  aria-label={stats?.subscription_status === 'active' ? 'Manage billing' : 'Upgrade plan'}
                className="w-full sm:w-auto min-h-11 px-4 sm:px-6 py-2.5 sm:py-3 rounded-xl bg-slate-900 border border-slate-800 text-white text-xs font-black uppercase tracking-widest hover:bg-slate-800 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading === 'portal' ? <Loader2 className="w-3 h-3 animate-spin" /> : <CreditCard className="w-3.5 h-3.5" />}
                  {stats?.subscription_status === 'active' ? 'Manage Billing' : 'Upgrade Plan'}
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
                <li>1. Pick a plan and complete secure Stripe checkout from the pricing page.</li>
                <li>2. Stripe processes the payment and creates the subscription.</li>
                <li>3. Stripe sends a webhook to our backend at <code>/api/v1/billing/stripe/webhook</code>.</li>
                <li>4. The backend updates your user record, activates the plan, and stores subscription info.</li>
                <li>5. Renewals happen automatically monthly until you cancel in the billing portal.</li>
                <li>6. Return here anytime to open the Stripe customer portal or upgrade again.</li>
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

      {/* Usage / Telemetry Section */}
      <div className="mt-8 rounded-xl border border-slate-800/60 bg-slate-950/40 p-4 sm:p-6">
        <h3 className="text-sm font-bold uppercase tracking-wide text-slate-300 mb-3">Usage</h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <div className="bg-transparent p-3 rounded-md">
              <div className="mb-2 flex items-center justify-between">
                <div className="text-xs text-slate-400">AI Requests (last 30 days)</div>
                <div className="text-xs text-slate-400">{loadingUsage ? 'Loading…' : `${aiSeries.length} days`}</div>
              </div>
              {loadingUsage ? (
                <div className="h-48 flex items-center justify-center text-slate-400">Loading chart…</div>
              ) : (
                <Charts.MeetingsLine data={aiSeries} />
              )}
            </div>

            <div className="bg-transparent p-3 rounded-md mt-4">
              <div className="mb-2 flex items-center justify-between">
                <div className="text-xs text-slate-400">Sync Events (last 30 days)</div>
                <div className="text-xs text-slate-400">{loadingUsage ? 'Loading…' : `${syncSeries.length} days`}</div>
              </div>
              {loadingUsage ? (
                <div className="h-36 flex items-center justify-center text-slate-400">Loading chart…</div>
              ) : (
                <Charts.MeetingsBar data={syncSeries} />
              )}
            </div>
          </div>

          <div className="lg:col-span-1">
            <div className="p-3 rounded-md border border-slate-800/40 bg-slate-900/30">
              <h4 className="text-xs text-slate-300 font-bold mb-2">Summary</h4>
              <div className="grid grid-cols-2 gap-2">
                <div className="text-xs text-slate-400">AI today</div>
                <div className="text-sm font-bold text-white">{stats?.daily_ai_count ?? 0}</div>
                <div className="text-xs text-slate-400">AI remaining</div>
                <div className="text-sm font-bold text-white">{stats?.ai_remaining ?? 0}</div>
                <div className="text-xs text-slate-400">Sync today</div>
                <div className="text-sm font-bold text-white">{stats?.daily_sync_count ?? 0}</div>
                <div className="text-xs text-slate-400">Sync remaining</div>
                <div className="text-sm font-bold text-white">{stats?.sync_remaining ?? 0}</div>
              </div>
              <div className="mt-3 text-xs text-slate-400">
                <div>30d total: <span className="font-bold text-white">{totalAi}</span></div>
                <div className="mt-1">AI peak: <span className="font-bold text-white">{aiPeak ? `${aiPeak.value} on ${new Date(aiPeak.day).toLocaleDateString()}` : '—'}</span></div>
                <div className="mt-1">Sync peak: <span className="font-bold text-white">{syncPeak ? `${syncPeak.value} on ${new Date(syncPeak.day).toLocaleDateString()}` : '—'}</span></div>
              </div>
            </div>
          </div>
        </div>

        {/* Transactions */}
        <div className="mt-6">
          <h3 className="text-sm font-bold uppercase tracking-wide text-slate-300 mb-3">Transactions</h3>

          <div className="mb-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <div className="relative w-full sm:w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search transactions or ID"
                  className="w-full pl-10 pr-10 py-2 bg-slate-900/10 border border-slate-800/40 rounded-md text-sm text-slate-200"
                />
                {searchQuery && (
                  <button onClick={() => setSearchQuery("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 p-1">
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>

              <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="bg-slate-900/10 border border-slate-800/40 text-sm text-slate-200 px-3 py-2 rounded-md">
                <option value="all">All statuses</option>
                <option value="success">Success</option>
                <option value="approved">Approved</option>
                <option value="pending">Pending</option>
                <option value="failed">Failed</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <button onClick={exportTransactionsCSV} className="inline-flex items-center gap-2 text-sm px-3 py-2 bg-slate-900/60 border border-slate-800/40 rounded-md hover:bg-slate-900">
                <DownloadCloud className="w-4 h-4" /> Export CSV
              </button>
            </div>
          </div>

          {loadingTransactions ? (
            <div className="space-y-3">
              {[1,2,3].map(n => (
                <div key={n} className="p-3 rounded-md bg-slate-900/20 border border-slate-800/30 animate-pulse">
                  <div className="h-4 bg-slate-800/40 rounded w-2/3 mb-2" />
                  <div className="h-3 bg-slate-800/30 rounded w-1/2" />
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {(filteredTransactions && filteredTransactions.length > 0) ? (
                filteredTransactions.map(tx => (
                  <div key={tx.id} className="p-3 rounded-md bg-slate-900/30 border border-slate-800/40">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-semibold text-white">{tx.description ?? tx.method}</div>
                        <div className="text-xs text-slate-400">{new Date(tx.timestamp).toLocaleString()}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-bold text-white">{formatCurrency(tx.amount ?? undefined, tx.currency ?? undefined)}</div>
                        <div className={`text-xs ${tx.status === 'approved' || tx.status === 'success' ? 'text-emerald-400' : 'text-amber-400'}`}>{tx.status}</div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-slate-400">No recent transactions.</div>
              )}
            </div>
          )}
        </div>
      </div>

    </div>
  );
}
