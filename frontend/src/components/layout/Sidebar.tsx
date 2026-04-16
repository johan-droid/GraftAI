"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, Calendar, PlusCircle, 
  Users, Zap, BarChart3, Settings 
} from "lucide-react";

const NAV_ITEMS = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "My Calendar", href: "/dashboard/calendar", icon: Calendar },
  { name: "Event Types", href: "/dashboard/event-types", icon: PlusCircle },
  { name: "Team & Resources", href: "/dashboard/teams", icon: Users },
  { name: "Workflows", href: "/dashboard/workflows", icon: Zap },
  { name: "Analytics", href: "/dashboard/analytics", icon: BarChart3 },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-[#F8F9FA] border-r border-[#DADCE0] flex flex-col h-screen hidden md:flex shrink-0">
      {/* App Brand */}
      <div className="h-16 flex items-center px-6 border-b border-[#DADCE0] shrink-0">
        <Link href="/dashboard" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
          <div className="w-8 h-8 rounded-lg bg-[#1A73E8] flex items-center justify-center text-white font-bold text-sm shadow-sm">
            G
          </div>
          <span className="font-medium text-lg tracking-tight text-[#202124]">GraftAI</span>
        </Link>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-6 space-y-1 overflow-y-auto custom-scrollbar">
        <div className="text-[11px] font-bold text-[#5F6368] uppercase tracking-wider mb-4 px-3">
          Workspace
        </div>
        
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || (pathname?.startsWith(`${item.href}/`) && item.href !== '/dashboard');
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-full transition-all text-sm font-medium group ${
                isActive 
                  ? "bg-[#E8F0FE] text-[#1967D2]" 
                  : "text-[#444746] hover:bg-[#F1F3F4] hover:text-[#202124]"
              }`}
            >
              <item.icon 
                size={20} 
                className={isActive ? "text-[#1967D2]" : "text-[#5F6368] group-hover:text-[#202124] transition-colors"} 
              />
              {item.name}
            </Link>
          );
        })}

        <div className="mt-8 mb-4 px-3 text-[11px] font-bold text-[#5F6368] uppercase tracking-wider">
          Configuration
        </div>
        
        <Link
          href="/dashboard/settings"
          className={`flex items-center gap-3 px-3 py-2.5 rounded-full transition-all text-sm font-medium group ${
            pathname?.startsWith('/dashboard/settings')
              ? "bg-[#E8F0FE] text-[#1967D2]" 
              : "text-[#444746] hover:bg-[#F1F3F4] hover:text-[#202124]"
          }`}
        >
          <Settings size={20} className={pathname?.startsWith('/dashboard/settings') ? "text-[#1967D2]" : "text-[#5F6368] group-hover:text-[#202124]"} />
          Settings
        </Link>
      </nav>

      {/* Quota Indicator */}
      <div className="p-4 border-t border-[#DADCE0] shrink-0 bg-[#F8F9FA]">
        <div className="bg-white p-4 rounded-2xl border border-[#DADCE0] shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-semibold text-[#202124]">Pro Plan</p>
            <Zap size={14} className="text-[#E37400]" />
          </div>
          <div className="w-full bg-[#F1F3F4] rounded-full h-1.5 mb-2 overflow-hidden">
            <div className="bg-[#1A73E8] h-1.5 rounded-full transition-all duration-1000 w-[45%]"></div>
          </div>
          <p className="text-[11px] text-[#5F6368]">450 / 1000 AI Automations</p>
        </div>
      </div>
    </aside>
  );
}
