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
  "Ready to conquer your schedule?",
  "Let's make today remarkably productive.",
  "Your time is your most valuable asset.",
  "Focus on what matters, we'll handle the rest.",
  "A clear calendar is a clear mind.",
  "Seize the day, one meeting at a time.",
];

export const CharmingHeader: React.FC<CharmingHeaderProps> = ({ userName, upcomingCount = 0 }) => {
  const [greeting, setGreeting] = useState("Good morning");
  const [wish, setWish] = useState(WISHES[0]);

  useEffect(() => {
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 12) setGreeting("Good morning");
    else if (hour >= 12 && hour < 17) setGreeting("Good afternoon");
    else if (hour >= 17 && hour < 22) setGreeting("Good evening");
    else setGreeting("Good night");

    // Randomize wish for a 'charming' experience on refresh
    setWish(WISHES[Math.floor(Math.random() * WISHES.length)]);
  }, []);

  const container = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.12 },
    },
  };

  const item = {
    hidden: { opacity: 0, y: 12, filter: "blur(4px)" },
    visible: { opacity: 1, y: 0, filter: "blur(0px)" },
  };

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="visible"
      className="relative flex flex-col md:flex-row md:items-end justify-between gap-6 pb-2"
    >
      <div className="space-y-1.5 transition-all">
        <motion.div variants={item} className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-500/10 border border-indigo-500/20">
            <Sparkles className="w-3 h-3 text-indigo-400" />
          </div>
          <span className="text-indigo-400 text-[10px] sm:text-[11px] font-black uppercase tracking-[0.2em]">
            {greeting}, {userName} ✨
          </span>
        </motion.div>

        <motion.h1 
          variants={item}
          className="text-4xl sm:text-5xl md:text-6xl font-bold text-white tracking-tighter leading-tight"
        >
          {wish}
        </motion.h1>

        <motion.div variants={item} className="flex items-center gap-4 text-slate-500 font-medium text-sm pt-2">
           <div className="flex items-center gap-1.5 font-bold text-slate-400">
             <Calendar className="w-4 h-4 text-indigo-500/60" />
             <span>{upcomingCount} upcoming</span>
           </div>
           <span className="h-4 w-px bg-slate-800" />
           <p className="flex items-center gap-1.5">
             <Clock className="w-4 h-4" />
             {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
           </p>
        </motion.div>
      </div>

      <motion.div variants={item} className="shrink-0 pb-1">
        <Link 
          href="/dashboard/calendar"
          className="group relative flex items-center gap-3 px-6 py-3.5 rounded-2xl bg-white text-black font-extrabold text-[13px] transition-all hover:bg-slate-200 active:scale-95 shadow-[0_20px_40px_-10px_rgba(255,255,255,0.15)]"
        >
          <span>Schedule New</span>
          <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </Link>
      </motion.div>
      
      {/* Subtle background glow for 'Charming' feel */}
      <div className="absolute -top-12 -left-12 w-64 h-64 bg-indigo-600/10 rounded-full blur-[100px] pointer-events-none -z-10" />
    </motion.div>
  );
};
