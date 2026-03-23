"use client";

import { useState } from "react";
import { useAuthContext } from "@/app/providers/auth-provider";
import { setConsent } from "@/lib/api";
import { motion } from "framer-motion";
import { User, Shield, Bell, Eye, Loader2, Check } from "lucide-react";

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
      <motion.div variants={itemVariants} className="bg-slate-950/50 border border-slate-800 rounded-2xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <User className="w-5 h-5 text-primary" /> Profile
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Email</p>
            <p className="text-slate-200 font-medium">{settingsUser?.email || settingsUser?.sub || "admin"}</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Full Name</p>
            <p className="text-slate-200 font-medium">{settingsUser?.full_name || "Administrator"}</p>
          </div>
        </div>
      </motion.div>

      {/* Consent Management */}
      <motion.div variants={itemVariants} className="bg-slate-950/50 border border-slate-800 rounded-2xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-primary" /> Privacy & Consent
        </h2>
        <div className="space-y-3">
          {CONSENT_TYPES.map((item) => (
            <div key={item.key} className="flex items-center justify-between p-4 rounded-xl bg-slate-900/50 border border-slate-800">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 p-2 rounded-lg bg-slate-800 text-slate-400">
                  <item.icon className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-200">{item.label}</p>
                  <p className="text-xs text-slate-500">{item.description}</p>
                </div>
              </div>
              <button
                onClick={() => handleToggle(item.key)}
                disabled={saving === item.key}
                className={`relative w-12 h-7 rounded-full transition-colors duration-200 ${consents[item.key] ? "bg-primary" : "bg-slate-700"}`}
              >
                {saving === item.key ? (
                  <Loader2 className="w-4 h-4 animate-spin absolute top-1.5 left-4 text-white" />
                ) : saved === item.key ? (
                  <Check className="w-4 h-4 absolute top-1.5 text-white" style={{ left: consents[item.key] ? "1.5rem" : "0.25rem" }} />
                ) : (
                  <span className={`absolute top-1 left-1 w-5 h-5 bg-white rounded-full transition-transform duration-200 ${consents[item.key] ? "translate-x-5" : ""}`} />
                )}
              </button>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Danger Zone */}
      <motion.div variants={itemVariants} className="bg-slate-950/50 border border-red-900/30 rounded-2xl p-6">
        <h2 className="text-lg font-semibold text-red-400 mb-4">Danger Zone</h2>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-200">Sign out of your account</p>
            <p className="text-xs text-slate-500">You will be redirected to the login page</p>
          </div>
          <button
            onClick={logout}
            className="px-4 py-2 rounded-xl text-sm font-medium text-red-400 border border-red-900/50 hover:bg-red-900/20 transition-colors"
          >
            Sign Out
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}
