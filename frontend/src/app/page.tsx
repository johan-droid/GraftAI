"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Bot, ShieldCheck, Sparkles, Zap, Lock, Globe, Cloud, FileText, Scale, Mail, GraduationCap, ArrowRight, BrainCircuit, Fingerprint, Database } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
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

const features = [
  { icon: <Fingerprint className="w-6 h-6" />, title: "Federated Identity", description: "Zero-trust authentication with SSO and Biometric support." },
  { icon: <Database className="w-6 h-6" />, title: "Vector Memory", description: "Your AI remembers your preferences without leaking your data." },
  { icon: <Globe className="w-6 h-6" />, title: "Global Sync", description: "Atomic updates across Google, Outlook, and private nodes." },
];

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<"unknown" | "live" | "sleeping">("unknown");

  const checkBackend = useCallback(async () => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "";
      const resp = await fetch(`${baseUrl}/health`.replace(/\/+/g, '/').replace(':/', '://'), { cache: "no-store" });
      if (resp.ok) setBackendStatus("live");
      else setBackendStatus("sleeping");
    } catch {
      setBackendStatus("sleeping");
    }
  }, []);

  useEffect(() => {
    checkBackend();
    const timer = setInterval(checkBackend, 30000);
    return () => clearInterval(timer);
  }, [checkBackend]);

  return (
    <div className="min-h-screen bg-[#020617] text-slate-100 selection:bg-primary/30 selection:text-white">
      {/* Dynamic Background */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] right-[-10%] w-[70%] h-[70%] bg-indigo-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[60%] h-[60%] bg-fuchsia-600/10 rounded-full blur-[140px]" />
      </div>

      <main className="relative z-10 max-w-7xl mx-auto px-6 pt-24 pb-32 sm:pt-32 lg:px-8">
        {/* Status Pill */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex justify-center mb-10"
        >
          <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-slate-900/50 border border-white/5 backdrop-blur-xl">
             <span className="relative flex h-2 w-2">
                <span className={cn(
                  "absolute inline-flex h-full w-full rounded-full opacity-75",
                  backendStatus === "live" ? "animate-ping bg-emerald-500" : "bg-slate-500"
                )}></span>
                <span className={cn(
                  "relative inline-flex rounded-full h-2 w-2",
                  backendStatus === "live" ? "bg-emerald-500" : "bg-slate-600"
                )}></span>
             </span>
             <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">
               {backendStatus === "live" ? "Systems Nominal" : "Connecting to Node..."}
             </span>
          </div>
        </motion.div>

        {/* Hero Section */}
        <div className="text-center max-w-4xl mx-auto">
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
            <Link href="/#features" className="w-full sm:w-auto px-8 py-4 bg-slate-900 border border-slate-800 text-white rounded-2xl font-bold text-base hover:bg-slate-800 transition-all">
              Security Protocol
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

        {/* Mini Features */}
        <section id="features" className="mt-20 py-20 border-t border-white/5">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {features.map((f, i) => (
              <div key={i} className="flex gap-4">
                 <div className="text-primary shrink-0 mt-1">{f.icon}</div>
                 <div>
                    <h4 className="font-bold text-white mb-1">{f.title}</h4>
                    <p className="text-xs text-slate-500 leading-relaxed">{f.description}</p>
                 </div>
              </div>
            ))}
          </div>
        </section>

        {/* Professional Footer */}
        <footer className="mt-32 pt-16 border-t border-white/5">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
            <div className="md:col-span-2 space-y-6">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center font-bold text-white">G</div>
                <span className="font-black text-xl tracking-tighter">GraftAI</span>
              </div>
              <p className="text-sm text-slate-500 max-w-sm leading-relaxed">
                Academic research project in Major SaaS Engineering. Focused on secure data federation and autonomous scheduling intelligence.
              </p>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-indigo-500/5 border border-indigo-500/10 text-[10px] font-black uppercase tracking-widest text-indigo-400">
                <GraduationCap className="w-4 h-4" /> Major Portfolio Ready
              </div>
            </div>
            
            <div className="space-y-4">
              <h5 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Node Links</h5>
              <ul className="space-y-2 text-sm text-slate-500">
                <li><Link href="/login" className="hover:text-white transition-colors">Authentication</Link></li>
                <li><Link href="/privacy-policy" className="hover:text-white transition-colors">Privacy Lexicon</Link></li>
                <li><Link href="/terms-of-service" className="hover:text-white transition-colors">Operational Terms</Link></li>
              </ul>
            </div>

            <div className="space-y-4">
              <h5 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Transmission</h5>
              <ul className="space-y-2 text-sm text-slate-500">
                <li className="flex items-center gap-2"><Mail className="w-4 h-4" /> project@graftai.tech</li>
                <li className="flex items-center gap-2"><Globe className="w-4 h-4" /> v1.0.1 Stable</li>
              </ul>
            </div>
          </div>
          <div className="mt-20 text-[10px] font-medium text-slate-600 flex justify-between uppercase tracking-widest">
            <span>© {new Date().getFullYear()} GRAFTAI LABS</span>
            <span>BUILT FOR EVALUATION</span>
          </div>
        </footer>
      </main>
    </div>
  );
}
