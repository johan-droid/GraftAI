"use client";

import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, ShieldCheck, Sparkles, Zap, Lock, Globe, Cloud, FileText, Scale, Mail, GraduationCap, ArrowRight, BrainCircuit, Fingerprint, Database, Server, Cpu, Layers, Code2, Terminal, Activity, Loader2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { cn } from "@/lib/utils";

const STRATEGY_STEPS = [
  { 
    title: "Data Sovereignty", 
    description: "Your schedule is encrypted and federated. No single point of failure. You own your time vectors.",
    icon: ShieldCheck,
    color: "text-indigo-400"
  },
  { 
    title: "AI Synthesis", 
    description: "Our neural engine parses your workflows to find optimal execution paths across all timezones.",
    icon: BrainCircuit,
    color: "text-purple-400"
  },
  { 
    title: "Autonomous Execution", 
    description: "Meetings book themselves. Conflicts resolve in the background. You just show up.", 
    icon: Zap,
    color: "text-amber-400"
  }
];

const ARCHITECTURE_NODES = [
  {
    layer: "Client & Edge",
    tech: "Next.js 14 / Framer Motion",
    desc: "React Server Components handle dynamic SEO and layout hydration at the edge, while Framer Motion drives fluid 'Galaxy HUD' micro-interactions.",
    icon: Layers,
    color: "emerald"
  },
  {
    layer: "API Gateway & Engine",
    tech: "FastAPI / Python 3.12",
    desc: "High-performance async ASGI server. Routes cryptographic tokens, validates Pydantic models, and processes AI scheduling requests.",
    icon: Terminal,
    color: "blue"
  },
  {
    layer: "Memory & Cache",
    tech: "Redis / Upstash",
    desc: "Provides sub-millisecond response times for session handling, rate limiting, and temporary AI context retention.",
    icon: Database,
    color: "fuchsia"
  },
  {
    layer: "Persistent Ledger",
    tech: "PostgreSQL / SQLAlchemy",
    desc: "Relational database utilizing advanced connection pooling. Guarantees ACID compliance for cross-instance chronological data.",
    icon: Server,
    color: "orange"
  }
];

