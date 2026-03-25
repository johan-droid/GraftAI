"use client";

import { useState } from "react";
import { useAuthContext } from "@/app/providers/auth-provider";
import { setConsent } from "@/lib/api";
import { motion } from "framer-motion";
import { User, Shield, Bell, Eye, Loader2, Check } from "lucide-react";
import { cn } from "@/lib/utils";

const CONSENT_TYPES = [
  { key: "analytics", label: "Analytics & Usage Data", description: "Help us improve by sharing anonymized usage data", icon: Eye },
  { key: "notifications", label: "Email Notifications", description: "Receive booking reminders and AI insights via email", icon: Bell },
  { key: "ai_training", label: "AI Model Training", description: "Allow your interactions to improve our AI models", icon: Shield },
];

type SettingsUser = { full_name?: string; email?: string; sub?: string } | null;

export default function SettingsPage() {
  const { user, logout } = useAuthContext();
  const settingsUser = user as SettingsUser;
  const [consents, setConsents] = useState<Record<string, boolean>>({
    analytics: true,
    notifications: true,
    ai_training: false,
  });
  const [saving, setSaving] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);

  const handleToggle = async (key: string) => {
    const newValue = !consents[key];
    setSaving(key);
    try {
      await setConsent(key, newValue);
      setConsents((prev) => ({ ...prev, [key]: newValue }));
      setSaved(key);
      setTimeout(() => setSaved(null), 2000);
    } catch (err) {
      console.error("Failed to update consent:", err);
    } finally {
      setSaving(null);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
  };
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-8">
      <header>
        <h1 className="text-3xl font-bold tracking-tight text-white mb-1">Settings</h1>
        <p className="text-slate-400">Manage your account preferences and privacy</p>
      </header>

      {/* Profile Section */}
      <motion.div variants={itemVariants} className="bg-white/40 dark:bg-slate-950/40 backdrop-blur-md border border-slate-200/60 dark:border-slate-800/60 rounded-[2rem] p-8 shadow-xl">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-3">
          <div className="p-2 rounded-xl bg-primary/10 text-primary">
            <User className="w-5 h-5" />
          </div>
          Profile Information
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-800/50 group transition-all hover:border-primary/30">
            <p className="text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em] font-bold mb-2">Email Address</p>
            <p className="text-slate-700 dark:text-slate-200 font-semibold">{settingsUser?.email || settingsUser?.sub || "admin"}</p>
          </div>
          <div className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-800/50 group transition-all hover:border-primary/30">
            <p className="text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em] font-bold mb-2">Full Name</p>
            <p className="text-slate-700 dark:text-slate-200 font-semibold">{settingsUser?.full_name || "Administrator"}</p>
          </div>
        </div>
      </motion.div>

      {/* Consent Management */}
      <motion.div variants={itemVariants} className="bg-white/40 dark:bg-slate-950/40 backdrop-blur-md border border-slate-200/60 dark:border-slate-800/60 rounded-[2rem] p-8 shadow-xl">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-3">
          <div className="p-2 rounded-xl bg-violet-500/10 text-violet-500">
            <Shield className="w-5 h-5" />
          </div>
          Privacy & Consent
        </h2>
        <div className="space-y-4">
          {CONSENT_TYPES.map((item) => (
            <div key={item.key} className="flex items-center justify-between p-5 rounded-3xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-800/50 transition-all hover:shadow-md">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-2xl bg-white dark:bg-slate-800 text-slate-400 border border-slate-100 dark:border-slate-700 shadow-sm">
                  <item.icon className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-sm font-bold text-slate-800 dark:text-slate-200">{item.label}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-500 font-medium">{item.description}</p>
                </div>
              </div>
              
              <button
                onClick={() => handleToggle(item.key)}
                disabled={saving === item.key}
                className={cn(
                  "relative w-14 h-8 rounded-full transition-all duration-300 shadow-inner group",
                  consents[item.key] ? "bg-primary shadow-primary/20" : "bg-slate-300 dark:bg-slate-700"
                )}
              >
                <div className={cn(
                  "absolute top-1 left-1 w-6 h-6 bg-white rounded-full transition-all duration-300 shadow-lg flex items-center justify-center",
                  consents[item.key] ? "translate-x-6" : "translate-x-0"
                )}>
                  {saving === item.key ? (
                    <Loader2 className="w-3 h-3 animate-spin text-primary" />
                  ) : saved === item.key ? (
                    <Check className="w-3 h-3 text-emerald-500" />
                  ) : null}
                </div>
              </button>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Danger Zone */}
      <motion.div variants={itemVariants} className="bg-red-50/50 dark:bg-red-950/10 border border-red-100 dark:border-red-900/30 rounded-[2rem] p-8 shadow-sm">
        <h2 className="text-lg font-bold text-red-600 dark:text-red-400 mb-6 flex items-center gap-3">
           Danger Zone
        </h2>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <p className="text-sm font-bold text-slate-800 dark:text-slate-200">Sign out of your account</p>
            <p className="text-xs text-slate-500 dark:text-slate-500 font-medium">You will be redirected to the login page securely.</p>
          </div>
          <button
            onClick={logout}
            className="w-full sm:w-auto px-8 py-3 rounded-full text-sm font-bold text-red-600 border-2 border-red-100 dark:border-red-900/30 hover:bg-red-600 hover:text-white dark:hover:bg-red-900/50 transition-all shadow-sm"
          >
            Sign Out
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}
