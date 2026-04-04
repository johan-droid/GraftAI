"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { LayoutDashboard, Calendar, Settings, Bot, Menu, X, LogOut, Globe2, Puzzle, CreditCard, Crown, Zap } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthContext } from "@/app/providers/auth-provider";

const SIDEBAR_LINKS = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Client Tools", href: "/dashboard/analytics", icon: Globe2 },
  { name: "Calendar", href: "/dashboard/calendar", icon: Calendar },
  { name: "AI Copilot", href: "/dashboard/ai", icon: Bot },
  { name: "Plugins", href: "/dashboard/plugins", icon: Puzzle },
  { name: "Billing", href: "/dashboard/settings/billing", icon: CreditCard },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { logout, user } = useAuthContext();

  return (
    <div className="flex h-screen w-full bg-[#020617] overflow-hidden relative selection:bg-primary/30 selection:text-primary-foreground">
      
      {/* 🚀 GALAXY HUD LAYERS */}
      <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
        {/* Animated Starfield */}
        <div className="starfield-container absolute inset-0 opacity-40">
          <div className="stars-small animate-pulse-slow bg-white/20" />
          <div className="stars-medium animate-pulse bg-white/10" />
          <div className="stars-large animate-bounce-slow bg-primary/20" />
        </div>
        
        {/* Dynamic Nebulae */}
        <div className="absolute -top-[10%] -right-[10%] w-[60%] h-[60%] bg-blue-600/10 rounded-full blur-[140px] animate-pulse-slow" />
        <div className="absolute -bottom-[20%] -left-[10%] w-[50%] h-[50%] bg-fuchsia-600/10 rounded-full blur-[160px] animate-pulse" />
        <div className="absolute top-[30%] left-[20%] w-[40%] h-[40%] bg-primary/5 rounded-full blur-[120px]" />
      </div>

      <style jsx global>{`
        @keyframes pulse-slow {
          0%, 100% { opacity: 0.3; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(1.05); }
        }
        .animate-pulse-slow {
          animation: pulse-slow 8s infinite ease-in-out;
        }
        .starfield-container::before {
          content: "";
          position: absolute;
          inset: 0;
          background-image: 
            radial-gradient(1px 1px at 20px 30px, #fff, rgba(0,0,0,0)),
            radial-gradient(1px 1px at 40px 70px, #fff, rgba(0,0,0,0)),
            radial-gradient(1.5px 1.5px at 150px 150px, rgba(236, 72, 153, 0.4), rgba(0,0,0,0)),
            radial-gradient(2px 2px at 300px 300px, rgba(79, 70, 229, 0.4), rgba(0,0,0,0));
          background-repeat: repeat;
          background-size: 400px 400px;
          opacity: 0.3;
        }
      `}</style>

      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex flex-col w-60 border-r border-slate-800/50 bg-slate-950/40 backdrop-blur-xl z-20">
        <div className="p-5 flex items-center gap-2.5 border-b border-slate-800/50">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary to-fuchsia-600 flex items-center justify-center shadow-[0_0_12px_rgba(79,70,229,0.4)]">
            <span className="text-white font-bold text-base leading-none">G</span>
          </div>
          <span className="font-bold text-base tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">GraftAI</span>
        </div>

        <nav className="flex-1 px-4 py-8 space-y-2">
          {SIDEBAR_LINKS.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.name}
                href={link.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  isActive 
                    ? "bg-primary/10 text-primary font-medium" 
                    : "text-slate-400 hover:text-white hover:bg-slate-800/50"
                }`}
              >
                <link.icon className="w-5 h-5" />
                {link.name}
                {isActive && (
                  <motion.div 
                    layoutId="active-nav" 
                    className="absolute left-0 w-1 h-8 bg-primary rounded-r-full"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  />
                )}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-800/50 space-y-4">
          {/* User Tier Badge */}
          {user?.tier && (
             <div className={`mx-2 p-3 rounded-xl border flex items-center gap-3 ${
                user.tier === 'free' 
                ? 'bg-slate-900/50 border-slate-800 text-slate-400' 
                : 'bg-primary/5 border-primary/20 text-primary shadow-[0_0_15px_rgba(79,70,229,0.1)]'
             }`}>
                {user.tier === 'free' ? <Zap className="w-4 h-4" /> : <Crown className="w-4 h-4" />}
                <div className="flex flex-col">
                  <span className="text-[10px] font-black uppercase tracking-widest leading-none mb-1">
                    {user.tier} Edition
                  </span>
                  <span className="text-[8px] font-medium opacity-60 leading-none">
                    Individual SaaS
                  </span>
                </div>
             </div>
          )}

          <button onClick={logout} className="flex w-full items-center gap-3 px-4 py-3 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all">
            <LogOut className="w-5 h-5" />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      {/* Mobile Header & Content Wrapper */}
      <div className="flex-1 flex flex-col min-w-0 z-10 relative">
        
        {/* Neural Pulse Header (Desktop) */}
        <header className="hidden lg:flex items-center justify-between px-8 py-4 border-b border-white/5 backdrop-blur-sm">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-4">
              {/* Status indicators removed for pinpoint accuracy */}
            </div>
          </div>
          <div className="flex items-center gap-6">
          <div className="flex items-center gap-6">
             {/* Link indicators removed */}
          </div>
          </div>
        </header>
        
        {/* Mobile Header */}
        <header className="lg:hidden flex items-center justify-between p-3.5 border-b border-slate-800/50 bg-slate-950/80 backdrop-blur-md sticky top-0 z-30">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-primary to-fuchsia-600 flex items-center justify-center shadow-[0_0_10px_rgba(79,70,229,0.3)]">
              <span className="text-white font-bold text-xs leading-none">G</span>
            </div>
            <span className="font-bold text-sm tracking-tight">GraftAI</span>
          </div>
          <button 
            onClick={() => setMobileMenuOpen(true)}
            aria-label="Open menu"
            title="Open menu"
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 active:scale-95 transition-all"
          >
            <Menu className="w-4 h-4" />
          </button>
        </header>

        {/* Mobile Sidebar Overlay */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <>
              <motion.div 
                initial={{ opacity: 0 }} 
                animate={{ opacity: 1 }} 
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
                onClick={() => setMobileMenuOpen(false)}
              />
              <motion.aside
                initial={{ x: "100%" }}
                animate={{ x: 0 }}
                exit={{ x: "100%" }}
                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                className="fixed inset-y-0 right-0 w-64 bg-slate-950 border-l border-slate-800 z-50 flex flex-col shadow-2xl lg:hidden"
              >
                <div className="flex items-center justify-between p-4 border-b border-slate-800/50">
                  <span className="font-medium text-slate-200">Menu</span>
                  <button
                    onClick={() => setMobileMenuOpen(false)}
                    aria-label="Close menu"
                    title="Close menu"
                    className="p-2 text-slate-400 hover:text-white"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
                
                <nav className="flex-1 px-3 py-6 space-y-1">
                  {SIDEBAR_LINKS.map((link) => {
                    const isActive = pathname === link.href;
                    return (
                      <Link
                        key={link.name}
                        href={link.href}
                        onClick={() => setMobileMenuOpen(false)}
                        className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                          isActive 
                            ? "bg-primary/20 text-primary font-medium" 
                            : "text-slate-400 hover:text-white hover:bg-slate-900"
                        }`}
                      >
                        <link.icon className="w-5 h-5" />
                        {link.name}
                      </Link>
                    );
                  })}
                </nav>

                <div className="p-4 border-t border-slate-800/50">
                  <button onClick={logout} className="flex w-full items-center gap-3 px-4 py-3 rounded-xl text-slate-400 hover:bg-slate-900 transition-all">
                    <LogOut className="w-5 h-5" />
                    <span>Sign out</span>
                  </button>
                </div>
              </motion.aside>
            </>
          )}
        </AnimatePresence>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-4 md:p-10 scroll-smooth">
          <motion.div
            key={pathname}
            initial={{ opacity: 0, scale: 0.995 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="h-full w-full max-w-6xl mx-auto"
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
}