const features = [
  { icon: <Fingerprint className="w-6 h-6" />, title: "Federated Identity", description: "Zero-trust authentication with SSO and Biometric support." },
  { icon: <Database className="w-6 h-6" />, title: "Vector Memory", description: "Your AI remembers your preferences without leaking your data." },
  { icon: <Globe className="w-6 h-6" />, title: "Global Sync", description: "Atomic updates across Google, Outlook, and private nodes." },
];

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<"unknown" | "live" | "sleeping" | "waking">("unknown");
  const [showToaster, setShowToaster] = useState(false);

  const checkBackend = useCallback(async () => {
    // If it was sleeping, set it to waking on the next check attempt
    if (backendStatus === "sleeping") {
      setBackendStatus("waking");
    }
    
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "";
      const resp = await fetch(`${baseUrl}/health`.replace(/\/+/g, '/').replace(':/', '://'), { cache: "no-store", signal: AbortSignal.timeout(5000) });
      if (resp.ok) setBackendStatus("live");
      else setBackendStatus("sleeping");
    } catch {
      setBackendStatus("sleeping");
    }
  }, [backendStatus]);

  useEffect(() => {
    checkBackend();
    const timer = setInterval(checkBackend, 30000);
    
    // Show toaster a bit after load
    const toasterDelay = setTimeout(() => setShowToaster(true), 1500);
    
    return () => {
      clearInterval(timer);
      clearTimeout(toasterDelay);
    };
  }, [checkBackend]);

  return (
    <div className="min-h-screen bg-[#020617] text-slate-100 selection:bg-primary/30 selection:text-white relative overflow-hidden">
      {/* Dynamic Background */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] right-[-10%] w-[70%] h-[70%] bg-indigo-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[60%] h-[60%] bg-fuchsia-600/10 rounded-full blur-[140px]" />
      </div>

      <main className="relative z-10 max-w-7xl mx-auto px-6 pt-24 pb-16 sm:pt-32 lg:px-8">
        
        {/* Floating Backend Toaster */}
        <AnimatePresence>
          {showToaster && (
            <motion.div
              initial={{ opacity: 0, y: 50, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 20, scale: 0.9 }}
              transition={{ type: "spring", stiffness: 300, damping: 25 }}
              className="fixed bottom-6 right-6 z-50 flex items-center gap-3 p-3 lg:p-4 rounded-2xl bg-slate-900/80 border border-white/10 backdrop-blur-2xl shadow-[0_20px_40px_rgba(0,0,0,0.5)] max-w-[300px] lg:max-w-xs"
            >
              <div className="shrink-0 flex items-center justify-center">
                 {backendStatus === "live" && <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.8)] animate-pulse" />}
                 {backendStatus === "waking" && <div className="w-3 h-3 rounded-full bg-amber-500 shadow-[0_0_12px_rgba(245,158,11,0.8)] animate-pulse" />}
                 {backendStatus === "sleeping" && <div className="w-3 h-3 rounded-full bg-slate-600" />}
                 {backendStatus === "unknown" && <Loader2 className="w-4 h-4 text-slate-400 animate-spin" />}
              </div>
              <div className="flex-1">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 leading-none mb-1">
                  Engine Status
                </p>
                <p className="text-xs font-medium text-white leading-tight">
                  {backendStatus === "live" && "Connection established. Node operations nominal."}
                  {backendStatus === "waking" && "Initiating cold start on backend cluster..."}
                  {backendStatus === "sleeping" && "Backend asleep. Requesting wake signal."}
                  {backendStatus === "unknown" && "Pinging telemetry gateway..."}
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Hero Section */}
        <div className="text-center max-w-4xl mx-auto pt-8">
          <motion.h1 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-5xl md:text-7xl font-black tracking-tight text-white mb-8 bg-gradient-to-b from-white via-white to-slate-500 bg-clip-text text-transparent leading-tight"
          >
            Autonomous Scheduling for <span className="text-primary tracking-tighter">Sovereign Focus</span>
          </motion.h1>
          
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-lg md:text-xl text-slate-400 mb-12 max-w-2xl mx-auto leading-relaxed"
          >
            GraftAI is a federated intelligence layer that handles your scheduling logistics automatically. Secure, private, and powered by vector memory.
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link href="/login" className="w-full sm:w-auto px-8 py-4 bg-primary text-white rounded-2xl font-bold text-base shadow-[0_10px_30px_rgba(79,70,229,0.4)] hover:scale-105 active:scale-95 transition-all flex items-center justify-center gap-2">
              Begin Decoupling <ArrowRight className="w-5 h-5" />
            </Link>
            <Link href="#architecture" className="w-full sm:w-auto px-8 py-4 bg-slate-900 border border-slate-800 text-white rounded-2xl font-bold text-base hover:bg-slate-800 transition-all flex items-center gap-2">
               <Code2 className="w-5 h-5" /> View Architecture
            </Link>
          </motion.div>
        </div>

        {/* Strategy Grid */}
        <section className="mt-32">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {STRATEGY_STEPS.map((step, i) => (
              <motion.div 
                key={step.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="p-8 rounded-[2rem] bg-slate-950/40 border border-slate-800/60 backdrop-blur-md relative overflow-hidden group hover:border-primary/50 transition-all"
              >
                <div className={cn("mb-6 p-3 rounded-2xl bg-slate-900 inline-block", step.color)}>
                  <step.icon className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold text-white mb-4">{step.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{step.description}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Technical Architecture View */}
        <section id="architecture" className="mt-32 pt-20 border-t border-slate-800/50">
          <div className="text-center mb-16">
            <h2 className="text-sm font-black text-primary uppercase tracking-[0.3em] mb-4">Under The Hood</h2>
            <h3 className="text-3xl md:text-5xl font-black text-white tracking-tighter">Enterprise-Grade Infrastructure</h3>
            <p className="mt-6 text-slate-400 max-w-2xl mx-auto">
              Sovereignty isn't just a buzzword. It's built into every layer of our stack. GraftAI operates on a robust, asynchronous tech stack designed for speed and security.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {ARCHITECTURE_NODES.map((node, i) => (
               <motion.div 
                 key={node.layer}
                 initial={{ opacity: 0, x: i % 2 === 0 ? -20 : 20 }}
                 whileInView={{ opacity: 1, x: 0 }}
                 viewport={{ once: true }}
                 transition={{ delay: i * 0.1 }}
                 className="group relative bg-slate-900/30 border border-slate-800 backdrop-blur-sm rounded-[2rem] p-8 overflow-hidden hover:bg-slate-900/60 hover:border-slate-700 transition-all"
               >
                  <div className={`absolute top-0 right-0 w-32 h-32 bg-${node.color}-500/10 blur-[50px] group-hover:bg-${node.color}-500/20 transition-colors`} />
                  <div className="flex items-start gap-6 relative z-10">
                     <div className={`p-4 rounded-2xl bg-slate-950 border border-slate-800 text-${node.color}-400 shadow-lg`}>
                        <node.icon className="w-8 h-8" />
                     </div>
                     <div>
                        <span className={`text-[10px] font-black uppercase tracking-widest text-${node.color}-500 mb-2 block`}>{node.layer}</span>
                        <h4 className="text-xl font-bold text-white mb-2">{node.tech}</h4>
                        <p className="text-sm text-slate-400 leading-relaxed">{node.desc}</p>
                     </div>
                  </div>
               </motion.div>
            ))}
          </div>
        </section>

      </main>

      {/* SaaS Grade Footer */}
      <footer className="mt-32 border-t border-slate-800/80 bg-slate-950/50 backdrop-blur-xl relative z-10">
         <div className="max-w-7xl mx-auto px-6 py-20 lg:px-8">
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-12">
               
               <div className="col-span-2 space-y-8">
                  <div className="flex items-center gap-3">
                     <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-fuchsia-600 flex items-center justify-center font-bold text-white text-xl shadow-lg shadow-primary/20">G</div>
                     <span className="font-black text-2xl tracking-tighter text-white">GraftAI</span>
                  </div>
                  <p className="text-sm text-slate-400 max-w-sm leading-relaxed">
                     The autonomous scheduling engine for sovereigns. Secure, hyper-fast, and built on an open protocol.
                  </p>
                  <div className="flex gap-4">
                     <a href="https://github.com/graftai" className="w-10 h-10 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-400 hover:text-white hover:border-slate-600 transition-all">
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd"/></svg>
                     </a>
                     <a href="https://twitter.com/graftai" className="w-10 h-10 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-400 hover:text-white hover:border-slate-600 transition-all">
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84"/></svg>
                     </a>
                  </div>
               </div>

               <div className="space-y-6">
                  <h4 className="text-[11px] font-black uppercase tracking-[0.2em] text-white">Product</h4>
                  <ul className="space-y-4 text-sm text-slate-400">
                     <li><Link href="/features" className="hover:text-primary transition-colors">Features</Link></li>
                     <li><Link href="/pricing" className="hover:text-primary transition-colors">Pricing</Link></li>
                     <li><Link href="/changelog" className="hover:text-primary transition-colors">Changelog</Link></li>
                     <li><Link href="/integrations" className="hover:text-primary transition-colors">Integrations</Link></li>
                  </ul>
               </div>

               <div className="space-y-6">
                  <h4 className="text-[11px] font-black uppercase tracking-[0.2em] text-white">Developers</h4>
                  <ul className="space-y-4 text-sm text-slate-400">
                     <li><Link href="/docs/api" className="hover:text-primary transition-colors">API Reference</Link></li>
                     <li><Link href="#architecture" className="hover:text-primary transition-colors">Architecture</Link></li>
                     <li><Link href="/status" className="hover:text-primary flex items-center justify-between transition-colors">
                        Status {backendStatus === 'live' ? <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span> : <span className="w-2 h-2 rounded-full bg-slate-500"></span>}
                     </Link></li>
                     <li><a href="https://github.com/graftai" className="hover:text-primary transition-colors">Open Source</a></li>
                  </ul>
               </div>

               <div className="space-y-6">
                  <h4 className="text-[11px] font-black uppercase tracking-[0.2em] text-white">Legal</h4>
                  <ul className="space-y-4 text-sm text-slate-400">
                     <li><Link href="/privacy" className="hover:text-primary transition-colors">Privacy Policy</Link></li>
                     <li><Link href="/terms" className="hover:text-primary transition-colors">Terms of Service</Link></li>
                     <li><Link href="/security" className="hover:text-primary transition-colors flex gap-2">Security <Lock className="w-3 h-3 inline pb-0.5"/></Link></li>
                     <li><Link href="/dpa" className="hover:text-primary transition-colors">DPA</Link></li>
                  </ul>
               </div>
            </div>

            <div className="mt-20 pt-8 border-t border-slate-800/80 flex flex-col md:flex-row justify-between items-center gap-4 text-xs font-semibold text-slate-500">
               <p>© {new Date().getFullYear()} GRAFTAI INC. ALL RIGHTS RESERVED.</p>
               <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
                  <Activity className="w-3.5 h-3.5 text-primary" /> System ID: GRFT-PROD-01
               </div>
            </div>
         </div>
      </footer>
    </div>
  );
}
