"use client";

import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import { 
  ArrowRight, 
  CheckCircle2, 
  Code2, 
  Cpu, 
  Globe, 
  ShieldCheck, 
  Zap,
  Menu,
  X,
  ChevronRight,
  Sparkles,
  Quote
} from "lucide-react";
import { useState, useEffect } from "react";

// ── Components ──

const Navbar = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <nav className={`fixed top-0 left-0 right-0 z-[100] transition-all duration-300 ${isScrolled ? "py-4 bg-[#0A0E27]/90 backdrop-blur-2xl border-b border-white/5" : "py-6 bg-transparent"}`}>
      <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#0066FF] to-[#6366F1] flex items-center justify-center shadow-lg shadow-[#0066FF]/20 group-hover:scale-105 transition-all">
            <Cpu className="text-white w-5 h-5" />
          </div>
          <span className="text-xl font-bold tracking-tighter text-white">GraftAI</span>
        </Link>

        {/* Desktop Links */}
        <div className="hidden md:flex items-center gap-10">
          {["Platform", "Solutions", "Developers", "Pricing"].map((link) => (
            <Link 
              key={link} 
              href={`#${link.toLowerCase()}`} 
              className="text-sm font-medium text-slate-400 hover:text-white transition-colors"
            >
              {link}
            </Link>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-4">
          <Link 
            href="/login" 
            className="px-6 py-2.5 text-sm font-semibold text-slate-300 hover:text-white transition-all focus:outline-none"
          >
            Sign In
          </Link>
          <Link 
            href="/register" 
            className="px-6 py-2 rounded-xl bg-[#0066FF] text-sm font-bold text-white shadow-lg shadow-[#0066FF]/25 hover:bg-[#0066FF]/90 transition-all active:scale-[0.98]"
          >
            Deploy
          </Link>
        </div>

        {/* Mobile Toggle */}
        <button className="md:hidden text-white p-2" onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}>
          {isMobileMenuOpen ? <X /> : <Menu />}
        </button>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 bg-[#0A0E27] backdrop-blur-3xl border-b border-white/5 py-8 px-6 flex flex-col gap-6 animate-in slide-in-from-top duration-300 z-50">
          {["Platform", "Solutions", "Developers", "Pricing"].map((link) => (
            <Link key={link} href={`#${link.toLowerCase()}`} className="text-xl font-bold text-white border-b border-white/5 pb-4" onClick={() => setIsMobileMenuOpen(false)}>
              {link}
            </Link>
          ))}
          <div className="flex flex-col gap-4 pt-4">
            <Link href="/login" className="text-center font-bold text-white py-4 border border-white/10 rounded-xl" onClick={() => setIsMobileMenuOpen(false)}>Login</Link>
            <Link href="/register" className="h-14 flex items-center justify-center rounded-xl bg-[#0066FF] font-black text-white uppercase tracking-widest shadow-lg shadow-[#0066FF]/20" onClick={() => setIsMobileMenuOpen(false)}>Establish ID</Link>
          </div>
        </div>
      )}
    </nav>
  );
};

// ── Hero ──
const Hero = () => {
  return (
    <section className="relative pt-40 pb-20 md:pt-60 md:pb-48 overflow-hidden">
      <div className="absolute inset-0 -z-10 bg-[#0A0E27]" />

      <div className="max-w-4xl mx-auto px-6 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#0066FF]/10 border border-[#0066FF]/20 text-[#0066FF] text-[10px] md:text-xs font-black uppercase tracking-widest mb-8 mx-auto">
          <Sparkles className="w-3.5 h-3.5" />
          Enterprise-Grade AI Orchestration
        </div>

        <h1 className="text-4xl sm:text-5xl md:text-7xl lg:text-[7rem] font-bold text-white leading-[1.05] tracking-tight mb-8 italic">
          Help your team <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#0066FF] to-cyan-400">achieve outcomes.</span>
        </h1>

        <div className="text-base md:text-xl text-slate-400 max-w-2xl mx-auto mb-12 leading-relaxed font-medium px-4">
          GraftAI simplifies complex scheduling and identity management. Sub-50ms execution on a global mesh network.
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6">
          <Link 
            href="/register" 
            className="w-full sm:w-auto h-14 sm:h-12 px-10 bg-[#0066FF] rounded-xl text-white font-bold flex items-center justify-center gap-3 shadow-lg shadow-[#0066FF]/20 hover:bg-[#0066FF]/90 transition-all active:scale-[0.98] group"
          >
            Start Automating
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link 
            href="/login" 
            className="w-full sm:w-auto h-14 sm:h-12 px-10 bg-white/5 border border-white/10 rounded-xl text-white font-bold flex items-center justify-center hover:bg-white/10 transition-all backdrop-blur-sm"
          >
            Enter Portal
          </Link>
        </div>
        
        <div className="mt-20 flex flex-wrap items-center justify-center gap-x-8 gap-y-4 opacity-30">
          <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-slate-400" /> <span className="text-[9px] font-bold uppercase tracking-widest text-slate-400">SOC 2</span></div>
          <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-slate-400" /> <span className="text-[9px] font-bold uppercase tracking-widest text-slate-400">AES-256</span></div>
          <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-slate-400" /> <span className="text-[9px] font-bold uppercase tracking-widest text-slate-400">FIDO2</span></div>
        </div>
      </div>
    </section>
  );
};

