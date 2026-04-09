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
  MapPin
} from "lucide-react";
import { useAuth } from "@/providers/auth-provider";

export function Sidebar() {
  const pathname = usePathname();
  const { logout } = useAuth();

  const NAV_ITEMS = [
    { label: "Overview", icon: LayoutDashboard, href: "/dashboard" },
    { label: "Calendar", icon: CalendarDays, href: "/dashboard/calendar" },
    { label: "Event Types", icon: MapPin, href: "/dashboard/event-types" },
    { label: "AI Assistant", icon: Bot, href: "/dashboard/ai" },
    { label: "Plugins", icon: Puzzle, href: "/dashboard/plugins" },
    { label: "Settings", icon: Settings, href: "/dashboard/settings" },
  ];

  return (
    <aside className="flex h-full flex-col justify-between bg-white/[0.02] p-4 backdrop-blur-3xl">
      <div>
        <div className="mb-8 px-4 flex items-center h-10 pt-2">
          <div className="h-8 w-8 rounded-xl bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 mr-3">
             <span className="font-bold text-white text-lg">G</span>
          </div>
          <span className="text-xl font-bold tracking-tight text-white">GraftAI</span>
        </div>

        <nav className="flex flex-col space-y-1.5">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "group flex items-center rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200",
                  isActive 
                    ? "bg-indigo-500/10 text-indigo-400" 
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                )}
              >
                <item.icon className={cn("mr-3 h-5 w-5", isActive ? "text-indigo-400" : "text-slate-500 group-hover:text-slate-300")} />
                {item.label}
              </Link>
            )
          })}
        </nav>
      </div>

      <div className="mt-auto pt-8">
         <button 
           onClick={logout}
           className="flex w-full items-center rounded-xl px-4 py-3 text-sm font-medium text-slate-500 transition-colors hover:bg-white/5 hover:text-red-400 group"
         >
            <LogOut className="mr-3 h-5 w-5 text-slate-600 group-hover:text-red-400" />
            Sign Out
         </button>
      </div>
    </aside>
  );
}