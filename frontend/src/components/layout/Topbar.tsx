"use client";

import { useSession, signOut } from "next-auth/react";
import { Bell, Menu, Search } from "lucide-react";

export function Topbar() {
  const { data: session } = useSession();
  
  const firstInitial = session?.user?.name?.charAt(0).toUpperCase() || "U";

  return (
    <header className="h-16 bg-white border-b border-[#DADCE0] flex items-center justify-between px-4 sm:px-6 sticky top-0 z-40">
      
      <div className="flex items-center gap-4 flex-1">
        <button aria-label="Open menu" title="Open menu" className="p-2 -ml-2 rounded-full hover:bg-[#F1F3F4] text-[#5F6368] md:hidden transition-colors">
          <Menu size={24} />
        </button>

        <div className="hidden sm:flex items-center bg-[#F1F3F4] px-4 py-2.5 rounded-full w-full max-w-md focus-within:bg-white focus-within:shadow-sm focus-within:ring-1 focus-within:ring-[#1A73E8] transition-all">
          <Search size={18} className="text-[#5F6368]" />
          <input 
            type="text" 
            placeholder="Search events, bookings, or settings..." 
            className="bg-transparent border-none outline-none text-sm ml-3 w-full text-[#202124] placeholder:text-[#5F6368]"
          />
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-4 ml-4">
        <button aria-label="Notifications" title="Notifications" className="p-2 rounded-full hover:bg-[#F1F3F4] text-[#5F6368] transition-colors relative">
          <Bell size={20} />
          <span className="absolute top-2 right-2 w-2 h-2 bg-[#D93025] rounded-full border-2 border-white"></span>
        </button>

        <div className="h-6 w-px bg-[#DADCE0] mx-1"></div>

        <div className="flex items-center gap-3 pl-1">
          <div className="hidden sm:block text-right">
            <p className="text-sm font-medium text-[#202124] leading-tight">
              {session?.user?.name || "Loading..."}
            </p>
            <p className="text-[11px] text-[#5F6368]">
              {session?.user?.email || "Please wait"}
            </p>
          </div>
          
          <button 
            onClick={() => signOut({ callbackUrl: '/login' })}
            title="Sign out"
            className="w-9 h-9 rounded-full bg-[#1A73E8] text-white flex items-center justify-center font-medium text-sm hover:ring-2 hover:ring-offset-2 hover:ring-[#1A73E8] transition-all cursor-pointer shadow-sm"
          >
            {firstInitial}
          </button>
        </div>
      </div>
    </header>
  );
}
