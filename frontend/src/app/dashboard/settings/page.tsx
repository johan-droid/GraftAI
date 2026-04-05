"use client";

import { useState } from "react";
import { useAuthContext } from "@/app/providers/auth-provider";
import { setConsent } from "@/lib/api";
import { motion } from "framer-motion";
import {
  User,
  Shield,
  Bell,
  Eye,
  Loader2,
  Check,
  LogOut,
  Clock,
  Globe,
  Link2,
  ChevronRight,
  Zap,
  ExternalLink,
} from "lucide-react";
import { cn } from "@/lib/utils";

const STAGGER = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.07 } },
};
const ITEM = {
  hidden: { opacity: 0, y: 14 },
  visible: { opacity: 1, y: 0 },
};

const NAV_SECTIONS = ["Profile", "Availability", "Integrations", "Privacy", "Notifications", "Danger zone"];

function Toggle({ on, onChange, loading }: { on: boolean; onChange: () => void; loading?: boolean }) {
  return (
    <button
      onClick={onChange}
      disabled={loading}
      aria-label={on ? "Disable setting" : "Enable setting"}
      className={cn(
        "relative w-11 h-6 rounded-full transition-all shrink-0",
        on ? "bg-indigo-600 shadow-lg shadow-indigo-600/20" : "bg-white/10 border border-white/15"
      )}
    >
      <div
        className={cn(
          "absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-all flex items-center justify-center shadow-sm",
          on ? "translate-x-5" : "translate-x-0"
        )}
      >
        {loading && <Loader2 className="w-2.5 h-2.5 animate-spin text-indigo-500" />}
      </div>
    </button>
  );
}

function Section({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-white/[0.07] bg-white/[0.02] overflow-hidden">
      <div className="px-6 py-4 border-b border-white/[0.05]">
        <h2 className="text-sm font-bold text-white">{title}</h2>
        {description && <p className="text-xs text-slate-500 mt-0.5">{description}</p>}
      </div>
      <div className="divide-y divide-white/[0.04]">{children}</div>
    </div>
  );
}

