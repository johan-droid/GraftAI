"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthContext } from "@/app/providers/auth-provider";
import { deleteAccount, getIntegrationStatus, setConsent, syncUserTimezone, updateUserProfile, getEmailDiagnostic, sendTestEmail } from "@/lib/api";
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
  ChevronRight,
  Zap,
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
  const router = useRouter();
  const { user, logout } = useAuthContext();
  const typedUser = user as { name?: string; email?: string } | null;

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
  const [integrationStatus, setIntegrationStatus] = useState<Record<string, boolean>>({
    google: false,
    microsoft: false,
  });
  const [loadingIntegrations, setLoadingIntegrations] = useState(true);
  
  // Profile Detail State
  const [editingName, setEditingName] = useState(false);
  const [editingBio, setEditingBio] = useState(false);
  const [editingJob, setEditingJob] = useState(false);
  const [editingLocation, setEditingLocation] = useState(false);

  const [nameDraft, setNameDraft] = useState("");
  const [bioDraft, setBioDraft] = useState("");
  const [jobDraft, setJobDraft] = useState("");
  const [locationDraft, setLocationDraft] = useState("");

  const [profileSaving, setProfileSaving] = useState(false);
  const [timezoneSaving, setTimezoneSaving] = useState(false);
  const [deletingAccount, setDeletingAccount] = useState(false);

  // Diagnostics State
  const [currentTime, setCurrentTime] = useState(new Date());
  const [emailStatus, setEmailStatus] = useState<any>(null);
  const [testingEmail, setTestingEmail] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (typedUser) {
      setNameDraft(typedUser.name || "");
      setBioDraft((typedUser as any).bio || "");
      setJobDraft((typedUser as any).job_title || "");
      setLocationDraft((typedUser as any).location || "");
    }
  }, [typedUser]);

  useEffect(() => {
    let alive = true;
    getIntegrationStatus()
      .then((data) => {
        if (!alive) return;
        setIntegrationStatus({
          google: Boolean(data.connections?.google),
          microsoft: Boolean(data.connections?.microsoft),
        });
      })
      .catch(() => {
        if (!alive) return;
        setIntegrationStatus({ google: false, microsoft: false });
      })
      .finally(() => {
        if (alive) setLoadingIntegrations(false);
      });

    return () => {
      alive = false;
    };
  }, []);

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

  const saveProfileField = async (field: "name" | "bio" | "job_title" | "location") => {
    setProfileSaving(true);
    try {
      const data: any = {};
      if (field === "name") data.full_name = nameDraft.trim();
      if (field === "bio") data.bio = bioDraft.trim();
      if (field === "job_title") data.job_title = jobDraft.trim();
      if (field === "location") data.location = locationDraft.trim();

      await updateUserProfile(data);
      
      setEditingName(false);
      setEditingBio(false);
      setEditingJob(false);
      setEditingLocation(false);
      
      router.refresh();
    } finally {
      setProfileSaving(false);
    }
  };

  const updateTimezoneToBrowser = async () => {
    setTimezoneSaving(true);
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      await syncUserTimezone(tz);
      await updateUserProfile({ timezone: tz });
      router.refresh();
    } finally {
      setTimezoneSaving(false);
    }
  };

  const handleTestEmail = async () => {
    if (!typedUser?.email) return;
    setTestingEmail(true);
    try {
      const res = await sendTestEmail(typedUser.email);
      setEmailStatus(res);
    } catch (err: any) {
      setEmailStatus({ status: "error", message: err.message });
    } finally {
      setTestingEmail(false);
    }
  };

  const handleRunDiagnostics = async () => {
    setTestingEmail(true);
    try {
      const res = await getEmailDiagnostic();
      setEmailStatus(res);
    } catch (err: any) {
      setEmailStatus({ status: "error", message: err.message });
    } finally {
      setTestingEmail(false);
    }
  };

  const handleDeleteAccount = async () => {
    const ok = window.confirm("This will permanently delete your account and data. Continue?");
    if (!ok) return;

    setDeletingAccount(true);
    try {
      await deleteAccount();
      await logout();
    } finally {
      setDeletingAccount(false);
    }
  };

  const userInitials = typedUser?.name
    ? typedUser.name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : typedUser?.email?.[0]?.toUpperCase() ?? "U";

  const joinDate = (typedUser as any)?.created_at 
    ? new Date((typedUser as any).created_at).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
    : "Recently joined";

  return (
    <div className="p-6 md:p-10 max-w-4xl mx-auto">
      <motion.div variants={STAGGER} initial="hidden" animate="visible" className="space-y-8">

        <motion.div variants={ITEM}>
          <h1 className="text-3xl font-bold text-white tracking-tight">Settings</h1>
          <p className="text-slate-500 text-[15px] mt-1.5">Configure your workspace identity and operational parameters.</p>
        </motion.div>

        <motion.div variants={ITEM}>
          <div className="rounded-[2.5rem] border border-white/[0.08] bg-[#0d1424]/40 p-8 md:p-10 shadow-2xl relative overflow-hidden group backdrop-blur-xl">
            {/* Ambient Background Glows */}
            <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-indigo-600/10 blur-[120px] rounded-full -mr-20 -mt-20 opacity-40" />
            <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-violet-600/10 blur-[120px] rounded-full -ml-20 -mb-20 opacity-40" />

            <div className="flex flex-col md:flex-row items-center md:items-start gap-10 relative z-10">
              <div className="relative shrink-0">
                <motion.div 
                  whileHover={{ scale: 1.02 }} 
                  className="w-32 h-32 md:w-36 md:h-36 rounded-[2.5rem] bg-gradient-to-br from-indigo-500 via-violet-600 to-fuchsia-600 p-1 shadow-2xl shadow-indigo-600/20"
                >
                  <div className="w-full h-full rounded-[2.3rem] bg-[#070b14] flex items-center justify-center overflow-hidden relative">
                    <span className="text-4xl md:text-5xl font-black text-white hover:scale-110 transition-transform cursor-default">
                      {userInitials}
                    </span>
                    <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent pointer-events-none" />
                  </div>
                </motion.div>
                <div className="absolute -bottom-1 -right-1 w-8 h-8 rounded-full bg-[#070b14] border-4 border-[#0d1424] p-1.5 flex items-center justify-center">
                  <div className="w-full h-full rounded-full bg-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.5)] animate-pulse" />
                </div>
              </div>

              <div className="flex-1 text-center md:text-left min-w-0">
                <div className="mb-8">
                  <h2 className="text-4xl md:text-5xl font-black text-white tracking-tighter mb-4 truncate">
                    {typedUser?.name || "Anonymous User"}
                  </h2>
                  <div className="flex flex-wrap items-center justify-center md:justify-start gap-3">
                    <span className="px-4 py-1.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-[11px] font-bold text-indigo-400 uppercase tracking-[0.15em] flex items-center gap-2">
                       <Zap className="w-3 h-3" /> {(typedUser as any)?.tier?.toUpperCase() || "FREE"} TIER
                    </span>
                    <span className="px-4 py-1.5 rounded-xl bg-white/5 border border-white/10 text-[11px] font-bold text-slate-400 uppercase tracking-[0.15em] flex items-center gap-2">
                       <Clock className="w-3 h-3" /> {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div className="p-5 rounded-[1.5rem] bg-white/[0.03] border border-white/[0.08] hover:bg-white/[0.05] hover:border-white/20 transition-all group/node relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent opacity-0 group-hover/node:opacity-100 transition-opacity" />
                    <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-black mb-3 flex items-center gap-2">
                      <Shield className="w-3.5 h-3.5 text-indigo-400/70" /> Node Identifier
                    </p>
                    <p className="text-[14px] text-white font-bold truncate relative z-10">{typedUser?.email}</p>
                  </div>
                  
                  <div className="p-5 rounded-[1.5rem] bg-white/[0.03] border border-white/[0.08] hover:bg-white/[0.05] hover:border-white/20 transition-all group/juris relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-violet-500/5 to-transparent opacity-0 group-hover/juris:opacity-100 transition-opacity" />
                    <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-black mb-3 flex items-center gap-2">
                      <Globe className="w-3.5 h-3.5 text-violet-400/70" /> Jurisdiction
                    </p>
                    <p className="text-[14px] text-white font-bold uppercase relative z-10">
                      {typedUser?.email?.split("@")[1] || "GraftAI.Tech"}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div variants={ITEM}>
          <Section title="Profile" description="Your public-facing identity on GraftAI">
            <SettingRow label="Avatar" description="Used across your workspace">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 via-violet-600 to-fuchsia-600 flex items-center justify-center text-white text-sm font-bold shadow-lg shadow-indigo-600/20">
                {userInitials}
              </div>
            </SettingRow>

            <SettingRow icon={User} label="Full name" description="Displayed to invitees">
              {editingName ? (
                <div className="flex items-center gap-2">
                  <input
                    value={nameDraft}
                    onChange={(e) => setNameDraft(e.target.value)}
                    className="bg-white/5 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 w-full max-w-[200px]"
                  />
                  <button onClick={() => saveProfileField("name")} disabled={profileSaving} className="text-xs text-indigo-400 font-bold">Save</button>
                  <button onClick={() => setEditingName(false)} className="text-xs text-slate-500">Cancel</button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-300 font-medium">{typedUser?.name ?? "Not set"}</span>
                  <button onClick={() => setEditingName(true)} className="text-xs text-indigo-400 font-bold hover:text-indigo-300 transition-colors">Edit</button>
                </div>
              )}
            </SettingRow>

            <SettingRow icon={Zap} label="Job title" description="Your role or specialization">
              {editingJob ? (
                <div className="flex items-center gap-2">
                  <input
                    value={jobDraft}
                    onChange={(e) => setJobDraft(e.target.value)}
                    className="bg-white/5 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 w-full max-w-[200px]"
                  />
                  <button onClick={() => saveProfileField("job_title")} disabled={profileSaving} className="text-xs text-indigo-400 font-bold">Save</button>
                  <button onClick={() => setEditingJob(false)} className="text-xs text-slate-500">Cancel</button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-300 font-medium">{jobDraft || "Not set"}</span>
                  <button onClick={() => setEditingJob(true)} className="text-xs text-indigo-400 font-bold hover:text-indigo-300 transition-colors">Edit</button>
                </div>
              )}
            </SettingRow>

            <SettingRow icon={Globe} label="Location" description="City, Country">
              {editingLocation ? (
                <div className="flex items-center gap-2">
                  <input
                    value={locationDraft}
                    onChange={(e) => setLocationDraft(e.target.value)}
                    className="bg-white/5 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 w-full max-w-[200px]"
                  />
                  <button onClick={() => saveProfileField("location")} disabled={profileSaving} className="text-xs text-indigo-400 font-bold">Save</button>
                  <button onClick={() => setEditingLocation(false)} className="text-xs text-slate-500">Cancel</button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-300 font-medium">{locationDraft || "Not set"}</span>
                  <button onClick={() => setEditingLocation(true)} className="text-xs text-indigo-400 font-bold hover:text-indigo-300 transition-colors">Edit</button>
                </div>
              )}
            </SettingRow>

            <SettingRow icon={Shield} label="Professional Bio" description="A short summary about yourself">
              {editingBio ? (
                <div className="w-full mt-2">
                  <textarea
                    value={bioDraft}
                    onChange={(e) => setBioDraft(e.target.value)}
                    rows={3}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-200 mb-3 focus:outline-none focus:border-indigo-500/50 transition-colors"
                    placeholder="Tell us about yourself..."
                  />
                  <div className="flex gap-3">
                    <button onClick={() => saveProfileField("bio")} disabled={profileSaving} className="px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-bold">Save Bio</button>
                    <button onClick={() => setEditingBio(false)} className="px-3 py-1.5 rounded-lg bg-white/5 text-slate-500 text-xs font-bold">Cancel</button>
                  </div>
                </div>
              ) : (
                <div className="w-full">
                  <p className="text-sm text-slate-400 mb-2 leading-relaxed italic">{bioDraft || "No bio set yet."}</p>
                  <button onClick={() => setEditingBio(true)} className="text-xs text-indigo-400 font-bold hover:text-indigo-300 transition-colors">Edit Bio</button>
                </div>
              )}
            </SettingRow>

            <SettingRow icon={Clock} label="Timezone" description="Global scheduling reference">
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-300 font-medium">{Intl.DateTimeFormat().resolvedOptions().timeZone}</span>
                <button onClick={updateTimezoneToBrowser} className="text-xs text-indigo-400 font-bold hover:text-indigo-300 transition-colors">
                  {timezoneSaving ? "Syncing..." : "Sync"}
                </button>
              </div>
            </SettingRow>
          </Section>
        </motion.div>

        {typedUser && (typedUser as any).is_superuser && (
          <motion.div variants={ITEM} className="mt-8">
            <div className="rounded-[2.5rem] border border-white/[0.08] bg-[#0d1424]/40 p-8 md:p-10 shadow-2xl relative overflow-hidden group backdrop-blur-xl">
              <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-indigo-600/10 blur-[120px] rounded-full -mr-20 -mt-20 opacity-40" />
              
              <div className="flex flex-col md:flex-row items-start gap-8 relative z-10">
                <div className="w-16 h-16 rounded-[1.5rem] bg-indigo-500/10 flex items-center justify-center shrink-0 border border-indigo-500/20">
                  <Bell className="w-8 h-8 text-indigo-400" />
                </div>
                
                <div className="flex-1">
                  <h3 className="text-2xl font-bold text-white mb-2 tracking-tight">Email System Diagnostics</h3>
                  <p className="text-slate-400 text-sm leading-relaxed mb-6 max-w-2xl">
                    Verify that your <code className="text-indigo-400 bg-indigo-400/10 px-1.5 py-0.5 rounded">SMTP_PASSWORD</code> is a 
                    <span className="text-white font-medium"> 16-character Google App Password</span>. Standard account passwords will be blocked by Google Security.
                  </p>

                  <div className="flex flex-wrap gap-4">
                    <button
                      onClick={handleRunDiagnostics}
                      disabled={testingEmail}
                      className="px-6 py-2.5 rounded-xl bg-white/5 border border-white/10 text-xs font-bold text-white hover:bg-white/10 transition-all flex items-center gap-2"
                    >
                      {testingEmail ? <Loader2 className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
                      Verify Connection
                    </button>
                    <button
                      onClick={handleTestEmail}
                      disabled={testingEmail}
                      className="px-6 py-2.5 rounded-xl bg-indigo-600 text-xs font-bold text-white hover:bg-indigo-500 transition-all flex items-center gap-2 shadow-lg shadow-indigo-600/20"
                    >
                      <Zap className="w-4 h-4" /> Send Test Email
                    </button>
                  </div>

                  {emailStatus && (
                    <motion.div 
                      initial={{ opacity: 0, height: 0 }} 
                      animate={{ opacity: 1, height: "auto" }}
                      className={cn(
                        "mt-8 p-6 rounded-[1.5rem] border text-[13px] font-mono relative overflow-hidden",
                        emailStatus.status === "success" 
                          ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" 
                          : "bg-red-500/10 border-red-500/20 text-red-400"
                      )}
                    >
                      <div className="flex items-center gap-2 mb-3">
                        <div className={cn("w-2 h-2 rounded-full animate-pulse", emailStatus.status === "success" ? "bg-emerald-400" : "bg-red-400")} />
                        <span className="font-bold uppercase tracking-widest text-[10px]">Diagnostics Result</span>
                      </div>
                      <p className="leading-relaxed opacity-90">{emailStatus.message}</p>
                      {emailStatus.hint && (
                        <div className="mt-4 p-3 rounded-lg bg-black/20 border border-white/5 text-white/70 italic flex items-start gap-2">
                           <span className="shrink-0 text-amber-400">💡</span> {emailStatus.hint}
                        </div>
                      )}
                    </motion.div>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        )}

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
              <Link href="/dashboard/calendar" className="text-sm text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-2">
                Configure advanced availability <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </Section>
        </motion.div>

        <motion.div variants={ITEM}>
          <Section title="Integrations" description="Connect your tools and calendars">
            {[
              { id: "google", name: "Google Calendar", icon: "📅" },
              { id: "microsoft", name: "Microsoft Teams", icon: "🟦" },
            ].map((int) => (
              <SettingRow key={int.id} label={int.name}>
                <div className="flex items-center gap-3">
                  <span>{int.icon}</span>
                  {loadingIntegrations ? (
                    <span className="text-xs text-slate-500">Checking...</span>
                  ) : (
                    <button
                      className={cn(
                        "px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all",
                        integrationStatus[int.id]
                          ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/15"
                          : "bg-white/5 border-white/10 text-slate-400 hover:text-white hover:bg-white/8"
                      )}
                      onClick={() => {
                        if (!integrationStatus[int.id]) {
                          router.push("/dashboard/settings/integrations");
                        }
                      }}
                    >
                      {integrationStatus[int.id] ? (
                        <span className="flex items-center gap-1.5"><Check className="w-3 h-3" />Connected</span>
                      ) : (
                        "Connect"
                      )}
                    </button>
                  )}
                </div>
              </SettingRow>
            ))}
            <div className="px-6 py-3 bg-white/[0.015]">
              <Link
                href="/dashboard/settings/integrations"
                className="text-sm text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-2"
              >
                Open integration controls <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
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
              <button
                onClick={handleDeleteAccount}
                disabled={deletingAccount}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-red-500/20 text-red-400 hover:bg-red-500/10 text-sm font-semibold transition-all disabled:opacity-60"
              >
                {deletingAccount ? "Deleting..." : "Delete account"}
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}
