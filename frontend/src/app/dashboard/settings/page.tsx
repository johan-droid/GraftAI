"use client";

import { useState, useEffect } from "react";
import { User, Shield, Bell, Eye, Loader2, Check, Video, ExternalLink, RefreshCw } from "lucide-react";
import { syncUserConsent, deleteAccount, API_BASE_URL, syncCalendars } from "@/lib/api";
import { motion } from "framer-motion";
import { useAuthContext } from "@/app/providers/auth-provider";
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
  zoom_connected?: boolean;
  google_connected?: boolean;
  microsoft_connected?: boolean;
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
  const [syncing, setSyncing] = useState(false);
  const [syncSuccess, setSyncSuccess] = useState(false);

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

  const handleManualSync = async () => {
    setSyncing(true);
    try {
      await syncCalendars();
      setSyncSuccess(true);
      setTimeout(() => setSyncSuccess(false), 3000);
      await refresh(); // Refresh session flags
    } catch (err) {
      console.error("Manual sync failed:", err);
      alert("Failed to sync calendars. Please check your connections.");
    } finally {
      setSyncing(false);
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
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6 md:space-y-8">
      <header>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white mb-1 font-outfit">Settings</h1>
        <p className="text-xs md:text-sm text-slate-400 font-medium">Account preferences and security</p>
      </header>

      {/* Profile Section */}
      <motion.div variants={itemVariants} className="bg-slate-950/40 backdrop-blur-xl border border-slate-800/60 rounded-[1.5rem] md:rounded-[2.5rem] p-5 md:p-8 shadow-2xl relative overflow-hidden group">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent pointer-events-none" />
        <h2 className="text-sm md:text-lg font-bold text-white mb-4 md:mb-6 flex items-center gap-3 relative z-10">
          <div className="p-1.5 md:p-2 rounded-xl bg-primary/20 text-primary border border-primary/20">
            <User className="w-4 h-4 md:w-5 md:h-5" />
          </div>
          Profile Identity
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 relative z-10">
          <div className="p-4 md:p-5 rounded-2xl md:rounded-3xl bg-slate-900/40 border border-slate-800 transition-all hover:bg-slate-900/60 group">
            <p className="text-[9px] md:text-[10px] text-slate-500 uppercase tracking-[0.2em] font-bold mb-1 md:mb-2">Email Control</p>
            <p className="text-xs md:text-sm text-slate-200 font-semibold truncate">{settingsUser?.email || settingsUser?.sub || "admin"}</p>
          </div>
          <div className="p-4 md:p-5 rounded-2xl md:rounded-3xl bg-slate-900/40 border border-slate-800 transition-all hover:bg-slate-900/60 group">
            <p className="text-[9px] md:text-[10px] text-slate-500 uppercase tracking-[0.2em] font-bold mb-1 md:mb-2">Authenticated Name</p>
            <p className="text-xs md:text-sm text-slate-200 font-semibold">{settingsUser?.full_name || "Sovereign User"}</p>
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

      {/* Integrations Section */}
      <motion.div variants={itemVariants} className="bg-slate-950/40 backdrop-blur-xl border border-slate-800/60 rounded-[1.5rem] md:rounded-[2.5rem] p-5 md:p-8 shadow-2xl relative overflow-hidden group">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent pointer-events-none" />
        <h2 className="text-sm md:text-lg font-bold text-white mb-4 md:mb-6 flex items-center gap-3 relative z-10">
          <div className="p-1.5 md:p-2 rounded-xl bg-blue-500/20 text-blue-400 border border-blue-500/20">
            <Video className="w-4 h-4 md:w-5 md:h-5" />
          </div>
          Connected Ecosystem
        </h2>
        
        {/* Sync Trigger */}
        {(settingsUser?.google_connected || settingsUser?.microsoft_connected) && (
          <div className="mb-6 flex items-center justify-between p-4 rounded-2xl bg-primary/5 border border-primary/20">
            <div>
              <p className="text-xs font-bold text-white uppercase tracking-wider mb-1">Manual Force Sync</p>
              <p className="text-[10px] text-slate-500 font-medium">Coordinate all external schedules immediately.</p>
            </div>
            <button
              onClick={handleManualSync}
              disabled={syncing}
              className={cn(
                "px-5 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-2 transition-all",
                syncSuccess 
                  ? "bg-emerald-500 text-white" 
                  : "bg-primary text-white hover:bg-primary/80 active:scale-95 disabled:opacity-50"
              )}
            >
              {syncing ? (
                <> <Loader2 className="w-3.5 h-3.5 animate-spin" /> Syncing... </>
              ) : syncSuccess ? (
                <> <Check className="w-3.5 h-3.5" /> Synchronized </>
              ) : (
                <> <RefreshCw className="w-3.5 h-3.5" /> Sync Now </>
              )}
            </button>
          </div>
        )}
        
        <div className="space-y-4 relative z-10">
          {/* Zoom Integration */}
          <div className="p-5 md:p-6 rounded-[1.5rem] md:rounded-[2rem] bg-slate-900/40 border border-slate-800 transition-all hover:bg-slate-900/60">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-white flex items-center justify-center p-2 shadow-xl shadow-blue-500/10 text-black">
                   <Video className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm font-black text-white uppercase tracking-tight">Zoom Video Communications</p>
                  <p className="text-xs text-slate-500 font-medium">Generate native meeting links directly from GraftAI.</p>
                </div>
              </div>

              {settingsUser?.zoom_connected ? (
                <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold uppercase tracking-widest">
                  <Check className="w-3.5 h-3.5" />
                  Active Connection
                </div>
              ) : (
                <a 
                  href={`${API_BASE_URL}/auth/zoom/connect`}
                  className="w-full md:w-auto px-6 h-12 bg-white text-black rounded-xl text-xs font-black uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-slate-200 transition-all active:scale-95"
                >
                  Link Account <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
            </div>
          </div>

          {/* Google Calendar Integration */}
          <div className="p-5 md:p-6 rounded-[1.5rem] md:rounded-[2rem] bg-slate-900/40 border border-slate-800 transition-all hover:bg-slate-900/60">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-white flex items-center justify-center p-2 shadow-xl shadow-red-500/10">
                   <img src="https://www.gstatic.com/images/branding/product/1x/calendar_2020q4_48dp.png" className="w-6 h-6" alt="Google" />
                </div>
                <div>
                  <p className="text-sm font-black text-white uppercase tracking-tight">Google Calendar Service</p>
                  <p className="text-xs text-slate-500 font-medium">Sync availability and prevent external scheduling conflicts.</p>
                </div>
              </div>

              {settingsUser?.google_connected ? (
                <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold uppercase tracking-widest">
                  <Check className="w-3.5 h-3.5" />
                  Sovereign Sync Enabled
                </div>
              ) : (
                <a 
                  href={`${API_BASE_URL}/api/v1/auth/google/connect`}
                  className="w-full md:w-auto px-6 h-12 bg-white text-black rounded-xl text-xs font-black uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-slate-200 transition-all active:scale-95"
                >
                  Link Account <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
            </div>
          </div>

          {/* Microsoft Graph Integration */}
          <div className="p-5 md:p-6 rounded-[1.5rem] md:rounded-[2rem] bg-slate-900/40 border border-slate-800 transition-all hover:bg-slate-900/60">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-[#0078d4] flex items-center justify-center p-2 shadow-xl shadow-blue-500/10">
                   <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Microsoft_logo.svg/2048px-Microsoft_logo.svg.png" className="w-6 h-auto brightness-0 invert" alt="Microsoft" />
                </div>
                <div>
                  <p className="text-sm font-black text-white uppercase tracking-tight">Microsoft Graph (Outlook)</p>
                  <p className="text-xs text-slate-500 font-medium">Connect Outlook/Teams for Enterprise-grade coordination.</p>
                </div>
              </div>

              {settingsUser?.microsoft_connected ? (
                <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold uppercase tracking-widest">
                  <Check className="w-3.5 h-3.5" />
                  Sovereign Sync Enabled
                </div>
              ) : (
                <a 
                  href={`${API_BASE_URL}/api/v1/auth/microsoft/connect`}
                  className="w-full md:w-auto px-6 h-12 bg-white text-black rounded-xl text-xs font-black uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-slate-200 transition-all active:scale-95"
                >
                  Link Account <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
            </div>
          </div>
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
