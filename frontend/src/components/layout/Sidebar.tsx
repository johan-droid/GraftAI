"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, Calendar, PlusCircle, 
  Users, Zap, BarChart3, Settings, MessageSquare 
} from "lucide-react";

const NAV_ITEMS = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "My Calendar", href: "/dashboard/calendar", icon: Calendar },
  { name: "AI Copilot", href: "/copilot", icon: MessageSquare },
  { name: "Event Types", href: "/dashboard/event-types", icon: PlusCircle },
  { name: "Team & Resources", href: "/dashboard/teams", icon: Users },
  { name: "Workflows", href: "/dashboard/workflows", icon: Zap },
  { name: "Analytics", href: "/dashboard/analytics", icon: BarChart3 },
];

import { useSession } from "next-auth/react";

import { useEffect, useState } from "react";
import { getUsageStats } from "@/lib/api";

export function Sidebar() {
  const pathname = usePathname();
  const { data: session } = useSession();
  const [stats, setStats] = useState<any>(null);
  
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getUsageStats();
        setStats(data);
      } catch (err) {
        console.error("Failed to fetch stats", err);
      }
    };
    if (session?.user) fetchStats();
  }, [session]);
  
  const user = session?.user;
  const tier = stats?.tier || user?.tier || "Free";
  const aiCount = stats?.daily_ai_usage || user?.daily_ai_count || 0;
  
  // Dynamic limits based on tier if not provided in user object
  const getLimits = (tier: string) => {
    const t = tier.toLowerCase();
    switch(t) {
      case 'enterprise':
        return { ai: 1000000, tokens: 10000000, api: 1000000, bookings: 10000 };
      case 'elite':
        return { ai: 2000, tokens: 500000, api: 50000, bookings: 1000 };
      case 'pro':
        return { ai: 200, tokens: 50000, api: 5000, bookings: 100 };
      default:
        return { ai: 10, tokens: 5000, api: 100, bookings: 5 };
    }
  };

  const limits = getLimits(tier);
  const aiLimit = user?.daily_ai_limit || limits.ai;
  const progress = Math.min((aiCount / aiLimit) * 100, 100);
  
  // Dynamic percentages for SaaS meters
  const tokenPct = Math.min(((stats?.ai_tokens || 0) / limits.tokens) * 100, 100);
  const apiPct = Math.min(((stats?.api_calls || 0) / limits.api) * 100, 100);
  const bookingPct = Math.min(((stats?.scheduling_count || 0) / limits.bookings) * 100, 100);

  const isPro = tier.toLowerCase() !== "free";

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

      {/* Meter Reading / Quota Indicator */}
      <div className="p-4 border-t border-[#DADCE0] shrink-0 bg-[#F8F9FA]">
        <div className="bg-white p-4 rounded-2xl border border-[#DADCE0] shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="flex flex-col">
              <p className="text-[10px] uppercase font-bold text-[#5F6368] tracking-wider mb-0.5">SaaS Grade</p>
              <p className="text-sm font-bold text-[#202124]">{tier.charAt(0).toUpperCase() + tier.slice(1)} Plan</p>
            </div>
            <Zap size={16} className={isPro ? "text-[#E37400]" : "text-[#5F6368]"} />
          </div>

          <div className="space-y-4">
            {/* AI Tokens Meter */}
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-[#444746] font-medium">AI Tokens</span>
                <span className="text-[#1A73E8] font-bold">{stats?.ai_tokens?.toLocaleString() || 0}</span>
              </div>
              <div className="w-full bg-[#F1F3F4] rounded-full h-1 overflow-hidden">
                <div className="bg-[#1A73E8] h-full" style={{ width: `${tokenPct}%` }}></div>
              </div>
            </div>

            {/* API Calls Meter */}
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-[#444746] font-medium">API Calls</span>
                <span className="text-[#1A73E8] font-bold">{stats?.api_calls?.toLocaleString() || 0}</span>
              </div>
              <div className="w-full bg-[#F1F3F4] rounded-full h-1 overflow-hidden">
                <div className="bg-[#34A853] h-full" style={{ width: `${apiPct}%` }}></div>
              </div>
            </div>

            {/* Scheduling Meter */}
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-[#444746] font-medium">Total Bookings</span>
                <span className="text-[#1A73E8] font-bold">{stats?.scheduling_count?.toLocaleString() || 0}</span>
              </div>
              <div className="w-full bg-[#F1F3F4] rounded-full h-1 overflow-hidden">
                <div className="bg-[#FBBC04] h-full" style={{ width: `${bookingPct}%` }}></div>
              </div>
            </div>

            {/* Daily Limit (Old AI Count) */}
            <div className="pt-2 border-t border-[#F1F3F4]">
              <div className="flex justify-between text-[10px] mb-1">
                <span className="text-[#5F6368]">Daily AI Copilot</span>
                <span className="text-[#5F6368] font-medium">{aiCount} / {aiLimit}</span>
              </div>
              <div className="w-full bg-[#F1F3F4] rounded-full h-1 overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all duration-1000 ${progress > 90 ? "bg-red-500" : "bg-[#1A73E8]"}`}
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
