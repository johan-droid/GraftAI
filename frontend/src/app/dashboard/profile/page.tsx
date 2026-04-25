"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/app/providers/auth-provider";
import { updateUserProfile, getUsageStats } from "@/lib/api";
import { motion } from "framer-motion";
import {
  User,
  Shield,
  Clock,
  Globe,
  Zap,
} from "lucide-react";
import { UsageProgress } from "@/components/profile/UsageProgress";
import { RecentActivity } from "@/components/profile/RecentActivity";
import { PricingSection } from "@/components/profile/PricingSection";

const STAGGER = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.07 } },
};
const ITEM = {
  hidden: { opacity: 0, y: 14 },
  visible: { opacity: 1, y: 0 },
};

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
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 px-4 sm:px-6 py-4">
      <div className="flex items-start sm:items-center gap-3 sm:gap-4 min-w-0 flex-1">
        {Icon && <Icon className="w-4 h-4 text-slate-500 shrink-0 mt-0.5 sm:mt-0" />}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-200">{label}</p>
          {description && <p className="text-xs text-slate-500 mt-0.5">{description}</p>}
        </div>
      </div>
      <div className="shrink-0 sm:mt-0 mt-1 pl-7 sm:pl-0 flex">{children}</div>
    </div>
  );
}

export default function ProfilePage() {
  const { user, refresh } = useAuth();
  const [stats, setStats] = useState<any>(null);

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
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getUsageStats();
        setStats(data);
      } catch (err) {
        console.error("Failed to fetch stats", err);
      }
    };
    if (user) {
      fetchStats();
      setNameDraft(user.full_name || user.name || "");
      setBioDraft(user.bio || "");
      setJobDraft(user.job_title || "");
      setLocationDraft(user.location || "");
    }
  }, [user]);

  const saveProfileField = async (field: "name" | "bio" | "job_title" | "location") => {
    setProfileSaving(true);
    try {
      const data: Record<string, string> = {};
      if (field === "name") data.full_name = nameDraft.trim();
      if (field === "bio") data.bio = bioDraft.trim();
      if (field === "job_title") data.job_title = jobDraft.trim();
      if (field === "location") data.location = locationDraft.trim();

      await updateUserProfile(data);
      
      setEditingName(false);
      setEditingBio(false);
      setEditingJob(false);
      setEditingLocation(false);
      
      await refresh();
    } finally {
      setProfileSaving(false);
    }
  };

  const updateTimezoneToBrowser = async () => {
    setTimezoneSaving(true);
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      await updateUserProfile({ timezone: tz });
      await refresh();
    } finally {
      setTimezoneSaving(false);
    }
  };

  const currentName = user?.full_name || user?.name || "Anonymous User";
  const userInitials = user?.name
    ? user.name.split(" ").map((n: string) => n[0]).join("").slice(0, 2).toUpperCase()
    : user?.email?.[0]?.toUpperCase() ?? "U";

  if (!user) return null;

  return (
    <div className="p-6 md:p-10 max-w-4xl mx-auto">
      <motion.div variants={STAGGER} initial="hidden" animate="visible" className="space-y-8">
        <motion.div variants={ITEM}>
          <h1 className="text-3xl font-bold text-white tracking-tight">Profile</h1>
          <p className="text-slate-500 text-[15px] mt-1.5">Manage your personal identity across the workspace.</p>
        </motion.div>

        <motion.div variants={ITEM}>
          <div className="rounded-[1.5rem] sm:rounded-[2.5rem] border border-white/[0.08] bg-[#0d1424]/40 p-5 sm:p-8 md:p-10 shadow-2xl relative overflow-hidden group backdrop-blur-xl">
            <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-indigo-600/10 blur-[120px] rounded-full -mr-20 -mt-20 opacity-40" />
            <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-violet-600/10 blur-[120px] rounded-full -ml-20 -mb-20 opacity-40" />

            <div className="flex flex-col md:flex-row items-center md:items-start gap-10 relative z-10">
              <div className="relative shrink-0">
                <motion.div 
                  whileHover={{ scale: 1.02 }} 
                  className="w-24 h-24 sm:w-32 sm:h-32 md:w-36 md:h-36 rounded-[2rem] sm:rounded-[2.5rem] bg-gradient-to-br from-indigo-500 via-violet-600 to-fuchsia-600 p-1 shadow-2xl shadow-indigo-600/20"
                >
                  <div className="w-full h-full rounded-[1.8rem] sm:rounded-[2.3rem] bg-[#070b14] flex items-center justify-center overflow-hidden relative">
                    <span className="text-3xl sm:text-4xl md:text-5xl font-black text-white hover:scale-110 transition-transform cursor-default">
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
                <div className="mb-6 sm:mb-8 w-full">
                  <h2 className="text-2xl sm:text-4xl md:text-5xl font-black text-white tracking-tighter mb-3 sm:mb-4 truncate">
                    {currentName}
                  </h2>
                  <div className="flex flex-wrap items-center justify-center md:justify-start gap-3">
                    <span className="px-4 py-1.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-[11px] font-bold text-indigo-400 uppercase tracking-[0.15em] flex items-center gap-2">
                       <Zap className="w-3 h-3" /> {user?.tier?.toUpperCase() || "FREE"} TIER
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
                      <Shield className="w-3.5 h-3.5 text-indigo-400/70" /> User Ident
                    </p>
                    <p className="text-[14px] text-white font-bold truncate relative z-10">{user?.email}</p>
                  </div>
                  
                  <div className="p-5 rounded-[1.5rem] bg-white/[0.03] border border-white/[0.08] hover:bg-white/[0.05] hover:border-white/20 transition-all group/juris relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-violet-500/5 to-transparent opacity-0 group-hover/juris:opacity-100 transition-opacity" />
                    <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-black mb-3 flex items-center gap-2">
                      <Globe className="w-3.5 h-3.5 text-violet-400/70" /> Jurisdiction
                    </p>
                    <p className="text-[14px] text-white font-bold uppercase relative z-10">
                      {user?.email?.split("@")[1] || "Global"}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div variants={ITEM}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-6 relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/10 blur-2xl rounded-full -mr-12 -mt-12 transition-all group-hover:scale-150" />
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center">
                  <Zap className="w-4 h-4 text-indigo-400" />
                </div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">AI Power</h3>
              </div>
              <div className="flex flex-col">
                <span className="text-2xl font-black text-white tabular-nums">
                  {stats?.ai_tokens?.toLocaleString() || user?.total_ai_tokens?.toLocaleString() || "0"}
                </span>
                <span className="text-[10px] text-slate-500 mt-1 font-medium">LIFETIME TOKENS CONSUMED</span>
              </div>
            </div>

            <div className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-6 relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-24 h-24 bg-violet-500/10 blur-2xl rounded-full -mr-12 -mt-12 transition-all group-hover:scale-150" />
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center">
                  <Globe className="w-4 h-4 text-violet-400" />
                </div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">API Engine</h3>
              </div>
              <div className="flex flex-col">
                <span className="text-2xl font-black text-white tabular-nums">
                  {stats?.api_calls?.toLocaleString() || user?.total_api_calls?.toLocaleString() || "0"}
                </span>
                <span className="text-[10px] text-slate-500 mt-1 font-medium">TOTAL SYSTEM API CALLS</span>
              </div>
            </div>

            <div className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-6 relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-24 h-24 bg-fuchsia-500/10 blur-2xl rounded-full -mr-12 -mt-12 transition-all group-hover:scale-150" />
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 rounded-lg bg-fuchsia-500/10 flex items-center justify-center">
                  <Clock className="w-4 h-4 text-fuchsia-400" />
                </div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Efficiency</h3>
              </div>
              <div className="flex flex-col">
                <span className="text-2xl font-black text-white tabular-nums">
                  {stats?.scheduling_count?.toLocaleString() || user?.total_scheduling_count?.toLocaleString() || "0"}
                </span>
                <span className="text-[10px] text-slate-500 mt-1 font-medium">EVENTS SCHEDULED</span>
              </div>
            </div>

            <div className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-6 relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/10 blur-2xl rounded-full -mr-12 -mt-12 transition-all group-hover:scale-150" />
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                  <Activity className="w-4 h-4 text-emerald-400" />
                </div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Health</h3>
              </div>
              <div className="flex flex-col">
                <span className="text-2xl font-black text-emerald-400 tabular-nums">
                  Optimal
                </span>
                <span className="text-[10px] text-slate-500 mt-1 font-medium">SAAS GRADE ARCHITECTURE</span>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div variants={ITEM} className="grid grid-cols-1 md:grid-cols-2 gap-8">
           <div className="space-y-6">
              <h2 className="text-sm font-black text-white uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                <Zap className="w-4 h-4 text-indigo-400" /> Daily Quotas
              </h2>
              <div className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-6 space-y-6">
                <UsageProgress 
                  label="AI Copilot Messages" 
                  current={stats?.daily_ai_usage || 0} 
                  limit={user?.tier === 'enterprise' ? 1000 : user?.tier === 'elite' ? 250 : user?.tier === 'pro' ? 100 : 25} 
                  unit="msgs"
                />
                <UsageProgress 
                  label="Calendar Syncs" 
                  current={stats?.daily_sync_usage || 0} 
                  limit={user?.tier === 'enterprise' ? 500 : user?.tier === 'elite' ? 100 : user?.tier === 'pro' ? 25 : 5} 
                  unit="syncs"
                  color="bg-violet-500"
                />
              </div>
           </div>

           <div className="space-y-6">
              <h2 className="text-sm font-black text-white uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-400" /> Recent Activity
              </h2>
              <div className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-4 h-[216px] overflow-y-auto">
                <RecentActivity />
              </div>
           </div>
        </motion.div>

        <motion.div variants={ITEM}>
          <Section title="Details" description="Your professional profile info">
            <SettingRow icon={User} label="Full name" description="Displayed to others">
              {editingName ? (
                <div className="flex items-center gap-2">
                  <input
                    aria-label="Full name"
                    value={nameDraft}
                    onChange={(e) => setNameDraft(e.target.value)}
                    className="bg-white/5 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 w-full max-w-[200px]"
                  />
                  <button onClick={() => saveProfileField("name")} disabled={profileSaving} className="text-xs text-indigo-400 font-bold">Save</button>
                  <button onClick={() => setEditingName(false)} className="text-xs text-slate-500">Cancel</button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-300 font-medium">{currentName || "Not set"}</span>
                  <button onClick={() => setEditingName(true)} className="text-xs text-indigo-400 font-bold hover:text-indigo-300 transition-colors">Edit</button>
                </div>
              )}
            </SettingRow>

            <SettingRow icon={Zap} label="Job title" description="Your role or specialization">
              {editingJob ? (
                <div className="flex items-center gap-2">
                  <input
                    aria-label="Job title"
                    value={jobDraft}
                    onChange={(e) => setJobDraft(e.target.value)}
                    className="bg-white/5 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 w-full max-w-[200px]"
                  />
                  <button onClick={() => saveProfileField("job_title")} disabled={profileSaving} className="text-xs text-indigo-400 font-bold">Save</button>
                  <button onClick={() => setEditingJob(false)} className="text-xs text-slate-500">Cancel</button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-300 font-medium">{user?.job_title || jobDraft || "Not set"}</span>
                  <button onClick={() => setEditingJob(true)} className="text-xs text-indigo-400 font-bold hover:text-indigo-300 transition-colors">Edit</button>
                </div>
              )}
            </SettingRow>

            <SettingRow icon={Globe} label="Location" description="City, Country">
              {editingLocation ? (
                <div className="flex items-center gap-2">
                  <input
                    aria-label="Location"
                    value={locationDraft}
                    onChange={(e) => setLocationDraft(e.target.value)}
                    className="bg-white/5 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 w-full max-w-[200px]"
                  />
                  <button onClick={() => saveProfileField("location")} disabled={profileSaving} className="text-xs text-indigo-400 font-bold">Save</button>
                  <button onClick={() => setEditingLocation(false)} className="text-xs text-slate-500">Cancel</button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-300 font-medium">{user?.location || locationDraft || "Not set"}</span>
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
                <div className="w-full flex items-center justify-between">
                  <p className="text-sm text-slate-400 leading-relaxed italic pr-4 line-clamp-2 max-w-[250px] sm:max-w-md">{user?.bio || bioDraft || "No bio set yet."}</p>
                  <button onClick={() => setEditingBio(true)} className="text-xs text-indigo-400 font-bold hover:text-indigo-300 transition-colors shrink-0">Edit Bio</button>
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

          <motion.div variants={ITEM}>
            <Section title="Account" description="Authentication, subscription and account metadata">
              <SettingRow icon={User} label="Username" description="Stable login alias">
                <span className="text-sm text-slate-300 font-medium">{user?.username || "Not specified"}</span>
              </SettingRow>
              <SettingRow icon={Globe} label="Email" description="Primary account email">
                <span className="text-sm text-slate-300 font-medium">{user?.email || "Not available"}</span>
              </SettingRow>
              <SettingRow icon={Shield} label="Subscription" description="Current plan and status">
                <span className="text-sm text-slate-300 font-medium">{(user?.tier || user?.subscription_status || "Free").toString().toUpperCase()}</span>
              </SettingRow>
              <SettingRow icon={Clock} label="Member since" description="Account creation date">
                <span className="text-sm text-slate-300 font-medium">{user?.created_at ? new Date(user.created_at).toLocaleDateString() : "Unknown"}</span>
              </SettingRow>
            </Section>
          </motion.div>

          <motion.div variants={ITEM} className="pt-8">
            <div className="flex items-center gap-3 mb-8">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center">
                <Zap className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <h2 className="text-xl font-black text-white uppercase tracking-wider">Subscription Plans</h2>
                <p className="text-xs text-slate-500 mt-0.5">Choose the plan that fits your professional needs.</p>
              </div>
            </div>
            <PricingSection currentTier={user?.tier || "free"} />
          </motion.div>
        </motion.div>
      </motion.div>
    </div>
  );
}
