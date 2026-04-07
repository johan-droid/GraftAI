"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";
import { Cpu, Calendar, Bot, LogIn, Command, Menu, X, ArrowRight } from "lucide-react";
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useAuthContext } from "@/app/providers/auth-provider";
import PulsePing from "./ui/pulse-ping";
import { useNotificationContext } from "@/providers/notification-provider";
import { AnimatePresence } from "framer-motion";

const NAV_ITEMS = [
  { name: "Dashboard", href: "/dashboard", icon: Command },
  { name: "Features", href: "/#features", icon: Bot },
  { name: "Pricing", href: "/pricing", icon: Calendar },
];

export function Navbar() {
  const pathname = usePathname();
  const { isAuthenticated } = useAuthContext();
  const { activePing } = useNotificationContext();
  const [mobileOpen, setMobileOpen] = useState(false);
  const isAuthPage = pathname === "/login" || pathname === "/register" || pathname === "/auth-callback";

  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [mobileOpen]);

  const visibleNavItems = NAV_ITEMS.filter(item => {
    if (item.href === "/dashboard") return isAuthenticated;
    return true;
  });

  if (isAuthPage) return null;

  return (
    <nav className="floating-nav">
      <Link href="/" className="flex items-center gap-2 pr-3 border-r border-white/10 group">
        <motion.div 
          whileHover={{ rotate: 5, scale: 1.05 }}
          className="w-10 h-10 rounded-xl flex items-center justify-center transition-all overflow-hidden"
        >
          <Image src="/assets/logo.png" alt="GraftAI" width={40} height={40} className="object-contain" />
        </motion.div>
        <span className="hidden sm:inline-block font-bold text-sm tracking-tight text-white/90 group-hover:text-white transition-colors">
          GraftAI
        </span>
      </Link>
      
      <div className="flex items-center gap-1 sm:gap-6 px-2 ml-auto sm:ml-0">
        <PulsePing status={activePing} className="mr-1 sm:mr-4" />
        
        <div className="hidden sm:flex items-center gap-6">
          {visibleNavItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "relative nav-link text-xs font-bold uppercase tracking-widest transition-all px-2 py-1",
                  isActive ? "text-white" : "text-slate-400 hover:text-slate-200"
                )}
              >
                <span>{item.name}</span>
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

        <button
          onClick={() => setMobileOpen(true)}
          className="sm:hidden flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 border border-white/10 text-slate-400 active:scale-95 transition-all"
        >
          <Menu className="w-4 h-4" />
        </button>
      </div>

      {!isAuthenticated ? (
        <Link
          href="/login"
          className="hidden sm:flex ml-auto px-4 py-1.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-white text-xs font-black uppercase tracking-tighter transition-all items-center gap-2 group"
        >
          <LogIn className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
          <span>Sync</span>
        </Link>
      ) : null}

      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)}
              className="fixed inset-0 z-[60] bg-black/60 backdrop-blur-sm"
            />
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed inset-y-0 right-0 z-[61] w-[min(85vw,320px)] bg-[#070711] border-l border-white/10 p-6 flex flex-col"
            >
              <div className="flex items-center justify-between mb-8">
                <span className="font-bold text-sm tracking-tight text-white/50 uppercase">Menu</span>
                <button 
                  onClick={() => setMobileOpen(false)}
                  className="p-2 -mr-2 text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="flex flex-col gap-2">
                {visibleNavItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className="flex items-center justify-between p-4 rounded-xl bg-white/[0.03] border border-white/[0.06] text-sm font-semibold text-slate-200 active:bg-white/[0.06] transition-all"
                  >
                    <span>{item.name}</span>
                    <ArrowRight className="w-4 h-4 text-slate-600" />
                  </Link>
                ))}
              </div>

              <div className="mt-auto pt-6 border-t border-white/10">
                {!isAuthenticated && (
                  <Link
                    href="/login"
                    onClick={() => setMobileOpen(false)}
                    className="flex items-center justify-center gap-2 w-full py-4 rounded-xl bg-white text-black text-sm font-bold active:scale-[0.98] transition-all"
                  >
                    <LogIn className="w-4 h-4" />
                    <span>Sign in to Sync</span>
                  </Link>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </nav>
  );
}
