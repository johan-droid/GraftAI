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
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-white/[0.06] bg-[#080d17]/75 px-4 md:px-6 backdrop-blur-xl supports-backdrop-blur:bg-[#080d17]/55">
      <div className="flex items-center lg:hidden">
        {/* Mobile Logo Logo */}
        <div className="mr-3 flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-500/90 shadow-md shadow-indigo-500/20">
            <span className="font-bold text-white">G</span>
        </div>
      </div>

      <div className="ml-auto flex items-center gap-4">
        {isOnline ? (
          <Badge variant="success" className="gap-1.5 hidden sm:flex">
             <Wifi className="h-3 w-3" /> Online
          </Badge>
        ) : (
          <Badge variant="warning" className="flex gap-1.5">
             <CloudOff className="h-3 w-3" /> Offline
          </Badge>
        )}
        
        <button className="relative rounded-full p-2 text-slate-400 transition-colors hover:bg-white/[0.05] hover:text-white">
          <Bell className="h-5 w-5" />
          <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-indigo-400 ring-2 ring-[#080d17]" />
        </button>
        
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-tr from-indigo-500 to-violet-500 text-sm font-medium text-white shadow-inner shadow-black/25">
          {profileName.charAt(0).toUpperCase()}
        </div>
      </div>
    </header>
  );
}