function SettingRow({ icon: Icon, label, description, children }: {
  icon?: React.ComponentType<{ className?: string }>;
  label: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-4 px-6 py-4">
      {Icon && <Icon className="w-4 h-4 text-slate-500 shrink-0" />}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-200">{label}</p>
        {description && <p className="text-xs text-slate-500 mt-0.5">{description}</p>}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

export default function SettingsPage() {
  const { user, logout } = useAuthContext();
  const typedUser = user as { name?: string; email?: string } | null;
  const bookingSlug = typedUser?.email?.split("@")[0] ?? "you";

  const [activeSection] = useState("Profile");
  const [consents, setConsents] = useState({ analytics: true, notifications: true, ai_training: false });
  const [saving, setSaving] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const [availability, setAvailability] = useState({
    weekdays: true,
    saturday: false,
    sunday: false,
    startHour: "09:00",
    endHour: "18:00",
  });

  const toggleConsent = async (key: keyof typeof consents) => {
    const next = !consents[key];
    setSaving(key);
    try {
      await setConsent(key, next);
      setConsents((p) => ({ ...p, [key]: next }));
      setSaved(key);
      setTimeout(() => setSaved(null), 2000);
    } catch {
      // empty
    } finally {
      setSaving(null);
    }
  };

  const userInitials = typedUser?.name
    ? typedUser.name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : typedUser?.email?.[0]?.toUpperCase() ?? "U";

  return (
    <div className="p-5 md:p-7 max-w-[900px] mx-auto">
      <motion.div variants={STAGGER} initial="hidden" animate="visible" className="space-y-6">

        <motion.div variants={ITEM}>
          <h1 className="text-2xl font-bold text-white tracking-tight">Settings</h1>
          <p className="text-slate-500 text-sm mt-0.5">Manage your account, availability and integrations</p>
        </motion.div>

        <motion.div variants={ITEM}>
          <div className="rounded-xl border border-slate-800/60 bg-slate-950/40 p-6 md:p-8 shadow-2xl relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-primary/5 pointer-events-none" />
            <div className="absolute -top-24 -right-24 w-64 h-64 bg-primary/20 rounded-full blur-[100px] animate-pulse" />
            <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-violet-600/10 rounded-full blur-[100px] animate-pulse delay-700" />

            <div className="flex flex-col md:flex-row items-center md:items-start gap-8 md:gap-12 relative z-10">
              <div className="relative">
                <motion.div whileHover={{ scale: 1.05, rotate: 2 }} className="w-24 h-24 md:w-32 md:h-32 rounded-[2rem] bg-gradient-to-br from-primary to-violet-600 p-1 shadow-[0_0_40px_rgba(79,70,229,0.4)]">
                  <div className="w-full h-full rounded-[1.8rem] md:rounded-[2.3rem] bg-slate-950 flex items-center justify-center overflow-hidden relative">
                    <span className="text-3xl md:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white to-white/40 tracking-tighter">
                      {userInitials}
                    </span>
                    <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/stardust.png')] opacity-10" />
                  </div>
                </motion.div>
                <div className="absolute -bottom-1 -right-1 w-6 h-6 md:w-8 md:h-8 rounded-full bg-slate-950 border-2 border-slate-900 p-1 flex items-center justify-center">
                  <div className="w-full h-full rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.6)] animate-pulse" />
                </div>
              </div>

              <div className="flex-1 text-center md:text-left">
                <div className="mb-6">
                  <h2 className="text-3xl md:text-4xl font-black text-white tracking-tight">{typedUser?.name || "Sovereign User"}</h2>
                  <div className="flex flex-wrap items-center justify-center md:justify-start gap-3 mt-3">
                    <span className="px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-[10px] md:text-xs font-bold text-primary uppercase tracking-widest">Direct Access</span>
                    <span className="px-3 py-1 rounded-full bg-slate-900/60 border border-slate-800 text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-widest">Personal Instance</span>
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800/60 hover:bg-slate-900/60 hover:border-primary/20 transition-all group/stat">
                    <p className="text-[9px] uppercase tracking-[0.2em] text-slate-500 font-bold mb-2 flex items-center gap-2"><Shield className="w-3 h-3 text-primary/60" /> Primary Node (Email)</p>
                    <p className="text-xs md:text-sm text-slate-200 font-bold truncate group-hover/stat:text-white transition-colors">{typedUser?.email || "root@graftai.tech"}</p>
                  </div>
                  <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800/60 hover:bg-slate-900/60 hover:border-violet-500/20 transition-all group/stat">
                    <p className="text-[9px] uppercase tracking-[0.2em] text-slate-500 font-bold mb-2 flex items-center gap-2"><Eye className="w-3 h-3 text-violet-500/60" /> Data Jurisdiction</p>
                    <p className="text-xs md:text-sm text-slate-200 font-bold group-hover/stat:text-white transition-colors uppercase">{typedUser?.email?.split("@")[1] || "graftai.tech"}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div variants={ITEM}>
          <Section title="Profile" description="Your public-facing identity on GraftAI">
            <SettingRow label="Avatar" description="Used on your booking page">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white text-sm font-bold">
                {userInitials}
              </div>
            </SettingRow>
            <SettingRow icon={User} label="Full name" description="Displayed to invitees">
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-300">{typedUser?.name ?? "Not set"}</span>
                <button className="text-xs text-indigo-400 hover:text-indigo-300 font-medium">Edit</button>
              </div>
            </SettingRow>
            <SettingRow icon={Link2} label="Booking page URL" description="Your personal scheduling link">
              <div className="flex items-center gap-2">
                <code className="text-xs text-indigo-300 bg-indigo-500/10 px-2 py-1 rounded-md font-mono">/{bookingSlug}</code>
                <button className="text-xs text-slate-500 hover:text-slate-300" aria-label="View booking page" title="View booking page">
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
              </div>
            </SettingRow>
            <SettingRow icon={Globe} label="Timezone" description="Used for all scheduling">
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-300">{Intl.DateTimeFormat().resolvedOptions().timeZone}</span>
                <button className="text-xs text-indigo-400 hover:text-indigo-300 font-medium">Change</button>
              </div>
            </SettingRow>
          </Section>
        </motion.div>

        <motion.div variants={ITEM}>
          <Section title="Availability" description="When you're open for bookings">
            <SettingRow icon={Clock} label="Working days">
              <div className="flex gap-1.5">
                {[
                  { key: "weekdays", label: "M–F" },
                  { key: "saturday", label: "Sat" },
                  { key: "sunday", label: "Sun" },
                ].map((day) => (
                  <button
                    key={day.key}
                    onClick={() => setAvailability((p) => ({ ...p, [day.key]: !p[day.key as keyof typeof p] }))}
                    className={cn(
                      "px-2.5 py-1 rounded-lg text-xs font-semibold transition-all border",
                      availability[day.key as keyof typeof availability]
                        ? "bg-indigo-600 border-indigo-500 text-white"
                        : "bg-white/5 border-white/10 text-slate-400 hover:text-white"
                    )}
                  >
                    {day.label}
                  </button>
                ))}
              </div>
            </SettingRow>
            <SettingRow icon={Clock} label="Working hours">
              <div className="flex items-center gap-2">
                <select
                  value={availability.startHour}
                  onChange={(e) => setAvailability((p) => ({ ...p, startHour: e.target.value }))}
                  aria-label="Start hour"
                  title="Start hour"
                  className="bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-xs text-slate-300 focus:outline-none appearance-none"
                >
                  {['08:00', '09:00', '10:00'].map((h) => (
                    <option key={h} value={h}>{h}</option>
                  ))}
                </select>
                <span className="text-slate-600 text-xs">to</span>
                <select
                  value={availability.endHour}
                  onChange={(e) => setAvailability((p) => ({ ...p, endHour: e.target.value }))}
                  aria-label="End hour"
                  title="End hour"
                  className="bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-xs text-slate-300 focus:outline-none appearance-none"
                >
                  {['17:00', '18:00', '19:00', '20:00'].map((h) => (
                    <option key={h} value={h}>{h}</option>
                  ))}
                </select>
              </div>
            </SettingRow>
            <div className="px-6 py-3 bg-white/[0.015]">
              <button className="text-sm text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-2">
                Configure advanced availability <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </Section>
        </motion.div>

        <motion.div variants={ITEM}>
          <Section title="Integrations" description="Connect your tools and calendars">
            {[
              { name: "Google Calendar", icon: "📅", connected: false },
              { name: "Zoom", icon: "📹", connected: true },
              { name: "Slack", icon: "💬", connected: false },
              { name: "Microsoft Teams", icon: "🟦", connected: false },
            ].map((int) => (
              <SettingRow key={int.name} label={int.name}>
                <div className="flex items-center gap-3">
                  <span>{int.icon}</span>
                  <button className={cn(
                    "px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all",
                    int.connected
                      ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/15"
                      : "bg-white/5 border-white/10 text-slate-400 hover:text-white hover:bg-white/8"
                  )}>
                    {int.connected ? (
                      <span className="flex items-center gap-1.5"><Check className="w-3 h-3" />Connected</span>
                    ) : (
                      "Connect"
                    )}
                  </button>
                </div>
              </SettingRow>
            ))}
          </Section>
        </motion.div>

        <motion.div variants={ITEM}>
          <Section title="Privacy & Data" description="Control how your data is used">
            {([
              { key: "analytics", icon: Eye, label: "Analytics & usage data", description: "Share anonymized usage to improve GraftAI" },
              { key: "notifications", icon: Bell, label: "Email notifications", description: "Booking reminders and AI insights via email" },
              { key: "ai_training", icon: Zap, label: "AI model training", description: "Help improve AI with your interactions" },
            ] as const).map((item) => (
              <SettingRow key={item.key} icon={item.icon} label={item.label} description={item.description}>
                <Toggle on={consents[item.key]} onChange={() => toggleConsent(item.key)} loading={saving === item.key} />
              </SettingRow>
            ))}
          </Section>
        </motion.div>

        <motion.div variants={ITEM}>
          <div className="rounded-xl border border-red-500/15 bg-red-500/[0.03] overflow-hidden">
            <div className="px-6 py-4 border-b border-red-500/10">
              <h2 className="text-sm font-bold text-red-400">Danger zone</h2>
            </div>
            <div className="px-6 py-4 flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-slate-300">Sign out of all sessions</p>
                <p className="text-xs text-slate-500 mt-0.5">You will be redirected to the login page</p>
              </div>
              <button
                onClick={logout}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-red-500/20 text-red-400 hover:bg-red-500/10 text-sm font-semibold transition-all"
              >
                <LogOut className="w-3.5 h-3.5" /> Sign out
              </button>
            </div>
            <div className="px-6 py-4 border-t border-red-500/10 flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-slate-300">Delete account</p>
                <p className="text-xs text-slate-500 mt-0.5">Permanently delete your account and all data</p>
              </div>
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg border border-red-500/20 text-red-400 hover:bg-red-500/10 text-sm font-semibold transition-all">
                Delete account
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}
