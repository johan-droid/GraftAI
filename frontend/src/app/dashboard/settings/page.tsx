"use client";

import { useState, useEffect } from "react";
import { useAuthContext } from "@/app/providers/auth-provider";
import { setConsent } from "@/lib/api";
import { motion } from "framer-motion";
import {
  User, Shield, Bell, Eye, Loader2, Check, LogOut,
  KeyRound, Trash2, AlertTriangle, ChevronRight,
} from "lucide-react";
import { toast } from "@/components/ui/Toast";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

const CONSENT_CONFIG = [
  {
    key: "analytics",
    label: "Analytics & Usage Data",
    description: "Share anonymized usage data to help improve GraftAI. No personal content is shared.",
    icon: Eye,
    defaultEnabled: true,
  },
  {
    key: "notifications",
    label: "Email Notifications",
    description: "Receive booking reminders, meeting summaries, and AI insights via email.",
    icon: Bell,
    defaultEnabled: true,
  },
  {
    key: "ai_training",
    label: "AI Model Training",
    description: "Allow anonymized interaction patterns to improve AI scheduling accuracy. Opt out anytime.",
    icon: Shield,
    defaultEnabled: false,
  },
] as const;

type ConsentKey = (typeof CONSENT_CONFIG)[number]["key"];

type SettingsUser = { name?: string; email?: string; sub?: string } | null;

