"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Zap, Bot, Sparkles, Globe, Calendar, ArrowRight, Menu, X, Check
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

const PLAN_PREVIEW = [
  {
    name: "Standard",
    price: "$0",
    description: "For individuals getting started with unified scheduling.",
    points: ["10 AI messages/day", "3 manual syncs/day", "Google + Microsoft calendar"],
    cta: "Start Free",
    href: "/register",
    featured: false,
  },
  {
    name: "Professional",
    price: "$19",
    description: "For heavy users who run their full workday through GraftAI.",
    points: ["200 AI messages/day", "50 manual syncs/day", "Priority processing + analytics"],
    cta: "Upgrade to Pro",
    href: "/pricing",
    featured: true,
  },
  {
    name: "Elite Sovereign",
    price: "$49",
    description: "For executive workflows and advanced AI-assisted operations.",
    points: ["High-volume AI usage", "Advanced integrations", "Concierge support model"],
    cta: "See Full Plans",
    href: "/pricing",
    featured: false,
  },
];

const FOOTER_LINK_GROUPS = [
  {
    title: "Product",
    links: [
      { label: "Features", href: "#features" },
      { label: "Pricing", href: "/pricing" },
      { label: "Docs", href: "/docs" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "Sign In", href: "/login" },
      { label: "Create Account", href: "/register" },
      { label: "Dashboard", href: "/dashboard" },
    ],
  },
  {
    title: "Legal",
    links: [
      { label: "Privacy Policy", href: "/privacy-policy" },
      { label: "Terms of Service", href: "/terms-of-service" },
      { label: "Documentation", href: "/docs" },
    ],
  },
];

// --- Sub-components ---
interface NavProps {
  scrolled: boolean;
  setMobileOpen: (value: boolean) => void;
}

const Nav = ({ scrolled, setMobileOpen }: NavProps) => (
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
        <Link href="/docs" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Docs</Link>
        <Link href="/login" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Sign in</Link>
        <Link href="/register" className="group flex items-center gap-2 rounded-xl bg-white px-5 py-2.5 text-sm font-bold text-black hover:bg-slate-200 transition-all active:scale-95">
          Get Started
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
        </Link>
      </div>

      <button
        onClick={() => setMobileOpen(true)}
        aria-label="Open navigation menu"
        title="Open menu"
        className="md:hidden flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-white"
      >
        <Menu className="h-5 w-5" />
      </button>
    </nav>
  </header>
);

interface FeatureCardProps {
  f: {
    icon: ReactNode;
    title: string;
    desc: string;
    accent: string;
    bg: string;
    border: string;
  };
  index: number;
}

const FeatureCard = ({ f, index }: FeatureCardProps) => (
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

      {/* Pricing Preview */}
      <section id="pricing" className="px-6 pb-24">
        <div className="mx-auto max-w-6xl">
          <div className="mb-10 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Pricing</p>
              <h2 className="mt-2 text-3xl font-black text-white md:text-5xl">Transparent plans for every stage.</h2>
            </div>
            <Link
              href="/pricing"
              className="inline-flex items-center gap-2 self-start rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/10"
            >
              Compare all plans
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          <div className="grid gap-5 md:grid-cols-3">
            {PLAN_PREVIEW.map((plan) => (
              <article
                key={plan.name}
                className={`rounded-3xl border p-6 ${
                  plan.featured
                    ? "border-indigo-500/40 bg-indigo-500/10 shadow-xl shadow-indigo-500/10"
                    : "border-white/10 bg-white/[0.02]"
                }`}
              >
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{plan.name}</p>
                <p className="mt-3 text-4xl font-black text-white">{plan.price}</p>
                <p className="mt-3 text-sm leading-relaxed text-slate-400">{plan.description}</p>

                <ul className="mt-5 space-y-2 text-sm text-slate-300">
                  {plan.points.map((point) => (
                    <li key={point} className="flex items-start gap-2">
                      <Check className="mt-0.5 h-4 w-4 text-indigo-400" />
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>

                <Link
                  href={plan.href}
                  className={`mt-6 inline-flex w-full items-center justify-center rounded-xl px-4 py-2.5 text-sm font-bold transition ${
                    plan.featured
                      ? "bg-white text-black hover:bg-slate-200"
                      : "border border-white/10 bg-white/5 text-white hover:bg-white/10"
                  }`}
                >
                  {plan.cta}
                </Link>
              </article>
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
      <footer className="border-t border-white/[0.05] py-14">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid gap-10 text-left md:grid-cols-[1.2fr_1fr_1fr_1fr]">
            <div>
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/25">
                  <Zap className="h-4 w-4 fill-white text-white" />
                </div>
                <span className="text-sm font-black uppercase tracking-wide text-white">GraftAI</span>
              </div>
              <p className="mt-4 max-w-xs text-sm leading-relaxed text-slate-400">
                AI-assisted scheduling infrastructure for focus-driven teams and individuals.
              </p>
            </div>

            {FOOTER_LINK_GROUPS.map((group) => (
              <div key={group.title}>
                <h3 className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">{group.title}</h3>
                <div className="mt-4 flex flex-col gap-2 text-sm text-slate-300">
                  {group.links.map((link) => (
                    <Link key={link.label} href={link.href} className="transition hover:text-white">
                      {link.label}
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-10 flex flex-col gap-2 border-t border-white/10 pt-6 text-xs text-slate-500 md:flex-row md:items-center md:justify-between">
            <p className="font-semibold uppercase tracking-[0.12em]">© 2026 GraftAI · The Presentation Version</p>
            <p>Built for speed, clarity, and scheduling sovereignty.</p>
          </div>
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
            <button
              onClick={() => setMobileOpen(false)}
              aria-label="Close navigation menu"
              title="Close menu"
              className="absolute top-8 right-8 text-white"
            ><X className="w-8 h-8" /></button>
            <div className="flex flex-col gap-10">
               <Link onClick={() => setMobileOpen(false)} href="/login" className="text-4xl font-black text-white transition-opacity hover:opacity-70">Sign In</Link>
               <Link onClick={() => setMobileOpen(false)} href="/register" className="text-4xl font-black text-indigo-400 transition-opacity hover:opacity-70">Register</Link>
               <Link onClick={() => setMobileOpen(false)} href="#features" className="text-4xl font-black text-white transition-opacity hover:opacity-70">Features</Link>
              <Link onClick={() => setMobileOpen(false)} href="/pricing" className="text-4xl font-black text-white transition-opacity hover:opacity-70">Pricing</Link>
               <Link onClick={() => setMobileOpen(false)} href="/docs" className="text-4xl font-black text-white transition-opacity hover:opacity-70">Docs</Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
