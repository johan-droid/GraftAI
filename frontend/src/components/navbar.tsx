"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Cpu, Calendar, Bot, LogIn, Command } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import PulsePing from "./ui/pulse-ping";
import { useNotificationContext } from "@/providers/notification-provider";

const NAV_ITEMS = [
  { name: "Dashboard", href: "/dashboard", icon: Command },
  { name: "Features", href: "/#features", icon: Bot },
  { name: "Pricing", href: "/pricing", icon: Calendar },
];

export function Navbar() {
  const pathname = usePathname();
  const { activePing } = useNotificationContext();
  const isAuthPage = pathname === "/login" || pathname === "/register" || pathname === "/auth-callback";

  if (isAuthPage) return null;

  return (
    <nav className="floating-nav">
      <Link href="/" className="flex items-center gap-2 pr-3 border-r border-white/10 group">
        <motion.div 
          whileHover={{ rotate: 10, scale: 1.1 }}
          className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-primary/20"
        >
          <Cpu className="text-white w-4 h-4" />
        </motion.div>
        <span className="hidden sm:inline-block font-bold text-sm tracking-tight text-white/90 group-hover:text-white transition-colors">
          GraftAI
        </span>
      </Link>
      
      <div className="flex items-center gap-1 sm:gap-6 px-2">
        <PulsePing status={activePing} className="mr-1 sm:mr-0" />
        
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "relative nav-link text-[10px] sm:text-xs font-bold uppercase tracking-widest transition-all px-2 py-1",
                isActive ? "text-white" : "text-slate-400 hover:text-slate-200"
              )}
            >
              <item.icon className="w-4 h-4 sm:hidden" />
              <span className="hidden sm:inline">{item.name}</span>
              {isActive && (
                <motion.div 
                  layoutId="nav-underline"
                  className="absolute -bottom-1 left-2 right-2 h-0.5 bg-primary rounded-full"
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
            </Link>
          );
        })}
      </div>

      <Link
        href="/login"
        className="ml-auto px-4 py-1.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-white text-[10px] sm:text-xs font-black uppercase tracking-tighter transition-all flex items-center gap-2 group"
      >
        <LogIn className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
        <span>Sync</span>
      </Link>
    </nav>
  );
}
