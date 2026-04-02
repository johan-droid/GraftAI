"use client";

import Link from "next/link";
import { motion, Variants } from "framer-motion";
import { 
  Bot, 
  ShieldCheck, 
  Sparkles, 
  Zap,
  Lock,
  ArrowRight,
  Globe,
  Plus
} from "lucide-react";
import { SpotlightCard } from "@/components/spotlight-card";

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { type: "spring", damping: 25, stiffness: 200 } }
};

export default function Home() {
  return (
    <div className="relative min-h-screen bg-background text-foreground selection:bg-primary/30 overflow-x-hidden app-shell">
      
      {/* ── Background Layering (Inspired by React Bits) ── */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="pixel-grid opacity-20" />
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-primary/10 rounded-full blur-[160px] opacity-40 animate-pulse" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-accent/5 rounded-full blur-[140px] opacity-30" />
      </div>

      <main className="relative z-10 pt-32 sm:pt-40 pb-20 px-4 sm:px-6">
        
        {/* ── Hero Section (Bento Grid Style) ── */}
        <div className="max-w-7xl mx-auto">
          <motion.div 
            initial="hidden" 
            animate="visible" 
            variants={containerVariants}
            className="grid grid-cols-1 md:grid-cols-12 gap-4 auto-rows-min"
          >
            {/* Main Headline Block */}
            <motion.div variants={itemVariants} className="md:col-span-8 flex flex-col justify-center p-8 sm:p-12 md:p-16 rounded-[2.5rem] bg-glass backdrop-blur-xl border border-card-border overflow-hidden relative">
              <div className="absolute top-0 right-0 w-32 h-32 bg-primary/20 blur-[100px] -mr-16 -mt-16" />
              
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary border border-primary/20 mb-6 text-[10px] font-black uppercase tracking-[0.2em]">
                <Sparkles className="w-3 h-3" />
                Sovereign Engine
              </div>
              
              <h1 className="text-4xl sm:text-6xl md:text-7xl font-black text-white leading-[0.95] tracking-tighter mb-6">
                ORCHESTRATE <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-accent to-primary animate-gradient">EVERY MOMENT</span>
              </h1>
              
              <p className="text-base sm:text-lg text-slate-400 max-w-xl mb-10 font-medium leading-relaxed">
                GraftAI is an autonomous calendar layer that keeps your schedule in sync with
                intelligent memory and conflict-free orchestration.
              </p>

              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  href="/login"
                  className="px-8 py-4 bg-primary rounded-2xl text-sm font-black text-white hover:scale-105 active:scale-95 transition-all text-center uppercase tracking-tight flex items-center justify-center gap-2"
                >
                  Start Syncing
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/#features"
                  className="px-8 py-4 bg-slate-900 border border-card-border rounded-2xl text-sm font-black text-slate-200 hover:bg-slate-800 transition-all text-center uppercase tracking-tight"
                >
                  Explore Tech
                </Link>
              </div>
            </motion.div>

            {/* AI Assistant Stat Block */}
            <motion.div variants={itemVariants} className="md:col-span-4 rounded-[2.5rem] bg-gradient-to-br from-primary/20 to-accent/20 border border-primary/20 p-8 flex flex-col justify-between relative group">
              <div className="flex items-center justify-between">
                <div className="w-12 h-12 rounded-2xl bg-white text-black flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                  <Bot className="w-6 h-6" />
                </div>
                <div className="text-[10px] font-black uppercase tracking-widest text-primary">Live Ready</div>
              </div>
              <div>
                <div className="text-4xl font-black text-white mb-2 leading-none tracking-tighter">4.2k</div>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Active Assistants</p>
              </div>
            </motion.div>

            {/* Feature Bento Grid (Desktop 3cols, Mobile Stacks) */}
            <motion.div variants={itemVariants} className="md:col-span-4 p-8 rounded-[2.5rem] bg-slate-900/50 border border-card-border flex flex-col gap-6">
              <Zap className="text-primary w-8 h-8" />
              <div>
                <h3 className="font-black text-lg text-white mb-2 uppercase tracking-tight">Instant Sync</h3>
                <p className="text-sm text-slate-400 leading-snug">Zero-latency reactive memory for your entire schedule.</p>
              </div>
            </motion.div>

            <motion.div variants={itemVariants} className="md:col-span-5 p-8 rounded-[2.5rem] bg-slate-900/50 border border-card-border flex flex-col gap-6 relative overflow-hidden group">
              <Plus className="absolute top-4 right-4 text-slate-700 w-8 h-8 group-hover:rotate-90 transition-transform" />
              <Lock className="text-accent w-8 h-8" />
              <div>
                <h3 className="font-black text-lg text-white mb-2 uppercase tracking-tight">Enterprise Identity</h3>
                <p className="text-sm text-slate-400 leading-snug">Passwordless FIDO2 and SSO protection for every user account.</p>
              </div>
            </motion.div>

            <motion.div variants={itemVariants} className="md:col-span-3 p-8 rounded-[2.5rem] bg-gradient-to-br from-slate-900 to-black border border-card-border flex flex-col justify-center items-center text-center gap-4">
              <div className="w-16 h-16 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
              <div className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Processing v2.0</div>
            </motion.div>
          </motion.div>
        </div>

        {/* ── Features Spotlight Section ── */}
        <section id="features" className="max-w-7xl mx-auto mt-32">
          <div className="flex flex-col md:flex-row md:items-end justify-between px-4 mb-20 gap-8">
            <div className="max-w-2xl text-left">
              <div className="text-primary font-black text-xs uppercase tracking-[0.4em] mb-4">Features</div>
              <h2 className="text-4xl md:text-6xl font-black text-white mb-6 leading-none tracking-tighter">THE SOVEREIGN STACK.</h2>
              <p className="text-slate-400 text-lg md:text-xl font-medium leading-relaxed">
                Modular intelligence designed to give you back 40% of your work week.
              </p>
            </div>
            <Link href="/dashboard" className="group flex items-center gap-4 py-4 px-8 rounded-2xl bg-slate-900 border border-card-border hover:bg-slate-800 transition-all">
              <span className="font-black text-xs uppercase tracking-widest">Dashboard</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-2 transition-transform" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <SpotlightCard className="h-full flex flex-col gap-6" glowColor="rgba(79, 70, 229, 0.1)">
              <div className="w-14 h-14 rounded-2xl bg-primary/20 flex items-center justify-center text-primary shadow-lg shadow-primary/5">
                <Bot className="w-7 h-7" />
              </div>
              <div>
                <h3 className="text-2xl font-black text-white mb-3 uppercase tracking-tighter italic">Autonomous Copilot</h3>
                <p className="text-slate-400 leading-relaxed text-sm">Advanced LLM orchestration that handles scheduling negotiations flawlessly.</p>
              </div>
            </SpotlightCard>

            <SpotlightCard className="h-full flex flex-col gap-6" glowColor="rgba(168, 85, 247, 0.1)">
              <div className="w-14 h-14 rounded-2xl bg-accent/20 flex items-center justify-center text-accent shadow-lg shadow-accent/5">
                <Globe className="w-7 h-7" />
              </div>
              <div>
                <h3 className="text-2xl font-black text-white mb-3 uppercase tracking-tighter italic">Reactive Memory</h3>
                <p className="text-slate-400 leading-relaxed text-sm">Instant vector synchronization across all connected calendar providers.</p>
              </div>
            </SpotlightCard>

            <SpotlightCard className="h-full flex flex-col gap-6" glowColor="rgba(255, 255, 255, 0.1)">
              <div className="w-14 h-14 rounded-2xl bg-slate-800 flex items-center justify-center text-white">
                <ShieldCheck className="w-7 h-7" />
              </div>
              <div>
                <h3 className="text-2xl font-black text-white mb-3 uppercase tracking-tighter italic">Zero Privacy</h3>
                <p className="text-slate-400 leading-relaxed text-sm">Your data stays yours with granular, AI-enforced local controls.</p>
              </div>
            </SpotlightCard>
          </div>
        </section>

        {/* ── Footer / Bottom CTA ── */}
        <section className="max-w-7xl mx-auto mt-40">
           <div className="relative group rounded-[3rem] p-12 sm:p-20 bg-slate-900 border border-card-border overflow-hidden text-center flex flex-col items-center">
              <div className="absolute inset-0 pixel-grid opacity-10 pointer-events-none" />
              <div className="relative z-10">
                <h2 className="text-5xl md:text-8xl font-black text-white mb-10 leading-[0.85] tracking-tighter italic">CLAIM THE <br /> AUTONOMY.</h2>
                <Link href="/login" className="inline-flex items-center gap-6 px-12 py-6 bg-white text-black rounded-3xl font-black text-lg hover:scale-110 active:scale-95 transition-all uppercase tracking-tighter italic">
                  Launch GraftAI <Plus className="w-6 h-6 " />
                </Link>
              </div>
           </div>
        </section>

      </main>

      <footer className="mt-20 border-t border-card-border py-20 px-6">
        <div className="max-w-7xl mx-auto flex flex-col items-center text-center gap-10">
          <div className="flex items-center gap-3">
             <div className="w-6 h-6 bg-slate-800 rounded-full" />
             <span className="font-black text-[10px] uppercase tracking-[0.5em] text-slate-500">Graft Protocol 2026/PROD</span>
          </div>
          <div className="flex flex-wrap justify-center gap-x-12 gap-y-4 text-[10px] sm:text-xs font-black uppercase tracking-[0.2em] text-slate-400">
            <Link href="/" className="hover:text-primary transition-colors">Documentation</Link>
            <Link href="/" className="hover:text-primary transition-colors">Security</Link>
            <Link href="/" className="hover:text-primary transition-colors">Privacy</Link>
            <Link href="/" className="hover:text-primary transition-colors">Status</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
