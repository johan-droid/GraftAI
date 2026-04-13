"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { 
  LayoutDashboard, 
  CalendarDays, 
  Bot, 
  Settings, 
  Puzzle, 
  LogOut,
  MapPin,
  Terminal,
  Activity
} from "lucide-react";
import { useAuth } from "@/app/providers/auth-provider";

export function Sidebar() {
  const pathname = usePathname();
  const { logout } = useAuth();

  const NAV_ITEMS = [
    { label: "OVERVIEW", icon: LayoutDashboard, href: "/dashboard" },
    { label: "CALENDAR", icon: CalendarDays, href: "/dashboard/calendar" },
    { label: "EVENT_TYPES", icon: MapPin, href: "/dashboard/event-types" },
    { label: "COGNITIVE_AI", icon: Bot, href: "/dashboard/ai" },
    { label: "CLUSTER_PLUGINS", icon: Puzzle, href: "/dashboard/plugins" },
    { label: "DEV_CORNER", icon: Terminal, href: "/dashboard/developer" },
    { label: "SYS_SETTINGS", icon: Settings, href: "/dashboard/settings" },
  ];

  return (
    <aside className="flex h-full flex-col justify-between bg-[var(--bg-base)] border-r border-dashed border-[var(--border-subtle)] font-mono">
      <div>
        <div className="mb-10 px-6 flex items-center h-16 border-b border-dashed border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
          <div className="mr-3 flex h-8 w-8 items-center justify-center border border-[var(--primary)] bg-[var(--bg-base)] shadow-[0_0_10px_var(--primary-glow)]">
             <span className="font-black text-[var(--primary)] text-lg">G</span>
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-black tracking-tighter text-[var(--text-primary)] uppercase">GraftAI_OS</span>
            <span className="text-[9px] text-[var(--primary)] font-bold tracking-widest opacity-80">v3.0.4-STABLE</span>
          </div>
        </div>

        <nav className="flex flex-col px-2 space-y-1">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "group flex items-center px-4 py-3 text-[11px] font-black tracking-widest transition-all duration-200 border-l-2",
                  isActive 
                    ? "bg-[var(--bg-hover)] text-[var(--primary)] border-[var(--primary)] shadow-[inset_0_0_15px_var(--primary-glow)]" 
                    : "text-[var(--text-muted)] border-transparent hover:bg-[var(--bg-elevated)] hover:text-[var(--text-primary)]"
                )}
              >
                <item.icon className={cn("mr-3 h-4 w-4 transition-colors", isActive ? "text-[var(--primary)]" : "text-[var(--text-faint)] group-hover:text-[var(--primary)]")} />
                {item.label}
              </Link>
            )
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-dashed border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
         <div className="mb-4 px-2 py-2 border border-dashed border-[var(--border-subtle)] bg-[var(--bg-base)]">
            <div className="flex items-center justify-between mb-1">
               <span className="text-[10px] text-[var(--text-faint)] font-bold uppercase">Uptime_Pulse</span>
               <Activity className="h-3 w-3 text-[var(--primary)] animate-pulse" />
            </div>
            <div className="w-full h-1 bg-[var(--bg-hover)]">
               <div className="w-3/4 h-full bg-[var(--primary)]" />
            </div>
         </div>
         <button
           onClick={logout}
           className="group flex w-full items-center px-4 py-3 text-[10px] font-black tracking-widest text-[var(--text-muted)] transition-all hover:bg-[var(--accent)] hover:text-white border border-transparent hover:border-white/20"
         >
            <LogOut className="mr-3 h-4 w-4 transition-colors group-hover:text-white" />
            TERMINATE_SESSION
         </button>
      </div>
    </aside>
  );
}