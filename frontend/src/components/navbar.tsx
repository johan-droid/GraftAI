"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Cpu, Calendar, Bot, LogIn } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { name: "Home", href: "/", icon: Cpu },
  { name: "Features", href: "/#features", icon: Bot },
  { name: "Pricing", href: "/pricing", icon: Calendar },
];

export function Navbar() {
  const pathname = usePathname();
  const isDashboard = pathname.startsWith("/dashboard");

  if (isDashboard || pathname === "/login" || pathname === "/register") return null;

  return (
    <nav className="floating-nav">
      <Link href="/" className="flex items-center gap-2 pr-2 border-r border-card-border">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
          <Cpu className="text-white w-4 h-4" />
        </div>
        <span className="hidden sm:inline-block font-bold text-sm tracking-tight">GraftAI</span>
      </Link>
      
      <div className="flex items-center gap-1 sm:gap-4">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.name}
            href={item.href}
            className={cn(
              "nav-link text-xs font-bold uppercase tracking-widest text-slate-400 hover:text-white transition-colors flex items-center gap-2",
              pathname === item.href && "text-primary"
            )}
          >
            <item.icon className="w-4 h-4 sm:hidden" />
            <span className="hidden sm:inline">{item.name}</span>
          </Link>
        ))}
      </div>

      <Link
        href="/login"
        className="ml-2 px-4 py-1.5 rounded-full bg-primary text-white text-[10px] sm:text-xs font-black uppercase tracking-tighter hover:scale-105 transition-transform flex items-center gap-2"
      >
        <LogIn className="w-3 h-3" />
        <span>Sync</span>
      </Link>
    </nav>
  );
}