export default function SettingsPage() {
  const { user, logout } = useAuthContext();
  const settingsUser = user as SettingsUser;

  const initialConsents = Object.fromEntries(CONSENT_CONFIG.map(c => [c.key, c.defaultEnabled])) as Record<ConsentKey, boolean>;
  const [consents, setConsents] = useState<Record<ConsentKey, boolean>>(initialConsents);

  useEffect(() => {
    fetch("/api/user/preferences", { credentials: "include" })
      .then(res => res.json())
      .then(data => {
        if (data && data.consents) {
          setConsents(data.consents);
        } else {
          setConsents(initialConsents);
        }
      })
      .catch(err => {
        console.error("Failed to load preferences:", err);
        setConsents(initialConsents);
      });
  }, []);

  const [savingKey, setSavingKey]     = useState<ConsentKey | null>(null);
  const [savedKey, setSavedKey]       = useState<ConsentKey | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [changingPw, setChangingPw]   = useState(false);
  const [pwForm, setPwForm]           = useState({ current: "", next: "", confirm: "" });

  async function handleToggle(key: ConsentKey) {
    const next = !consents[key];
    setSavingKey(key);
    try {
      await setConsent(key, next);
      setConsents(prev => ({ ...prev, [key]: next }));
      setSavedKey(key);
      setTimeout(() => setSavedKey(null), 2200);
      toast.success(`${next ? "Enabled" : "Disabled"} ${key} preference.`);
    } catch {
      toast.error("Failed to update preference. Please try again.");
    } finally {
      setSavingKey(null);
    }
  }

  async function handleChangePassword(e: React.FormEvent) {
    e.preventDefault();
    if (pwForm.next !== pwForm.confirm) {
      toast.error("Passwords don't match.");
      return;
    }
    if (pwForm.next.length < 8) {
      toast.error("Password must be at least 8 characters.");
      return;
    }
    setChangingPw(true);
    try {
      const res = await fetch("/api/auth/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ current: pwForm.current, next: pwForm.next }),
      });
      if (!res.ok) throw new Error("Failed to update password.");
      setPwForm({ current: "", next: "", confirm: "" });
      toast.success("Password updated successfully.");
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setChangingPw(false);
    }
  }

  const item = { hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0 } };
  const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };

  return (
    <ErrorBoundary>
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-6 max-w-2xl">

        <motion.div variants={item}>
          <h1 className="text-h1 text-white">Settings</h1>
          <p className="text-sm mt-1 text-slate-400">
            Manage your account preferences and privacy
          </p>
        </motion.div>

        {/* ── Profile ── */}
        <motion.section variants={item} className="card p-6 space-y-4">
          <SectionHeader icon={User} title="Profile" />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <InfoField label="Full Name" value={settingsUser?.name ?? "Administrator"} />
            <InfoField label="Email Address" value={settingsUser?.email ?? settingsUser?.sub ?? "—"} />
          </div>
        </motion.section>

        {/* ── Password ── */}
        <motion.section variants={item} className="card p-6 space-y-4">
          <SectionHeader icon={KeyRound} title="Change Password" />
          <form onSubmit={handleChangePassword} className="space-y-3">
            <div>
              <label className="text-label block mb-1.5 text-slate-400">Current Password</label>
              <input
                className="input" type="password" autoComplete="current-password"
                placeholder="••••••••"
                value={pwForm.current}
                onChange={e => setPwForm(p => ({ ...p, current: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-label block mb-1.5 text-slate-400">New Password</label>
                <input
                  className="input" type="password" autoComplete="new-password"
                  placeholder="Min. 8 characters"
                  value={pwForm.next}
                  onChange={e => setPwForm(p => ({ ...p, next: e.target.value }))}
                />
              </div>
              <div>
                <label className="text-label block mb-1.5 text-slate-400">Confirm</label>
                <input
                  className="input" type="password" autoComplete="new-password"
                  placeholder="Repeat password"
                  value={pwForm.confirm}
                  onChange={e => setPwForm(p => ({ ...p, confirm: e.target.value }))}
                />
              </div>
            </div>
            <button type="submit" className="btn btn-surface text-sm" disabled={changingPw || !pwForm.current || !pwForm.next}>
              {changingPw ? <><Loader2 className="w-4 h-4 animate-spin" /> Updating…</> : "Update Password"}
            </button>
          </form>
        </motion.section>

        {/* ── Privacy & Consent ── */}
        <motion.section variants={item} className="card p-6 space-y-4">
          <SectionHeader icon={Shield} title="Privacy & Consent" />
          <div className="space-y-3">
            {CONSENT_CONFIG.map((item) => {
              const isSaving = savingKey === item.key;
              const isSaved  = savedKey === item.key;
              const enabled  = consents[item.key];

              return (
                <div
                  key={item.key}
                  className="flex items-center justify-between gap-4 p-4 rounded-xl transition-colors bg-slate-800 border border-white/10"
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 bg-slate-900">
                      <item.icon className="w-4 h-4 text-slate-400" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate text-white">{item.label}</p>
                      <p className="text-xs leading-relaxed mt-0.5 text-slate-400">
                        {item.description}
                      </p>
                    </div>
                  </div>

                  <button
                    className={`toggle flex-shrink-0 ${enabled ? "on" : ""}`}
                    onClick={() => handleToggle(item.key)}
                    disabled={isSaving}
                    aria-label={item.label}
                  >
                    {isSaving && (
                      <span className="absolute inset-0 flex items-center justify-center">
                        <Loader2 className="w-3 h-3 animate-spin text-amber-300" />
                      </span>
                    )}
                    {isSaved && !isSaving && (
                      <span className="absolute right-1 top-1/2 -translate-y-1/2">
                        <Check className="w-2.5 h-2.5 text-emerald-400" />
                      </span>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        </motion.section>

        {/* ── Danger Zone ── */}
        <motion.section variants={item}
          className="p-6 rounded-xl space-y-4 bg-red-500/5 border border-red-500/15"
        >
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <h2 className="text-sm font-bold text-red-400">Danger Zone</h2>
          </div>

          <DangerRow
            label="Sign Out"
            description="End your current session securely."
            action={
              <button className="btn btn-ghost text-sm" onClick={logout}>
                <LogOut className="w-4 h-4" /> Sign Out
              </button>
            }
          />

          <DangerRow
            label="Delete Account"
            description="Permanently delete your account and all data. This cannot be undone."
            action={
              !deleteConfirm ? (
                <button className="btn btn-danger text-sm" onClick={() => setDeleteConfirm(true)}>
                  <Trash2 className="w-4 h-4" /> Delete
                </button>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-red-400">Are you sure?</span>
                  <button className="btn btn-danger text-sm py-1.5 px-3 min-h-0"
                    onClick={() => toast.error("Account deletion requires contacting support.")}
                  >
                    Confirm
                  </button>
                  <button className="btn btn-ghost text-sm py-1.5 px-3 min-h-0"
                    onClick={() => setDeleteConfirm(false)}
                  >
                    Cancel
                  </button>
                </div>
              )
            }
          />
        </motion.section>
      </motion.div>
    </ErrorBoundary>
  );
}

function SectionHeader({ icon: Icon, title }: { icon: React.ElementType; title: string }) {
  return (
    <div className="flex items-center gap-2 mb-2">
      <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-slate-900">
        <Icon className="w-4 h-4 text-amber-300" />
      </div>
      <h2 className="text-sm font-semibold text-white">{title}</h2>
    </div>
  );
}

function InfoField({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 rounded-xl bg-slate-900 border border-white/10">
      <p className="text-label mb-1 text-slate-400">{label}</p>
      <p className="text-sm font-medium truncate text-white">{value}</p>
    </div>
  );
}

function DangerRow({ label, description, action }: { label: string; description: string; action: React.ReactNode }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 py-3 border-t border-red-500/15">
      <div>
        <p className="text-sm font-medium text-white">{label}</p>
        <p className="text-xs mt-0.5 text-slate-400">{description}</p>
      </div>
      {action}
    </div>
  );
}