// ── Social Proof ──
const SocialProof = () => {
    return (
        <section className="py-20 border-y border-white/5 bg-[#1A1D2E]/30 overflow-hidden">
            <div className="max-w-7xl mx-auto px-6 relative z-10">
                <p className="text-center text-[10px] md:text-[11px] font-bold text-slate-500 uppercase tracking-[0.3em] mb-12">Trusted by institutional-grade teams</p>
                <div className="flex flex-wrap items-center justify-center gap-8 md:gap-24 opacity-30 grayscale contrast-125">
                    <span className="text-xl md:text-2xl font-black tracking-tighter text-white">STRIPE</span>
                    <span className="text-xl md:text-2xl font-black tracking-tighter text-white">VERCEL</span>
                    <span className="text-xl md:text-2xl font-black tracking-tighter text-white">LINEAR</span>
                    <span className="text-xl md:text-2xl font-black tracking-tighter text-white">SCALE_AI</span>
                    <span className="text-xl md:text-2xl font-black tracking-tighter text-white">RAYCAST</span>
                </div>
            </div>
        </section>
    );
};

// ── Testimonials ──
const Testimonials = () => {
    const reviews = [
        {
            name: "Sarah Chen",
            role: "CTO, Nexus Corp",
            text: "GraftAI transformed our engineering workflows. We reduced scheduling overhead by 70%.",
            avatar: "SC"
        },
        {
            name: "Marcus Thorne",
            role: "VP Operations, Velocity",
            text: "The institutional security markers were the selling point. FIDO2 sovereignty is exactly what we needed.",
            avatar: "MT"
        },
        {
            name: "Elena Rodriguez",
            role: "Director, Quantum Systems",
            text: "The orchestration mesh is incredibly low-latency. It feels like the system is thinking ahead.",
            avatar: "ER"
        }
    ];

    return (
        <section className="py-32 md:py-48 px-6 max-w-7xl mx-auto">
            <div className="text-center mb-24">
                <h2 className="text-3xl md:text-5xl font-bold text-white mb-6 italic">Proven by Industry Leaders</h2>
                <p className="text-slate-400 font-medium max-w-2xl mx-auto italic text-sm md:text-base">High-growth teams rely on GraftAI to maintain operational focus.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {reviews.map((review, i) => (
                    <motion.div 
                        key={i}
                        whileHover={{ y: -8 }}
                        className="p-8 md:p-10 rounded-[2rem] md:rounded-[2.5rem] bg-[#1A1D2E]/40 border border-white/5 relative overflow-hidden group"
                    >
                        <Quote className="absolute top-8 right-8 w-12 h-12 text-[#0066FF]/10" />
                        <p className="text-lg md:text-xl text-white font-medium mb-10 leading-relaxed italic">&quot;{review.text}&quot;</p>
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#0066FF] to-[#6366F1] flex items-center justify-center text-sm font-black text-white shadow-lg shadow-[#0066FF]/10">
                                {review.avatar}
                            </div>
                            <div>
                                <p className="font-bold text-white text-sm md:text-base">{review.name}</p>
                                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">{review.role}</p>
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>
        </section>
    );
};

// ── Main Layout ──
export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0A0E27] text-slate-200 selection:bg-[#0066FF]/30 selection:text-white">
      <Navbar />
      
      <main>
        <Hero />
        <SocialProof />

        {/* ── Feature Showcase ── */}
        <section id="platform" className="py-32 md:py-48 px-6 max-w-7xl mx-auto relative">
            <div className="max-w-3xl mb-24 text-center md:text-left">
                <h2 className="text-4xl md:text-6xl font-bold text-white tracking-tight mb-8 italic">The Orchestration Suite.</h2>
                <p className="text-lg md:text-xl text-slate-400 font-medium leading-relaxed">Coordinate every cell of your digital workspace with autonomous precision.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
                {[
                    { 
                        title: "Autonomous Scheduling", 
                        desc: "Let our AI matrix negotiate slots, manage buffer time, and resolve conflicts.",
                        icon: <Zap className="w-6 h-6" />,
                        accent: "text-[#0066FF]"
                    },
                    { 
                        title: "Identity Sovereignty", 
                        desc: "FIDO2 identity vaults ensure your data remains your own, zero-knowledge by design.",
                        icon: <ShieldCheck className="w-6 h-6" />,
                        accent: "text-[#6366F1]"
                    },
                    { 
                        title: "Global Mesh Network", 
                        desc: "Deploy orchestration nodes across our low-latency global mesh for sub-50ms execution.",
                        icon: <Globe className="w-6 h-6" />,
                        accent: "text-cyan-400"
                    }
                ].map((feature, i) => (
                    <div key={feature.title} className="p-8 md:p-12 rounded-[2rem] bg-[#1A1D2E]/40 border border-white/5 hover:border-white/10 transition-all hover:-translate-y-1 group">
                        <div className={`w-14 h-14 rounded-2xl bg-white/5 flex items-center justify-center mb-8 ${feature.accent} group-hover:scale-110 transition-transform`}>
                            {feature.icon}
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-4 italic">{feature.title}</h3>
                        <p className="text-slate-400 leading-relaxed font-medium text-sm md:text-base">{feature.desc}</p>
                    </div>
                ))}
            </div>
        </section>

        {/* ── Metrics Bento Grid ── */}
        <section className="py-32 md:py-48 bg-[#1A1D2E]/20 overflow-hidden">
            <div className="max-w-7xl mx-auto px-6">
                <div className="grid grid-cols-1 md:grid-cols-4 md:grid-rows-2 gap-4 md:gap-6">
                    <div className="md:col-span-2 md:row-span-2 p-10 md:p-12 h-[450px] md:h-auto rounded-[2.5rem] bg-gradient-to-br from-[#0066FF] to-[#6366F1] flex flex-col justify-end relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-12 opacity-10 group-hover:scale-110 transition-transform"><Cpu className="w-48 md:w-64 h-48 md:h-64" /></div>
                        <h3 className="text-[9px] md:text-[10px] font-black uppercase tracking-[0.4em] text-white/60 mb-4">Core Performance</h3>
                        <p className="text-6xl md:text-9xl font-black text-white leading-none tracking-tighter italic">42ms</p>
                        <p className="text-base md:text-lg font-bold text-white/80 mt-6 italic">Global Orchestration Latency</p>
                    </div>
                    
                    <div className="md:col-span-2 p-8 md:p-10 rounded-[2rem] md:rounded-[2.5rem] bg-[#1A1D2E]/50 border border-white/5 backdrop-blur-3xl flex items-center justify-between group overflow-hidden">
                        <div>
                            <h3 className="text-[9px] md:text-[10px] font-black uppercase tracking-[0.4em] text-slate-500 mb-2">Identity Scale</h3>
                            <p className="text-4xl md:text-5xl font-bold text-white tracking-tight italic">99.9%</p>
                            <p className="text-xs md:text-sm font-medium text-slate-400 mt-2">Encryption Success Rate</p>
                        </div>
                        <ShieldCheck className="w-16 md:w-20 h-16 md:h-20 text-[#6366F1] opacity-20 group-hover:scale-110 transition-transform" />
                    </div>

                    <div className="p-8 md:p-10 rounded-[2rem] md:rounded-[2.5rem] bg-[#1A1D2E]/50 border border-white/5 backdrop-blur-3xl flex flex-col justify-center">
                        <h3 className="text-[9px] md:text-[10px] font-black uppercase tracking-[0.4em] text-slate-500 mb-2">Deployments</h3>
                        <p className="text-4xl md:text-5xl font-bold text-white tracking-tight italic">2.4k</p>
                        <p className="text-xs md:text-sm font-medium text-slate-400 mt-2">Daily Pipelines Cleaned</p>
                    </div>

                    <div className="p-8 md:p-10 rounded-[2rem] md:rounded-[2.5rem] bg-[#1A1D2E]/50 border border-white/5 backdrop-blur-3xl flex flex-col justify-center">
                        <h3 className="text-[9px] md:text-[10px] font-black uppercase tracking-[0.4em] text-slate-500 mb-2">Uptime</h3>
                        <p className="text-4xl md:text-5xl font-bold text-emerald-400 tracking-tight italic">∞</p>
                        <p className="text-xs md:text-sm font-medium text-slate-400 mt-2">Zero-Downtime Design</p>
                    </div>
                </div>
            </div>
        </section>

        <Testimonials />

        {/* ── Final CTA ── */}
        <section className="py-32 md:py-60 px-6 max-w-7xl mx-auto text-center">
            <div className="p-10 md:p-32 rounded-[2.5rem] md:rounded-[3.5rem] bg-gradient-to-br from-[#1A1D2E] to-[#0A0E27] border border-white/10 relative overflow-hidden group">
                <div className="absolute inset-0 bg-[#0066FF]/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700 blur-[100px] -z-10" />
                
                <h2 className="text-3xl md:text-7xl font-bold text-white tracking-tighter mb-12 italic">
                   Institutional quality. <br />
                   <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#0066FF] via-[#6366F1] to-cyan-400">Startup speed.</span>
                </h2>
                
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6">
                    <Link 
                        href="/register" 
                        className="w-full sm:w-auto h-14 md:h-12 px-10 bg-white text-[#0A0E27] rounded-xl font-black text-xs md:text-base shadow-xl hover:bg-slate-100 transition-all active:scale-[0.98] uppercase tracking-widest"
                    >
                        Deploy the Protocol
                    </Link>
                    <Link 
                        href="/login" 
                        className="w-full sm:w-auto h-14 md:h-12 px-10 bg-white/5 border border-white/10 rounded-xl text-white font-black text-xs md:text-base hover:bg-white/10 transition-all uppercase tracking-widest"
                    >
                        Enter Terminal
                    </Link>
                </div>
            </div>
        </section>

      </main>

    </div>
  );
}
