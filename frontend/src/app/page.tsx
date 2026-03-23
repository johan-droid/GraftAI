"use client";

import Link from "next/link";
import { motion, Variants } from "framer-motion";
import { Calendar, Bot, ChevronRight, ShieldCheck, Sparkles } from "lucide-react";

export default function Home() {
  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { staggerChildren: 0.12 }
    }
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <div className="app-shell flex flex-col min-h-[100dvh]">
      <main className="flex-1 flex flex-col items-center px-5 relative overflow-hidden">
        
        {/* Background glow — hidden on small screens for performance */}
        <div className="hidden md:block absolute top-[10%] left-1/4 w-[500px] h-[500px] bg-primary/20 rounded-full blur-[120px] pointer-events-none" />
        <div className="hidden md:block absolute top-[40%] right-1/4 w-[400px] h-[400px] bg-fuchsia-500/10 rounded-full blur-[100px] pointer-events-none" />

        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="w-full max-w-6xl z-10 flex flex-col items-center pt-16 md:pt-24 pb-20"
        >
          {/* ── Hero Section ── */}
          <div className="flex flex-col items-center mb-24 md:mb-32">
            <motion.div variants={itemVariants} className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary border border-primary/20 mb-6 md:mb-8 text-xs md:text-sm font-medium">
              <Sparkles className="w-3.5 h-3.5 md:w-4 md:h-4" />
              <span>Next-Gen AI Scheduling</span>
            </motion.div>

            <motion.h1 variants={itemVariants} className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-center tracking-tight mb-4 md:mb-6 leading-[1.1]">
              Schedule Smarter <br className="hidden sm:block" />
              with <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-fuchsia-400">GraftAI Copilot</span>
            </motion.h1>

            <motion.p variants={itemVariants} className="text-base md:text-xl text-slate-400 max-w-2xl text-center mb-8 md:mb-10 leading-relaxed px-2">
              The autonomous AI assistant that manages your calendar, syncs with Cal.com, and handles meeting requests perfectly.
            </motion.p>

            <motion.div variants={itemVariants} className="flex flex-col gap-3 w-full max-w-sm sm:max-w-none sm:flex-row sm:items-center sm:gap-4 sm:w-auto">
              <Link
                href="/login"
                className="w-full sm:w-auto relative group flex items-center justify-center gap-2 rounded-xl bg-primary px-6 py-3.5 md:px-8 md:py-4 text-sm md:text-base font-semibold text-white transition-all hover:bg-primary/90 hover:shadow-[0_0_30px_rgba(79,70,229,0.4)]"
              >
                Get Started Free
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                href="/dashboard"
                className="w-full sm:w-auto flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-900/50 backdrop-blur px-6 py-3.5 md:px-8 md:py-4 text-sm md:text-base font-medium text-slate-300 transition-all hover:bg-slate-800 hover:text-white"
              >
                Access Dashboard
              </Link>
            </motion.div>
          </div>

          {/* ── Features Section ── */}
          <motion.div variants={itemVariants} className="w-full">
            <div className="text-center mb-12 md:mb-16">
              <h2 className="text-2xl md:text-4xl font-bold text-white mb-4">Everything you need to automate your day</h2>
              <p className="text-slate-400 text-sm md:text-base max-w-2xl mx-auto">
                GraftAI provides a complete suite of tools to manage your time, secure your identity, and extend your capabilities.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
              {[
                {
                  id: "ai",
                  icon: <Bot className="w-6 h-6 text-primary" />,
                  title: "Autonomous AI Copilot",
                  desc: "Let our advanced LLM orchestration handle complex booking intent, negotiations, and scheduling back-and-forth seamlessly."
                },
                {
                  id: "sync",
                  icon: <Calendar className="w-6 h-6 text-fuchsia-400" />,
                  title: "Smart Calendar Sync",
                  desc: "Deep two-way integration with Cal.com and existing calendar workflows to ensure you're never double-booked."
                },
                {
                  id: "auth",
                  icon: <ShieldCheck className="w-6 h-6 text-emerald-400" />,
                  title: "Enterprise-Grade Auth",
                  desc: "Passwordless magic links, FIDO2/WebAuthn passkeys, and enterprise SSO (Google, GitHub, Microsoft) out of the box."
                },
                {
                  id: "plugins",
                  icon: <svg className="w-6 h-6 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" /></svg>,
                  title: "Extensible Plugins",
                  desc: "Browse and install powerful plugins from the marketplace to connect GraftAI with your favorite external tools and APIs."
                },
                {
                  id: "proactive",
                  icon: <Sparkles className="w-6 h-6 text-blue-400" />,
                  title: "Proactive Suggestions",
                  desc: "The system learns your habits and proactively suggests meeting times, breaks, and context preparation before you even ask."
                },
                {
                  id: "privacy",
                  icon: <svg className="w-6 h-6 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>,
                  title: "Granular Privacy Controls",
                  desc: "You own your data. Manage fine-grained consent settings for AI processing, data tracking, and third-party access directly in settings."
                }
              ].map((feature) => (
                <div key={feature.id} className="bg-slate-900/40 backdrop-blur-sm border border-slate-800 rounded-2xl p-6 flex flex-col gap-4 group hover:bg-slate-800/60 hover:-translate-y-1 transition-all duration-300">
                  <div className="w-12 h-12 rounded-xl bg-slate-950 flex items-center justify-center border border-slate-800 group-hover:border-slate-700 transition-colors">
                    {feature.icon}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                    <p className="text-slate-400 text-sm leading-relaxed">{feature.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </motion.div>
      </main>

      {/* ── Footer ── */}
      <footer className="border-t border-slate-800 bg-slate-950/50 py-12 px-5 md:px-10">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8 md:gap-12">
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-fuchsia-600 flex items-center justify-center">
                <span className="text-white font-bold text-sm leading-none">G</span>
              </div>
              <span className="text-white font-bold text-lg">GraftAI</span>
            </div>
            <p className="text-slate-500 text-sm leading-relaxed mb-6">
              The next generation of autonomous scheduling and AI orchestration for modern professionals.
            </p>
          </div>
          
          <div>
            <h4 className="text-white font-medium mb-4">Product</h4>
            <ul className="space-y-3 text-sm">
              <li><Link href="#features" className="text-slate-400 hover:text-primary transition-colors">Features</Link></li>
              <li><Link href="#" className="text-slate-400 hover:text-primary transition-colors">Integrations</Link></li>
              <li><Link href="/dashboard/plugins" className="text-slate-400 hover:text-primary transition-colors">Plugins</Link></li>
              <li><Link href="#" className="text-slate-400 hover:text-primary transition-colors">Pricing</Link></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-white font-medium mb-4">Company</h4>
            <ul className="space-y-3 text-sm">
              <li><Link href="#" className="text-slate-400 hover:text-primary transition-colors">About Us</Link></li>
              <li><Link href="#" className="text-slate-400 hover:text-primary transition-colors">Blog</Link></li>
              <li><Link href="#" className="text-slate-400 hover:text-primary transition-colors">Careers</Link></li>
              <li><Link href="#" className="text-slate-400 hover:text-primary transition-colors">Contact</Link></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-white font-medium mb-4">Legal</h4>
            <ul className="space-y-3 text-sm">
              <li><Link href="/privacy" className="text-slate-400 hover:text-primary transition-colors">Privacy Policy</Link></li>
              <li><Link href="/terms" className="text-slate-400 hover:text-primary transition-colors">Terms of Service</Link></li>
              <li><Link href="/dashboard/settings" className="text-slate-400 hover:text-primary transition-colors">Cookie Preferences</Link></li>
              <li><Link href="/security" className="text-slate-400 hover:text-primary transition-colors">Security</Link></li>
            </ul>
          </div>
        </div>
        
        <div className="max-w-6xl mx-auto mt-12 pt-8 border-t border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-slate-500 text-sm">© {new Date().getFullYear()} GraftAI Inc. All rights reserved.</p>
          <div className="flex gap-4">
            {/* Social SVGs could go here */}
            <a href="#" className="text-slate-500 hover:text-white transition-colors">Twitter</a>
            <a href="#" className="text-slate-500 hover:text-white transition-colors">GitHub</a>
            <a href="#" className="text-slate-500 hover:text-white transition-colors">LinkedIn</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
