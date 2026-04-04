"use client";

import { useState, useEffect } from "react";
import { useAuthContext } from "@/app/providers/auth-provider";
import { syncUserConsent, deleteAccount } from "@/lib/api";
import { motion } from "framer-motion";
import { User, Shield, Bell, Eye, Loader2, Check } from "lucide-react";
import { cn } from "@/lib/utils";

const CONSENT_TYPES = [
  { key: "consent_analytics", label: "Analytics & Usage Data", description: "Help us improve by sharing anonymized usage data", icon: Eye },
  { key: "consent_notifications", label: "Email Notifications", description: "Receive booking reminders and AI insights via email", icon: Bell },
  { key: "consent_ai_training", label: "AI Model Training", description: "Allow your interactions to improve our AI models", icon: Shield },
];

type SettingsUser = { 
  full_name?: string; 
  email?: string; 
  sub?: string;
  consent_analytics?: boolean;
  consent_notifications?: boolean;
  consent_ai_training?: boolean;
} | null;

export default function SettingsPage() {
  const { user, refresh, logout } = useAuthContext();
  const settingsUser = user as SettingsUser;
  
  // Initialize from user object if available, else defaults
  const [consents, setConsents] = useState<Record<string, boolean>>({
    consent_analytics: settingsUser?.consent_analytics ?? true,
    consent_notifications: settingsUser?.consent_notifications ?? true,
    consent_ai_training: settingsUser?.consent_ai_training ?? false,
  });

  const [saving, setSaving] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Sync state if user object updates
  useEffect(() => {
    if (settingsUser) {
      setConsents({
        consent_analytics: settingsUser.consent_analytics ?? true,
        consent_notifications: settingsUser.consent_notifications ?? true,
        consent_ai_training: settingsUser.consent_ai_training ?? false,
      });
    }
  }, [settingsUser]);

  const handleDeleteAccount = async () => {
    setDeleting(true);
    try {
      await deleteAccount();
      window.location.href = "/register";
    } catch (err) {
      console.error("Failed to delete account:", err);
      alert("Failed to delete account. Please try again.");
    } finally {
      setDeleting(false);
    }
  };

  const handleToggle = async (key: string) => {
    const newValue = !consents[key];
    setSaving(key);
    try {
      // Use the new persistent sync API
      await syncUserConsent({ [key]: newValue });
      setConsents((prev) => ({ ...prev, [key]: newValue }));
      setSaved(key);
      
      // Refresh context so other components see the update
      await refresh();
      
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

  // Helper: Extract Initials
  const getInitials = (name?: string, email?: string) => {
    if (name) return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
    if (email) return email[0].toUpperCase();
    return "??";
  };

  // Helper: Extract Domain & Org Info
  const getProfileExtras = (email?: string) => {
    if (!email) return { domain: "Sovereign Auth", type: "Autonomous", isCorporate: false };
    const domain = email.split("@")[1]?.toLowerCase() || "unknown";
    const isCorporate = !["gmail.com", "outlook.com", "yahoo.com", "icloud.com", "hotmail.com"].includes(domain);
    return {
      domain: domain.split(".")[0].toUpperCase() + "." + domain.split(".").slice(1).join("."),
      type: isCorporate ? "Enterprise Node" : "Personal Instance",
      isCorporate
    };
  };

  const initials = getInitials(settingsUser?.full_name, settingsUser?.email);
  const { domain, type, isCorporate } = getProfileExtras(settingsUser?.email);

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6 md:space-y-8 pb-10">
      <header>
        <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold tracking-tight text-white mb-2 font-outfit">
          Settings & Identity
        </h1>
        <p className="text-xs md:text-sm text-slate-400 font-medium">Configure your core system parameters and security protocols</p>
      </header>

      {/* Premium Profile Box */}
      <motion.div 
        variants={itemVariants} 
        className="bg-slate-950/40 backdrop-blur-2xl border border-slate-800/60 rounded-[2rem] md:rounded-[3rem] p-6 md:p-10 shadow-2xl relative overflow-hidden group"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-primary/5 pointer-events-none" />
        
        {/* Animated Background Mesh */}
        <div className="absolute -top-24 -right-24 w-64 h-64 bg-primary/20 rounded-full blur-[100px] animate-pulse" />
        <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-violet-600/10 rounded-full blur-[100px] animate-pulse delay-700" />

        <div className="flex flex-col md:flex-row items-center md:items-start gap-8 md:gap-12 relative z-10">
          {/* Avatar Area */}
          <div className="relative">
            <motion.div 
              whileHover={{ scale: 1.05, rotate: 2 }}
              className="w-24 h-24 md:w-32 md:h-32 rounded-[2rem] md:rounded-[2.5rem] bg-gradient-to-br from-primary to-violet-600 p-1 shadow-[0_0_40px_rgba(79,70,229,0.4)]"
            >
              <div className="w-full h-full rounded-[1.8rem] md:rounded-[2.3rem] bg-slate-950 flex items-center justify-center overflow-hidden relative">
                <span className="text-3xl md:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white to-white/40 tracking-tighter">
                  {initials}
                </span>
                {/* Micro-sparkle effect */}
                <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/stardust.png')] opacity-10" />
              </div>
            </motion.div>
            
            {/* Online Status Badge */}
            <div className="absolute -bottom-1 -right-1 w-6 h-6 md:w-8 md:h-8 rounded-full bg-slate-950 border-2 border-slate-900 p-1 flex items-center justify-center">
              <div className="w-full h-full rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.6)] animate-pulse" />
            </div>
          </div>

          {/* User Details Area */}
          <div className="flex-1 text-center md:text-left">
            <div className="mb-6">
              <h2 className="text-3xl md:text-4xl font-black text-white tracking-tight mb-1 font-outfit">
                {settingsUser?.full_name || "Sovereign User"}
              </h2>
              <div className="flex flex-wrap items-center justify-center md:justify-start gap-3 mt-3">
                <span className="px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-[10px] md:text-xs font-bold text-primary uppercase tracking-widest">
                  {type}
                </span>
                <span className="px-3 py-1 rounded-full bg-slate-900/60 border border-slate-800 text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-widest">
                  {isCorporate ? "Verified Org" : "Direct Access"}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 md:p-5 rounded-2xl md:rounded-[1.5rem] bg-slate-900/40 border border-slate-800/60 hover:bg-slate-900/60 hover:border-primary/20 transition-all group/stat">
                <p className="text-[9px] md:text-[10px] text-slate-500 uppercase tracking-[0.2em] font-bold mb-2 flex items-center gap-2">
                  <Shield className="w-3 h-3 text-primary/60" />
                  Primary Node (Email)
                </p>
                <p className="text-xs md:text-sm text-slate-200 font-bold truncate group-hover/stat:text-white transition-colors">
                    {settingsUser?.email || settingsUser?.sub || "root@graftai.tech"}
                </p>
              </div>
              
              <div className="p-4 md:p-5 rounded-2xl md:rounded-[1.5rem] bg-slate-900/40 border border-slate-800/60 hover:bg-slate-900/60 hover:border-violet-500/20 transition-all group/stat">
                <p className="text-[9px] md:text-[10px] text-slate-500 uppercase tracking-[0.2em] font-bold mb-2 flex items-center gap-2">
                  <Eye className="w-3 h-3 text-violet-500/60" />
                  Data Jurisdiction
                </p>
                <p className="text-xs md:text-sm text-slate-200 font-bold group-hover/stat:text-white transition-colors uppercase">
                  {domain}
                </p>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Consent Management */}
      <motion.div variants={itemVariants} className="bg-slate-950/40 backdrop-blur-xl border border-slate-800/60 rounded-[1.5rem] md:rounded-[2.5rem] p-5 md:p-8 shadow-2xl relative overflow-hidden group">
        <div className="absolute inset-0 bg-gradient-to-br from-violet-500/5 to-transparent pointer-events-none" />
        <h2 className="text-sm md:text-lg font-bold text-white mb-4 md:mb-6 flex items-center gap-3 relative z-10">
          <div className="p-1.5 md:p-2 rounded-xl bg-violet-500/20 text-violet-400 border border-violet-500/20">
            <Shield className="w-4 h-4 md:w-5 md:h-5" />
          </div>
          Privacy & Consent
        </h2>
        <div className="space-y-2 md:space-y-3 relative z-10">
          {CONSENT_TYPES.map((item) => (
            <div 
                key={item.key} 
                className="flex items-center justify-between p-4 md:p-5 rounded-[1.2rem] md:rounded-[2rem] bg-slate-900/30 border border-slate-800/60 transition-all hover:bg-slate-900/50 hover:border-slate-700 active:scale-[0.99]"
            >
              <div className="flex items-center gap-3 md:gap-5">
                <div className="p-2.5 md:p-3.5 rounded-xl md:rounded-2xl bg-slate-900 text-slate-400 border border-slate-800 shadow-inner group-hover:text-primary transition-colors">
                  <item.icon className="w-4 h-4 md:w-5 md:h-5" />
                </div>
                <div>
                  <p className="text-xs md:text-sm font-bold text-slate-100 leading-tight">{item.label}</p>
                  <p className="text-[10px] md:text-xs text-slate-500 font-medium leading-tight opacity-70">{item.description}</p>
                </div>
              </div>
              
              <button
                onClick={() => handleToggle(item.key)}
                disabled={saving === item.key}
                className={cn(
                  "relative w-12 h-7 md:w-16 md:h-9 rounded-full transition-all duration-500 p-0.5 md:p-1 font-medium overflow-hidden group/btn",
                  consents[item.key] 
                    ? "bg-primary shadow-[0_0_20px_rgba(138,43,226,0.3)]" 
                    : "bg-slate-800 border border-slate-700"
                )}
              >
                {/* Glow Background for Active State */}
                {consents[item.key] && (
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover/btn:translate-x-[100%] transition-transform duration-1000" />
                )}

                <motion.div 
                    layout
                    className={cn(
                        "w-5 h-5 md:w-7 md:h-7 rounded-full transition-all duration-500 shadow-2xl flex items-center justify-center relative z-10",
                        consents[item.key] 
                            ? "ml-5 md:ml-7 bg-white" 
                            : "ml-0 bg-slate-600"
                    )}
                >
                  {saving === item.key ? (
                    <Loader2 className="w-3 h-3 md:w-4 md:h-4 animate-spin text-primary" />
                  ) : saved === item.key ? (
                    <Check className="w-3 h-3 md:w-4 md:h-4 text-emerald-500" />
                  ) : (
                    <div className={cn(
                        "w-1 h-1 md:w-1.5 md:h-1.5 rounded-full transition-all duration-500",
                        consents[item.key] ? "bg-primary" : "bg-slate-400"
                    )} />
                  )}
                </motion.div>
              </button>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Danger Zone */}
      <motion.div variants={itemVariants} className="bg-red-950/5 border border-red-900/20 rounded-[1.5rem] md:rounded-[2rem] p-5 md:p-8 shadow-sm">
        <h2 className="text-sm md:text-lg font-bold text-red-500 mb-4 md:mb-6 flex items-center gap-3">
           Danger Zone
        </h2>
        
        <div className="space-y-4 md:space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div>
              <p className="text-xs md:text-sm font-bold text-slate-100">Sign out of your account</p>
              <p className="text-[10px] md:text-xs text-slate-500 font-medium">Safe session termination.</p>
            </div>
            <button
              onClick={logout}
              className="w-full sm:w-auto px-6 py-2 rounded-xl text-[11px] md:text-sm font-bold text-slate-400 border border-slate-800 hover:bg-slate-900 transition-all"
            >
              Sign Out
            </button>
          </div>

          <div className="pt-4 md:pt-6 border-t border-red-900/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div>
              <p className="text-xs md:text-sm font-bold text-red-500">Delete Account</p>
              <p className="text-[10px] md:text-xs text-slate-500 font-medium leading-tight">Permanently purge all data. This is irreversible.</p>
            </div>
            {!showDeleteConfirm ? (
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="w-full sm:w-auto px-6 py-2 rounded-xl text-[11px] md:text-sm font-bold text-red-500 border border-red-900/30 hover:bg-red-950 transition-all shadow-sm"
              >
                Delete Account
              </button>
            ) : (
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <button
                  disabled={deleting}
                  onClick={handleDeleteAccount}
                  className="flex-1 sm:flex-none px-4 py-2 rounded-xl text-[11px] md:text-sm font-bold bg-red-600 text-white hover:bg-red-700 transition-all"
                >
                  {deleting ? "Deleting..." : "Confirm"}
                </button>
                <button
                  disabled={deleting}
                  onClick={() => setShowDeleteConfirm(false)}
                  className="flex-1 sm:flex-none px-4 py-2 rounded-xl text-[11px] md:text-sm font-bold text-slate-400 hover:bg-slate-900 transition-all"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
