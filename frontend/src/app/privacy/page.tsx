"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Shield, ArrowLeft, Lock, Eye, Globe, Fingerprint } from "lucide-react";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#020617] text-slate-300 font-sans selection:bg-violet-500/30 overflow-x-hidden">
      
      {/* ── Ambient Glow ── */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[60%] h-[60%] bg-violet-600/5 rounded-full blur-[140px] opacity-50" />
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
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-black uppercase tracking-widest mb-6">
            <Shield className="w-3 h-3" />
            Sovereign Trust Verified
          </div>
          <h1 className="text-4xl md:text-6xl font-black text-white tracking-tight leading-none mb-4 uppercase">Privacy Policy.</h1>
          <p className="text-slate-500 font-bold tracking-widest uppercase text-xs">Last Updated: March 2026</p>
        </motion.header>

        <section className="space-y-12 text-sm md:text-base leading-relaxed text-slate-400 border-l border-white/5 pl-8 ml-2">
          
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}>
            <h2 className="text-white font-black text-lg mb-4 uppercase tracking-tighter">1. Data Sovereignty.</h2>
            <p>
              At GraftAI, we believe that your calendar data is an extension of your sovereign identity. 
              We do not &quot;own&quot; your information; we merely orchestrate it. Under our <strong>Zero-Persistence Protocol</strong>, 
              meeting metadata is processed in high-fidelity memory and encrypted at rest using AES-256 bit Fernet logic.
            </p>
          </motion.div>

          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}>
            <h2 className="text-white font-black text-lg mb-4 uppercase tracking-tighter">2. Token Encapsulation.</h2>
            <p>
              External service tokens (e.g., Zoom, Google, Microsoft) are isolated within <strong>Encrypted Context Containers</strong>. 
              GraftAI AI agents operate with least-privilege security, ensuring they only access the minimal metadata required 
              to execute scheduling negotiations on your behalf.
            </p>
          </motion.div>

          {/* Additional clauses... */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 py-8">
            <div className="p-6 rounded-2xl bg-white/5 border border-white/5 backdrop-blur-lg">
              <Lock className="w-6 h-6 text-violet-500 mb-4" />
              <h3 className="text-white font-bold mb-2">Biometric Isolation</h3>
              <p className="text-xs text-slate-500">Passkey data never leaves your device. We only store public signatures for verification.</p>
            </div>
            <div className="p-6 rounded-2xl bg-white/5 border border-white/5 backdrop-blur-lg">
              <Fingerprint className="w-6 h-6 text-emerald-500 mb-4" />
              <h3 className="text-white font-bold mb-2">Universal Deletion</h3>
              <p className="text-xs text-slate-500">A &quot;Purge&quot; request from your dashboard initiates a cryptographic erase across all nodes.</p>
            </div>
          </div>

          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}>
            <h2 className="text-white font-black text-lg mb-4 uppercase tracking-tighter">3. Compliance Badges.</h2>
            <p className="mb-8">
              GraftAI is architected for GDPR, CCPA, and SOC2 compliance. Our infrastructure is hosted on ISO 27001 certified 
              environments, ensuring that the &quot;grafted&quot; intelligence layer adheres to the strictest global standards.
            </p>
            <div className="flex gap-4 opacity-50 grayscale hover:grayscale-0 transition-all cursor-crosshair">
              <div className="px-4 py-2 bg-slate-800 rounded-lg text-[10px] font-black">GDPR READY</div>
              <div className="px-4 py-2 bg-slate-800 rounded-lg text-[10px] font-black">SOC2 TYPE II</div>
              <div className="px-4 py-2 bg-slate-800 rounded-lg text-[10px] font-black">ISO 27001</div>
            </div>
          </motion.div>

        </section>

        <footer className="mt-20 pt-12 border-t border-white/5 text-center">
            <p className="text-xs font-black text-slate-700 tracking-[0.3em] uppercase mb-8">© 2026 GRAFT AI PROTOCOL. ALL RIGHTS RESERVED.</p>
            <Link href="/" className="inline-flex h-12 px-8 bg-white text-black rounded-xl font-black hover:bg-slate-200 transition-all uppercase tracking-tighter items-center gap-4">
                Got it, Take me back
            </Link>
        </footer>
      </main>
    </div>
  );
}
