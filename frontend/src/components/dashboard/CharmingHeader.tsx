"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Sparkles, Calendar, Clock, ArrowRight } from "lucide-react";
import Link from "next/link";

interface CharmingHeaderProps {
  userName: string;
  upcomingCount?: number;
}

const WISHES = [
  "Strategic Oversight",
  "Synchronized Precision",
  "High-Density Productivity",
  "Sovereign Schedule Management",
  "Operational Excellence",
  "Optimized Workflow Momentum",
  "Architectural Focus",
];

export const CharmingHeader: React.FC<CharmingHeaderProps> = ({ userName, upcomingCount = 0 }) => {
  const [greeting, setGreeting] = useState("Status");
  const [wish, setWish] = useState(WISHES[0]);

  useEffect(() => {
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 12) setGreeting("Morning Briefing");
    else if (hour >= 12 && hour < 17) setGreeting("Afternoon Pulse");
    else if (hour >= 17 && hour < 22) setGreeting("Evening Review");
    else setGreeting("Night Operations");

    setWish(WISHES[Math.floor(Math.random() * WISHES.length)]);
  }, []);

  const initial = userName?.charAt(0).toUpperCase() || "G";

  const container = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const item = {
    hidden: { opacity: 0, y: 8, filter: "blur(4px)" },
    visible: { opacity: 1, y: 0, filter: "blur(0px)" },
  };

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="visible"
      className="relative flex flex-col md:flex-row md:items-end justify-between gap-4 pb-4 border-b border-white/[0.04]"
    >
      {/* Abstract Background Letter */}
      <div className="absolute top-0 -left-6 md:-left-12 pointer-events-none select-none opacity-[0.03] text-[180px] md:text-[240px] font-black italic tracking-tighter leading-none text-white transition-all">
        {initial}
      </div>

      <div className="relative z-10 space-y-1 transition-all">
        <motion.div variants={item} className="flex items-center gap-2">
          <div className="flex h-5 w-5 items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/20">
            <Sparkles className="w-2.5 h-2.5 text-indigo-400" />
          </div>
          <span className="text-indigo-400 text-[9px] font-black underline decoration-indigo-500/30 underline-offset-4 uppercase tracking-[0.25em]">
            {greeting} // {userName}
          </span>
        </motion.div>

        <motion.h1 
          variants={item}
          className="font-serif text-3xl sm:text-4xl md:text-5xl font-black tracking-tight leading-tight"
        >
          <span className="bg-gradient-to-r from-white via-white to-white/50 bg-clip-text text-transparent">
            {wish}
          </span>
        </motion.h1>

        <motion.div variants={item} className="flex items-center gap-3 text-slate-500 font-bold text-[11px] pt-1 uppercase tracking-widest">
           <div className="flex items-center gap-1.5 text-slate-400">
             <Calendar className="w-3.5 h-3.5 text-indigo-500/60" />
             <span>{upcomingCount} ACTIVE</span>
           </div>
           <span className="h-3 w-px bg-slate-800" />
           <p className="flex items-center gap-1.5">
             <Clock className="w-3.5 h-3.5" />
             {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
           </p>
        </motion.div>
      </div>

      <motion.div variants={item} className="relative z-10 shrink-0 pb-0.5">
        <Link 
          href="/dashboard/calendar"
          className="group relative flex items-center gap-2.5 px-5 py-3 rounded-xl bg-white text-black font-black text-[11px] uppercase tracking-wider transition-all hover:bg-slate-200 active:scale-95 shadow-xl shadow-white/5"
        >
          <span>Initiate Event</span>
          <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
        </Link>
      </motion.div>
    </motion.div>
  );
};
