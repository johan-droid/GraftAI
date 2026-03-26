"use client";

import Link from "next/link";
import { useState } from "react";
import { motion, AnimatePresence, Variants } from "framer-motion";
import { 
  Calendar, 
  Bot, 
  ChevronRight, 
  ShieldCheck, 
  Sparkles, 
  Cpu, 
  Globe, 
  Layers, 
  Zap,
  Lock,
  ArrowRight
} from "lucide-react";

const FEATURE_CARDS = [
  {
    id: "ai",
    icon: <Bot className="w-6 h-6" />,
    title: "Autonomous Copilot",
    desc: "Advanced LLM orchestration that handles scheduling negotiations flawlessly.",
    color: "from-violet-600 to-indigo-600",
    glow: "rgba(124, 58, 237, 0.3)"
  },
  {
    id: "sync",
    icon: <Zap className="w-6 h-6" />,
    title: "Instant Vector Sync",
    desc: "Reactive AI memory that updates as soon as your calendar changes.",
    color: "from-blue-600 to-cyan-600",
    glow: "rgba(37, 99, 235, 0.3)"
  },
  {
    id: "auth",
    icon: <Lock className="w-6 h-6" />,
    title: "Sovereign Auth",
    desc: "Passwordless FIDO2 and SSO for enterprise-grade identity protection.",
    color: "from-emerald-600 to-teal-600",
    glow: "rgba(5, 150, 105, 0.3)"
  },
  {
    id: "plugins",
    icon: <Layers className="w-6 h-6" />,
    title: "Infinite Plugins",
    desc: "Extend your AI's capabilities with a vast ecosystem of third-party tools.",
    color: "from-amber-500 to-orange-600",
    glow: "rgba(245, 158, 11, 0.3)"
  },
  {
    id: "proactive",
    icon: <Sparkles className="w-6 h-6" />,
    title: "Proactive Flow",
    desc: "The assistant that predicts your next meeting slot before you ask.",
    color: "from-rose-500 to-pink-600",
    glow: "rgba(244, 63, 94, 0.3)"
  },
  {
    id: "privacy",
    icon: <ShieldCheck className="w-6 h-6" />,
    title: "Zero-Knowledge",
    desc: "Your data stays yours with granular, AI-enforced privacy controls.",
    color: "from-slate-600 to-slate-800",
    glow: "rgba(71, 85, 105, 0.3)"
  }
];

