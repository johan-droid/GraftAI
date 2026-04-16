"use client";

import { useState, useEffect, useRef } from "react";
import { useSession } from "next-auth/react";
import { motion } from "framer-motion";
import { toast } from "@/components/ui/Toast";
import { 
  User, Mail, Globe, Clock, Calendar, 
  ShieldAlert, Camera, Check, Loader2 
} from "lucide-react";

// --- Animation Config ---
const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const bentoVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { 
    opacity: 1, 
    y: 0,
    transition: { type: "spring", stiffness: 260, damping: 24 }
  }
};

// --- Types ---
interface UserProfile {
  name: string;
  email: string;
  bio: string;
  timezone: string;
  timeFormat: "12h" | "24h";
  bufferMinutes: number;
}

export default function SettingsProfilePage() {
  const { data: session, update } = useSession();
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  
  const [profile, setProfile] = useState<UserProfile>({
    name: "",
    email: "",
    bio: "",
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    timeFormat: "12h",
    bufferMinutes: 15,
  });
  // Keep a ref to the latest session to avoid stale closures inside timeouts
  const sessionRef = useRef(session);
  useEffect(() => {
    sessionRef.current = session;
  }, [session]);

  // 1. Read from Backend (simulated)
  useEffect(() => {
    setIsLoading(true);
    const timeoutId = setTimeout(() => {
      const s = sessionRef.current;
      setProfile(prev => ({
        ...prev,
        name: s?.user?.name || "System Admin",
        email: s?.user?.email || "admin@graftai.com",
        bio: "Scheduling meetings efficiently via GraftAI.",
      }));
      setIsLoading(false);
    }, 800);

    return () => clearTimeout(timeoutId);
  }, [session]);

  // 2. Save to Backend
  const handleSave = async () => {
    try {
      setIsSaving(true);
      // TODO: Uncomment when backend route is ready
      // await apiClient.patch('/users/me', profile);
      
      // Update NextAuth session if name changed
      if (profile.name !== session?.user?.name) {
        await update({ name: profile.name });
      }

      setTimeout(() => {
        setIsSaving(false);
        toast.success("Profile updated successfully!");
      }, 600);
    } catch (err) {
      console.error("Failed to save profile:", err);
      toast.error("Failed to save changes.");
      setIsSaving(false);
    }
  };

  // Placeholder handlers for security actions
  const handleChangePassword = () => {
    // TODO: wire to backend password change flow
    toast.info("Change Password flow is not implemented yet.");
  };

  const handleDeleteAccount = () => {
    // TODO: implement account deletion flow with confirmation modal
    if (!confirm("Are you sure you want to delete your account? This action is irreversible.")) return;
    toast.error("Delete Account flow is not implemented.");
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setProfile(prev => ({ ...prev, [name]: value }));
  };

  // --- Loading Skeleton ---
  if (isLoading) {
    return (
      <div className="p-6 md:p-10 max-w-6xl mx-auto w-full animate-pulse">
        <div className="h-10 bg-[#F1F3F4] rounded-lg w-1/4 mb-10"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="col-span-1 md:col-span-2 h-[400px] bg-[#F1F3F4] rounded-3xl"></div>
          <div className="col-span-1 h-[400px] bg-[#F1F3F4] rounded-3xl"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-10 max-w-6xl mx-auto w-full">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-medium text-[#202124] tracking-tight mb-2">
            Profile Settings
          </h1>
          <p className="text-[#5F6368] text-base">
            Manage your personal information and scheduling preferences.
          </p>
        </div>
        <button 
          onClick={handleSave}
          disabled={isSaving}
          className="inline-flex items-center justify-center gap-2 bg-[#1A73E8] text-white hover:bg-[#1557B0] px-6 py-2.5 rounded-full text-sm font-medium transition-colors shadow-sm disabled:opacity-70 disabled:cursor-not-allowed"
        >
          {isSaving ? <Loader2 size={18} className="animate-spin" /> : <Check size={18} />}
          {isSaving ? "Saving..." : "Save Changes"}
        </button>
      </div>

      {/* Bento Grid */}
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
      >
        
        {/* BENTO 1: Identity (Spans 2 columns) */}
        <motion.div variants={bentoVariants} className="md:col-span-2 bg-white border border-[#DADCE0] rounded-3xl p-8 shadow-sm relative overflow-hidden group">
          <h2 className="text-lg font-semibold text-[#202124] mb-6">Personal Information</h2>
          
          <div className="flex flex-col sm:flex-row gap-8">
            {/* Avatar Upload UI */}
            <div className="flex flex-col items-center gap-3">
              <div className="relative w-28 h-28 rounded-full bg-[#E8F0FE] border border-[#DADCE0] flex items-center justify-center text-[#1A73E8] text-3xl font-medium overflow-hidden group-hover:border-[#1A73E8] transition-colors">
                {profile.name.charAt(0).toUpperCase()}
                <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity cursor-pointer backdrop-blur-sm">
                  <Camera size={24} className="text-white" />
                </div>
              </div>
              <span className="text-xs font-medium text-[#1A73E8] cursor-pointer hover:underline">Change Picture</span>
            </div>

            {/* Inputs */}
            <div className="flex-1 space-y-5">
              <div>
                <label htmlFor="name" className="block text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-2 flex items-center gap-2">
                  <User size={14} /> Full Name
                </label>
                <input 
                  id="name"
                  type="text" 
                  name="name"
                  value={profile.name}
                  onChange={handleInputChange}
                  className="w-full bg-[#F8F9FA] border border-[#DADCE0] rounded-xl px-4 py-3 text-[#202124] focus:outline-none focus:ring-2 focus:ring-[#1A73E8]/20 focus:border-[#1A73E8] transition-all"
                />
              </div>

              <div>
                <label htmlFor="email" className="block text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-2 flex items-center gap-2">
                  <Mail size={14} /> Email Address
                </label>
                <input 
                  id="email"
                  type="email" 
                  name="email"
                  value={profile.email}
                  onChange={handleInputChange}
                  disabled
                  className="w-full bg-[#F1F3F4] border border-[#DADCE0] rounded-xl px-4 py-3 text-[#5F6368] cursor-not-allowed"
                />
                <p className="text-[11px] text-[#5F6368] mt-1.5">Email cannot be changed directly. Contact support.</p>
              </div>

              <div>
                <label htmlFor="bio" className="block text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-2">
                  Bio / Welcome Message
                </label>
                <textarea 
                  id="bio"
                  name="bio"
                  value={profile.bio}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full bg-[#F8F9FA] border border-[#DADCE0] rounded-xl px-4 py-3 text-[#202124] focus:outline-none focus:ring-2 focus:ring-[#1A73E8]/20 focus:border-[#1A73E8] transition-all resize-none"
                  placeholder="Welcome to my booking page..."
                />
              </div>
            </div>
          </div>
        </motion.div>

        {/* BENTO 2: Localization */}
        <motion.div variants={bentoVariants} className="bg-white border border-[#DADCE0] rounded-3xl p-8 shadow-sm flex flex-col">
          <h2 className="text-lg font-semibold text-[#202124] mb-6">Localization</h2>
          
          <div className="space-y-6 flex-1">
            <div>
              <label htmlFor="timezone" className="block text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-2 flex items-center gap-2">
                <Globe size={14} /> Timezone
              </label>
              <select 
                id="timezone"
                name="timezone"
                value={profile.timezone}
                onChange={handleInputChange}
                className="w-full bg-[#F8F9FA] border border-[#DADCE0] rounded-xl px-4 py-3 text-[#202124] focus:outline-none focus:border-[#1A73E8] transition-all appearance-none cursor-pointer"
              >
                <option value="Asia/Kolkata">India Standard Time (IST)</option>
                <option value="America/New_York">Eastern Time (ET)</option>
                <option value="Europe/London">Greenwich Mean Time (GMT)</option>
                <option value="America/Los_Angeles">Pacific Time (PT)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-2 flex items-center gap-2">
                <Clock size={14} /> Time Format
              </label>
              <div className="flex bg-[#F8F9FA] border border-[#DADCE0] rounded-xl p-1" role="group" aria-label="Time format selection">
                <button 
                  type="button"
                  onClick={() => setProfile(prev => ({ ...prev, timeFormat: "12h" }))}
                  className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${profile.timeFormat === "12h" ? "bg-white shadow-sm border border-[#DADCE0] text-[#1A73E8]" : "text-[#5F6368] hover:text-[#202124]"}`}
                >
                  12-hour (AM/PM)
                </button>
                <button 
                  type="button"
                  onClick={() => setProfile(prev => ({ ...prev, timeFormat: "24h" }))}
                  className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${profile.timeFormat === "24h" ? "bg-white shadow-sm border border-[#DADCE0] text-[#1A73E8]" : "text-[#5F6368] hover:text-[#202124]"}`}
                >
                  24-hour
                </button>
              </div>
            </div>
          </div>
        </motion.div>

        {/* BENTO 3: Global Scheduling Preferences */}
        <motion.div variants={bentoVariants} className="md:col-span-2 bg-white border border-[#DADCE0] rounded-3xl p-8 shadow-sm">
          <h2 className="text-lg font-semibold text-[#202124] mb-6">Default Scheduling Rules</h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="p-5 rounded-2xl border border-[#DADCE0] bg-[#F8F9FA] hover:border-[#1A73E8] transition-colors">
              <div className="flex items-center gap-3 mb-3 text-[#202124]">
                <div className="p-2 bg-[#E8F0FE] text-[#1A73E8] rounded-lg">
                  <Calendar size={18} />
                </div>
                <span className="font-medium">Buffer Time</span>
              </div>
              <p className="text-xs text-[#5F6368] mb-4 line-clamp-2">
                Add extra time before and after events to avoid back-to-back meetings.
              </p>
              <label htmlFor="bufferMinutes" className="sr-only">Buffer time in minutes</label>
              <select 
                id="bufferMinutes"
                name="bufferMinutes"
                value={profile.bufferMinutes}
                onChange={handleInputChange}
                className="w-full bg-white border border-[#DADCE0] rounded-xl px-4 py-2.5 text-sm text-[#202124] focus:outline-none focus:border-[#1A73E8]"
              >
                <option value={0}>No buffer</option>
                <option value={5}>5 minutes</option>
                <option value={15}>15 minutes</option>
                <option value={30}>30 minutes</option>
              </select>
            </div>
          </div>
        </motion.div>

        {/* BENTO 4: Danger Zone */}
        <motion.div variants={bentoVariants} className="bg-white border border-[#DADCE0] rounded-3xl p-8 shadow-sm relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-[#D93025]"></div>
          <h2 className="text-lg font-semibold text-[#D93025] mb-2 flex items-center gap-2">
            <ShieldAlert size={18} /> Security
          </h2>
          <p className="text-sm text-[#5F6368] mb-6">
            Manage your account security or permanently delete your account data.
          </p>
          
          <div className="space-y-3 mt-auto">
            <button
              onClick={handleChangePassword}
              type="button"
              className="w-full py-2.5 px-4 text-sm font-medium text-[#202124] border border-[#DADCE0] rounded-xl hover:bg-[#F8F9FA] transition-colors text-left"
            >
              Change Password
            </button>
            <button
              onClick={handleDeleteAccount}
              type="button"
              className="w-full py-2.5 px-4 text-sm font-medium text-[#D93025] border border-[#FCE8E6] bg-[#FCE8E6]/50 rounded-xl hover:bg-[#FCE8E6] transition-colors text-left"
            >
              Delete Account
            </button>
          </div>
        </motion.div>

      </motion.div>
    </div>
  );
}
