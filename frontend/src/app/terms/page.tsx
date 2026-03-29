"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Scale, ArrowLeft, Gavel, FileText, Bot, Zap } from "lucide-react";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-[#020617] text-slate-300 font-sans selection:bg-violet-500/30 overflow-x-hidden">
      
      {/* ── Ambient Glow ── */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] right-[-10%] w-[60%] h-[60%] bg-fuchsia-600/5 rounded-full blur-[140px] opacity-30" />
      </div>

      <nav className="fixed top-0 w-full z-[100] border-b border-white/5 bg-[#020617]/60 backdrop-blur-xl">
        <div className="max-w-4xl mx-auto px-6 h-20 flex items-center justify-between">
          <Link href="/" className="group flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            Back to Dashboard
          </Link>
          <span className="text-xl font-black tracking-tighter text-white">GraftAI</span>
        </div>
      </nav>

      <main className="relative z-10 pt-32 pb-24 px-6 max-w-4xl mx-auto">
        <motion.header
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-16"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-black uppercase tracking-widest mb-6">
            <Scale className="w-3 h-3" />
            Legal Service Agreement
          </div>
          <h1 className="text-4xl md:text-6xl font-black text-white tracking-tight leading-none mb-4 uppercase">Terms of Service.</h1>
          <p className="text-slate-500 font-bold tracking-widest uppercase text-xs">Last Updated: March 2026</p>
        </motion.header>

        <section className="space-y-12 text-sm md:text-base leading-relaxed text-slate-400 border-l border-white/5 pl-8 ml-2">
          
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}>
            <h2 className="text-white font-black text-lg mb-4 uppercase tracking-tighter">1. Product Sovereignty.</h2>
            <p>
              By &quot;grafting&quot; our AI agents into your calendar stack, you acknowledge that GraftAI acts as an autonomous 
              scheduling proxy. You retain full ownership and responsibility for the appointments negotiated by the AI 
              within the parameters you define.
            </p>
          </motion.div>

          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}>
            <h2 className="text-white font-black text-lg mb-4 uppercase tracking-tighter">2. Acceptable Use.</h2>
            <p>
              Users must not use the GraftAI platform for mass automated spam scheduling or malicious orchestration of 
              third-party resources. Any attempt to reverse-engineer our proprietary <strong>Conflict Negotiation Logic</strong> 
              is strictly prohibited.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 py-8">
            <div className="p-6 rounded-2xl bg-white/5 border border-white/5 backdrop-blur-lg">
              <Bot className="w-6 h-6 text-blue-500 mb-4" />
              <h3 className="text-white font-bold mb-2">AI Orchestration</h3>
              <p className="text-xs text-slate-500">Autonomous meeting generation is subject to the availability of the connected platform (Zoom, Google, etc.).</p>
            </div>
            <div className="p-6 rounded-2xl bg-white/5 border border-white/5 backdrop-blur-lg">
              <Zap className="w-6 h-6 text-yellow-500 mb-4" />
              <h3 className="text-white font-bold mb-2">Service Uptime</h3>
              <p className="text-xs text-slate-500">We aim for 99.9% uptime of our scheduling cluster, barring scheduled maintenance or upstream API blackouts.</p>
            </div>
          </div>

          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}>
            <h2 className="text-white font-black text-lg mb-4 uppercase tracking-tighter">3. Limitation of Liability.</h2>
            <p>
              GraftAI is not liable for meeting attendance failures or technical synchronization errors caused by 
              third-party API interruptions. Our liability is capped at the total amount paid for the service in the 
              preceding three-month period.
            </p>
          </motion.div>

          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}>
            <h2 className="text-white font-black text-lg mb-4 uppercase tracking-tighter">4. Termination.</h2>
            <p className="mb-8">
              You may terminate your &quot;Sovereign Account&quot; at any time. Upon termination, we will purge all encrypted tokens 
              and metadata within 72 hours, effectively severing the &quot;graft&quot; between our AI and your data.
            </p>
          </motion.div>

        </section>

        <footer className="mt-20 pt-12 border-t border-white/5 text-center">
            <p className="text-xs font-black text-slate-700 tracking-[0.3em] uppercase mb-8">© 2026 GRAFT AI PROTOCOL. ALL RIGHTS RESERVED.</p>
            <Link href="/" className="inline-flex h-12 px-8 bg-white text-black rounded-xl font-black hover:bg-slate-200 transition-all uppercase tracking-tighter items-center gap-4">
                Accept & Proceed
            </Link>
        </footer>
      </main>
    </div>
  );
}