export default function Home() {
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0, transition: { type: "spring", damping: 20, stiffness: 100 } }
  };

  return (
    <div className="min-h-screen bg-[#020617] text-slate-200 selection:bg-primary/30 overflow-x-hidden">
      
      {/* ── Background Layering ── */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-primary/20 rounded-full blur-[120px] opacity-50" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-fuchsia-600/10 rounded-full blur-[120px] opacity-30" />
        <div className="absolute inset-0 bg-[url('/noise.svg')] opacity-20 brightness-50 contrast-150" />
      </div>

      <nav className="relative z-50 flex items-center justify-between px-6 py-6 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-fuchsia-600 flex items-center justify-center shadow-md shadow-primary/15">
            <Cpu className="text-white w-5 h-5" />
          </div>
          <span className="text-lg font-semibold tracking-tight text-white">GraftAI</span>
        </div>
        <div className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-400">
          <Link href="#features" className="hover:text-white transition-colors">Technology</Link>
          <Link href="/dashboard/plugins" className="hover:text-white transition-colors">Ecosystem</Link>
          <Link href="/login" className="px-4 py-2 rounded-lg bg-slate-800/50 border border-slate-700 hover:bg-slate-700 transition-all text-white text-sm">Login</Link>
        </div>
        <Link href="/login" className="md:hidden px-3 py-2 rounded-lg bg-primary text-white text-sm font-semibold">Start</Link>
      </nav>

      <main className="relative z-10">
        {/* ── Hero Section ── */}
        <section className="pt-20 pb-32 px-6 max-w-7xl mx-auto text-center">
          <motion.div 
            initial="hidden" 
            animate="visible" 
            variants={containerVariants}
            className="flex flex-col items-center"
          >
            <motion.div variants={itemVariants} className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary border border-primary/20 mb-8 text-xs font-bold uppercase tracking-widest">
              <Sparkles className="w-4 h-4" />
              Sovereign Scheduling Engine
            </motion.div>

            <motion.h1 variants={itemVariants} className="text-4xl md:text-6xl font-extrabold text-white leading-[1.02] tracking-tight mb-6 drop-shadow-lg">
              ORCHESTRATE <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-fuchsia-400 to-primary bg-[length:200%_auto] animate-gradient">EVERY MOMENT</span>
            </motion.h1>

            <motion.p variants={itemVariants} className="text-base md:text-lg text-slate-400 max-w-3xl mb-8 leading-relaxed">
              GraftAI is an autonomous calendar layer that keeps your schedule in sync with
              intelligent memory and conflict-free orchestration. Fewer meetings, more focus.
            </motion.p>

            <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
              <Link
                href="/login"
                className="group relative px-6 py-3 bg-primary rounded-xl text-sm md:text-base font-semibold text-white shadow-md hover:scale-102 transition-all overflow-hidden flex items-center justify-center gap-2"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/15 to-white/0 -translate-x-full group-hover:translate-x-full transition-transform duration-900" />
                Deploy AI Copilot
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                href="/dashboard"
                className="px-6 py-3 bg-slate-900 border border-slate-800 rounded-xl text-sm md:text-base font-semibold text-slate-300 hover:bg-slate-800 hover:text-white transition-all flex items-center justify-center"
              >
                Open Dashboard
              </Link>
            </motion.div>
          </motion.div>
        </section>

        {/* ── Hovering Card System ── */}
        <section id="features" className="py-24 px-6 max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-6">
            <div className="max-w-xl">
              <h2 className="text-3xl md:text-5xl font-bold text-white mb-4 tracking-tight">The Stack of Sovereignty</h2>
              <p className="text-slate-400 text-lg">Layered intelligence designed to give you back 40% of your work week.</p>
            </div>
            <Link href="/dashboard/plugins" className="flex items-center gap-2 text-primary font-bold hover:underline">
              Explore Plugin Marketplace <ChevronRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURE_CARDS.map((feature) => (
              <motion.div
                key={feature.id}
                onMouseEnter={() => setHoveredCard(feature.id)}
                onMouseLeave={() => setHoveredCard(null)}
                whileHover={{ y: -6 }}
                className="relative group h-full"
              >
                {/* Layered Glow Effect */}
                <div 
                  className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-2xl z-0"
                  style={{ backgroundColor: feature.glow }}
                />

                <div className="relative z-10 h-full bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-2xl p-6 transition-all group-hover:border-slate-700/50 group-hover:bg-slate-900/80 flex flex-col items-start gap-4">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center text-white shadow-md`}>
                    {feature.icon}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-primary transition-colors">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-slate-400 leading-snug">
                      {feature.desc}
                    </p>
                  </div>
                  
                  <div className="mt-auto pt-4 w-full flex items-center justify-between opacity-100 transition-opacity">
                    <span className="text-xs font-bold uppercase text-slate-500">Feature Ready</span>
                    <Link href={`/features/${feature.id}`} className="text-sm text-primary font-semibold hover:underline flex items-center gap-2">
                      Learn more <ChevronRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ── CTA / Layering Demo ── */}
        <section className="py-24 px-6">
          <div className="max-w-6xl mx-auto rounded-[3rem] bg-gradient-to-br from-primary/20 via-slate-900 to-fuchsia-900/10 border border-primary/20 p-8 md:p-20 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/20 rounded-full blur-[80px] -mr-32 -mt-32" />
            
            <div className="relative z-10 flex flex-col md:flex-row items-center gap-12">
              <div className="flex-1 text-center md:text-left">
                <h2 className="text-4xl md:text-6xl font-black text-white mb-6 leading-none">JOIN THE <br /> AUTONOMY.</h2>
                <p className="text-slate-400 text-lg mb-8 max-w-md mx-auto md:mx-0 font-medium">
                  Thousands of high-performer teams use GraftAI to reclaim their focus. Start your sovereign schedule today.
                </p>
                <Link href="/login" className="inline-flex items-center gap-2 px-10 py-5 bg-white text-black rounded-2xl font-black hover:bg-slate-200 transition-all uppercase tracking-tighter">
                  Claim Your Handle <ArrowRight className="w-5 h-5" />
                </Link>
              </div>
              
              <div className="relative w-full max-w-sm">
                {/* Floating layering icons */}
                <motion.div 
                  animate={{ y: [-10, 10, -10] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                  className="bg-slate-900 border border-slate-800 p-6 rounded-3xl shadow-2xl relative z-20"
                >
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center"><Bot className="text-primary w-5 h-5"/></div>
                    <div>
                      <div className="h-2 w-24 bg-slate-700 rounded-full mb-2" />
                      <div className="h-2 w-16 bg-slate-800 rounded-full" />
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="h-2 w-full bg-slate-800 rounded-full" />
                    <div className="h-2 w-3/4 bg-slate-800 rounded-full" />
                  </div>
                </motion.div>
                
                <motion.div 
                  animate={{ y: [10, -10, 10] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                  className="absolute -top-10 -right-10 bg-fuchsia-600/20 border border-fuchsia-500/30 p-4 rounded-2xl backdrop-blur-md z-30 shadow-fuchsia-500/20 shadow-xl"
                >
                  <Globe className="text-white w-6 h-6" />
                </motion.div>

                <motion.div 
                   initial={{ opacity: 0.5 }}
                   className="absolute -bottom-6 -left-6 w-32 h-32 bg-primary/20 rounded-full blur-3xl z-10" 
                />
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="mt-20 border-t border-slate-900 py-16 px-6">
        <div className="max-w-7xl mx-auto flex flex-col items-center gap-12 text-center text-slate-500">
          <div className="flex flex-col items-center gap-2">
            <Cpu className="w-8 h-8 text-slate-700"/>
            <span className="font-bold text-white tracking-widest text-sm uppercase">GraftAI Sovereign</span>
          </div>
          <p className="max-w-lg text-sm font-medium leading-relaxed">
            The next generation of autonomous scheduling and AI orchestration. Built for those who 
            value time more than anything else. Developed by the Graft Protocol Team.
          </p>
          <div className="flex gap-8 text-xs font-black uppercase tracking-widest">
            <Link href="/privacy" className="hover:text-white transition-colors">Privacy</Link>
            <Link href="/terms" className="hover:text-white transition-colors">Security</Link>
            <Link href="https://github.com/johan-droid" className="hover:text-white transition-colors">Repo</Link>
          </div>
          <p className="text-[10px] font-bold text-slate-800">© 2026 GRAFT AI PROTOCOL. ALL RIGHTS RESERVED.</p>
        </div>
      </footer>
    </div>
  );
}
