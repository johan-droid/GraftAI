"use client";

import { useSyncEngine } from "@/hooks/useSyncEngine";
import { CloudOff, Wifi, Bell } from "lucide-react";
import { useAuth } from "@/providers/auth-provider";
import { Badge } from "@/components/ui/Badge";

export function Topbar() {
  const { isOnline } = useSyncEngine();
  const { user } = useAuth();
  const profileName = user?.full_name?.split(" ")[0] ?? user?.email?.split("@")[0] ?? "Guest";

  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-white/[0.05] bg-[#070711]/80 px-4 md:px-6 backdrop-blur-xl supports-backdrop-blur:bg-[#070711]/60">
      <div className="flex items-center lg:hidden">
        {/* Mobile Logo Logo */}
        <div className="h-8 w-8 rounded-xl bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 mr-3">
            <span className="font-bold text-white">G</span>
        </div>
      </div>

      <div className="ml-auto flex items-center gap-4">
        {isOnline ? (
          <Badge variant="success" className="gap-1.5 hidden sm:flex">
             <Wifi className="h-3 w-3" /> Online
          </Badge>
        ) : (
          <Badge variant="warning" className="gap-1.5 flex animate-pulse">
             <CloudOff className="h-3 w-3" /> Offline
          </Badge>
        )}
        
        <button className="relative rounded-full p-2 text-slate-400 hover:bg-white/5 hover:text-white transition-colors">
          <Bell className="h-5 w-5" />
          <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-indigo-500 ring-2 ring-[#070711]" />
        </button>
        
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 text-sm font-medium text-white shadow-inner">
          {profileName.charAt(0).toUpperCase()}
        </div>
      </div>
    </header>
  );
}