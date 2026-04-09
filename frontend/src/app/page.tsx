"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Zap, Bot, Sparkles, Globe, Calendar, ArrowRight, 
  CheckCircle2, Clock, Star, Menu, X, ChevronDown
} from "lucide-react";

// --- Data Objects ---
const LOGOS = ["Stripe", "Linear", "Vercel", "Notion", "Figma", "Loom"];

const FEATURES = [
  {
    icon: <Bot className="w-6 h-6" />,
    title: "AI Scheduling Intelligence",
    desc: "GraftAI understands your intent, not just your availability. Hand off the back-and-forth entirely.",
    accent: "text-violet-400",
    bg: "bg-violet-500/5",
    border: "border-violet-500/20"
  },
  {
    icon: <Globe className="w-6 h-6" />,
    title: "Universal Ecosystem Sync",
    desc: "Seamless bidirectional sync with Google and Microsoft. Connect your entire world in 10 seconds.",
    accent: "text-blue-400",
    bg: "bg-blue-500/5",
    border: "border-blue-500/20"
  },
  {
    icon: <Calendar className="w-6 h-6" />,
    title: "Sovereign Time Control",
    desc: "Monolithic, high-performance architecture ensures zero lag and absolute privacy for your schedule.",
    accent: "text-emerald-400",
    bg: "bg-emerald-500/5",
    border: "border-emerald-500/20"
  }
];

// --- Sub-components ---
const Nav = ({ scrolled, setMobileOpen }: any) => (
  <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
    scrolled ? "bg-[#070711]/80 backdrop-blur-xl border-b border-white/[0.05]" : ""
  }`}>
    <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
      <Link href="/" className="flex items-center gap-2 group">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/25">
          <Zap className="w-5 h-5 text-white fill-white" />
        </div>
        <span className="text-lg font-black tracking-tight text-white uppercase">GraftAI</span>
      </Link>

      <div className="hidden md:flex items-center gap-8">
        <Link href="#features" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Features</Link>
        <Link href="#pricing" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Pricing</Link>
        <Link href="/login" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Sign in</Link>
        <Link href="/register" className="group flex items-center gap-2 rounded-xl bg-white px-5 py-2.5 text-sm font-bold text-black hover:bg-slate-200 transition-all active:scale-95">
          Get Started
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
        </Link>
      </div>

      <button onClick={() => setMobileOpen(true)} className="md:hidden flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-white">
        <Menu className="h-5 w-5" />
      </button>
    </nav>
  </header>
);

const FeatureCard = ({ f, index }: any) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    transition={{ delay: index * 0.1 }}
    whileHover={{ y: -5 }}
    className={`p-8 rounded-3xl border ${f.border} ${f.bg} backdrop-blur-sm group transition-all`}
  >
    <div className={`mb-6 flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 border border-white/5 ${f.accent}`}>
      {f.icon}
    </div>
    <h3 className="text-xl font-bold text-white mb-3">{f.title}</h3>
    <p className="text-slate-400 leading-relaxed text-sm">{f.desc}</p>
  </motion.div>
);

export default function Home() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-[#070711] text-slate-200 selection:bg-indigo-500/30 font-sans">
      
      {/* Background Layers */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[20%] w-[600px] h-[600px] bg-indigo-600/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[10%] right-[10%] w-[400px] h-[400px] bg-violet-600/5 blur-[100px] rounded-full" />
        <div className="absolute inset-0 home-grid-layer opacity-[0.02]" />
      </div>

      <Nav scrolled={scrolled} setMobileOpen={setMobileOpen} />

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-6 overflow-hidden">
        <div className="mx-auto max-w-5xl text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 text-xs font-bold text-indigo-300 mb-8"
          >
            <Sparkles className="w-3.5 h-3.5" />
            THE MONOLITHIC EVOLUTION
          </motion.div>
          
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-5xl md:text-7xl lg:text-8xl font-black text-white leading-[0.95] tracking-tighter mb-8"
          >
            MASTER YOUR <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-white to-white/40 italic">SOVEREIGN TIME.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mx-auto max-w-2xl text-lg md:text-xl text-slate-400 leading-relaxed mb-10"
          >
            GraftAI is the high-performance scheduling brain that unifies your digital world. 
            Google and Microsoft sync, paired with advanced AI coordination.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
          >
            <Link href="/register" className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-white text-black font-black text-sm hover:bg-slate-200 transition-all shadow-xl shadow-white/5 active:scale-95">
              Launch Your Engine
            </Link>
            <Link href="/login" className="w-full sm:w-auto px-8 py-4 rounded-2xl border border-white/10 bg-white/5 text-white font-bold text-sm hover:bg-white/10 transition-all active:scale-95">
              Sign In
            </Link>
          </motion.div>

          {/* Social Proof */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="flex flex-col items-center gap-6"
          >
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-600">TRUSTED BY TEAMS FROM</p>
            <div className="flex flex-wrap justify-center gap-8 md:gap-16">
              {LOGOS.map(logo => (
                <span key={logo} className="text-sm font-black text-slate-700 tracking-tighter grayscale opacity-50">{logo}</span>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-24 px-6 relative">
        <div className="mx-auto max-w-6xl">
          <div className="mb-16">
            <h2 className="text-3xl md:text-5xl font-black text-white mb-4">Stripped for performance.</h2>
            <p className="text-slate-400 max-w-xl text-lg">No bloat. No noise. Just the fastest scheduling experience ever built.</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6">
            {FEATURES.map((f, i) => (
              <FeatureCard key={i} f={f} index={i} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 px-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="mx-auto max-w-5xl rounded-[40px] border border-indigo-500/20 bg-gradient-to-br from-indigo-500/10 to-violet-500/10 p-12 md:p-24 text-center relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 blur-[80px] rounded-full" />
          <div className="relative z-10">
            <h2 className="text-4xl md:text-6xl font-black text-white mb-6">Own your day again.</h2>
            <p className="text-slate-400 text-lg mb-10 max-w-md mx-auto">Free to start. Connect your calendars in seconds. No credit card required.</p>
            <Link href="/register" className="inline-flex items-center gap-3 px-10 py-5 rounded-2xl bg-white text-black font-black hover:bg-slate-200 transition-all shadow-2xl active:scale-95">
              Create Free Account
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-white/[0.05] text-center">
        <div className="mx-auto max-w-6xl px-6">
          <p className="text-xs text-slate-600 font-bold tracking-widest uppercase">© 2026 GraftAI · The Presentation Version</p>
        </div>
      </footer>

      {/* Mobile Nav Overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] bg-black/90 backdrop-blur-2xl flex flex-col items-center justify-center p-8 text-center"
          >
            <button onClick={() => setMobileOpen(false)} className="absolute top-8 right-8 text-white"><X className="w-8 h-8" /></button>
            <div className="flex flex-col gap-10">
               <Link onClick={() => setMobileOpen(false)} href="/login" className="text-4xl font-black text-white transition-opacity hover:opacity-70">Sign In</Link>
               <Link onClick={() => setMobileOpen(false)} href="/register" className="text-4xl font-black text-indigo-400 transition-opacity hover:opacity-70">Register</Link>
               <Link onClick={() => setMobileOpen(false)} href="#features" className="text-4xl font-black text-white transition-opacity hover:opacity-70">Features</Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
