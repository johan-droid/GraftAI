"use client";

import Link from "next/link";
import { useState, useEffect, useRef } from "react";
import { motion, useScroll, useTransform, AnimatePresence } from "framer-motion";
import {
  Bot, Sparkles, Globe, Zap, Lock, ChevronRight, ArrowRight,
  CheckCircle2, Clock, Star, Menu, X, Shield, Crown,
  TrendingUp, Users, Activity, ChevronDown,
} from "lucide-react";

// ─── Data ──────────────────────────────────────────────────────
const LOGOS = [
  "Stripe", "Linear", "Vercel", "Notion", "Figma", "Loom", "Intercom", "Retool",
];

const FEATURES_BENTO = [
  {
    colspan: "md:col-span-2",
    icon: <Bot className="w-6 h-6" />,
    tag: "AI Copilot",
    accent: "text-violet-400",
    bg: "from-violet-500/8 to-indigo-500/4",
    border: "border-violet-500/20",
    title: "A scheduling brain, not just a chatbot",
    desc: "GraftAI remembers context, tracks preferences, and handles the back-and-forth automatically. It gets smarter with every interaction.",
    visual: (
      <div className="mt-4 space-y-2">
        {[
          { msg: "Find time with Alex next week", side: "user" },
          { msg: "Tuesday 2–3 PM works across all timezones. Sending invite now ✓", side: "ai" },
          { msg: "Block every Friday afternoon for deep work", side: "user" },
          { msg: "Done. Protected 13 upcoming Fridays.", side: "ai" },
        ].map((m, i) => (
          <div key={i} className={`flex ${m.side === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] rounded-xl px-3 py-2 text-[11px] font-medium leading-snug ${
              m.side === "user"
                ? "bg-indigo-500/20 text-indigo-200"
                : "bg-slate-800/60 text-slate-300"
            }`}>
              {m.side === "ai" && <span className="text-violet-400 font-bold mr-1.5">✦</span>}
              {m.msg}
            </div>
          </div>
        ))}
      </div>
    ),
  },
  {
    colspan: "md:col-span-1",
    icon: <Globe className="w-6 h-6" />,
    tag: "Global",
    accent: "text-blue-400",
    bg: "from-blue-500/8 to-cyan-500/4",
    border: "border-blue-500/20",
    title: "Timezones, eliminated",
    desc: "NYC, London, Singapore — GraftAI finds the overlap and proposes the slot in seconds.",
    visual: (
      <div className="mt-4 grid grid-cols-3 gap-2">
        {["NYC 9am", "LON 2pm", "SGP 9pm"].map((tz) => (
          <div key={tz} className="rounded-lg bg-blue-500/10 border border-blue-500/20 px-2 py-2 text-center">
            <p className="text-[10px] text-blue-300 font-bold">{tz}</p>
            <div className="mt-1 h-1 rounded-full bg-blue-500/30" />
          </div>
        ))}
      </div>
    ),
  },
  {
    colspan: "md:col-span-1",
    icon: <Zap className="w-6 h-6" />,
    tag: "Realtime",
    accent: "text-amber-400",
    bg: "from-amber-500/8 to-orange-500/4",
    border: "border-amber-500/20",
    title: "Live calendar sync",
    desc: "Changes propagate instantly. No stale data. No double bookings. Zero latency.",
    visual: (
      <div className="mt-4 flex items-center gap-2">
        <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
        <p className="text-[11px] text-slate-400">Synced <span className="text-emerald-400 font-bold">0.3s</span> ago</p>
      </div>
    ),
  },
  {
    colspan: "md:col-span-1",
    icon: <Lock className="w-6 h-6" />,
    tag: "Privacy",
    accent: "text-emerald-400",
    bg: "from-emerald-500/8 to-teal-500/4",
    border: "border-emerald-500/20",
    title: "Your data, your rules",
    desc: "Passkey auth, granular consent controls, zero third-party trackers built in.",
    visual: null,
  },
  {
    colspan: "md:col-span-1",
    icon: <Sparkles className="w-6 h-6" />,
    tag: "Proactive",
    accent: "text-rose-400",
    bg: "from-rose-500/8 to-pink-500/4",
    border: "border-rose-500/20",
    title: "Proactive, not reactive",
    desc: "GraftAI flags your tight Tuesdays and suggests buffer time before you even notice.",
    visual: null,
  },
  {
    colspan: "md:col-span-1",
    icon: <Shield className="w-6 h-6" />,
    tag: "Enterprise",
    accent: "text-slate-400",
    bg: "from-slate-500/8 to-slate-600/4",
    border: "border-slate-500/20",
    title: "Enterprise-ready",
    desc: "SSO, MFA, RBAC, custom domains. Everything IT needs to say yes.",
    visual: null,
  },
];

const TESTIMONIALS = [
  {
    quote: "We cut scheduling overhead by half in the first week. Feels almost unfair.",
    name: "Mia Chen", role: "Eng Lead @ Stripe", avatar: "MC", stars: 5,
    color: "from-violet-500/20 to-indigo-500/10",
  },
  {
    quote: "Finally a calendar tool that doesn't feel like it was designed by a committee.",
    name: "Dev Ramirez", role: "Solo founder", avatar: "DR", stars: 5,
    color: "from-blue-500/20 to-cyan-500/10",
  },
  {
    quote: "The timezone handling alone is worth the price. Our distributed team swears by it.",
    name: "Anaya Osei", role: "Head of Ops @ Linear", avatar: "AO", stars: 5,
    color: "from-emerald-500/20 to-teal-500/10",
  },
];

const STATS = [
  { value: "40%", label: "less time scheduling", icon: <TrendingUp className="w-4 h-4" /> },
  { value: "12k+", label: "active teams", icon: <Users className="w-4 h-4" /> },
  { value: "99.9%", label: "uptime SLA", icon: <Activity className="w-4 h-4" /> },
  { value: "4.9★", label: "avg rating", icon: <Star className="w-4 h-4 fill-current" /> },
];

const PRICING_TIERS = [
  {
    id: "free", name: "Standard", price: "$0", per: "",
    description: "Perfect for casual AI-assisted scheduling.",
    features: ["10 AI messages / day", "3 Calendar syncs / day", "Google & Outlook integration", "Standard AI processing"],
    highlight: false, cta: "Get started free", href: "/register",
    icon: <Zap className="w-4 h-4 text-slate-400" />,
  },
  {
    id: "pro", name: "Professional", price: "$12", per: "/ month",
    description: "The productivity engine for high-density users.",
    features: ["200 AI messages / day", "50 Calendar syncs / day", "Priority AI processing", "Advanced time analytics", "Custom booking pages"],
    highlight: true, cta: "Start free trial", href: "/register",
    icon: <Crown className="w-4 h-4 text-indigo-400" />,
  },
  {
    id: "elite", name: "Elite", price: "$49", per: "/ month",
    description: "Unlimited AI coordination for executives.",
    features: ["Unlimited AI messages", "Unlimited calendar syncs", "24/7 concierge support", "Zero-data-retention", "Dedicated infrastructure"],
    highlight: false, cta: "Contact sales", href: "/pricing",
    icon: <Sparkles className="w-4 h-4 text-amber-400" />,
  },
];

const FAQS = [
  { q: "How does GraftAI handle my calendar data?", a: "All calendar data is processed with AES-256 encryption in transit and at rest. We never sell data to third parties. You can export or delete your data at any time from Settings." },
  { q: "Which calendar providers are supported?", a: "Google Calendar and Microsoft Outlook are fully supported with real-time bidirectional sync. Apple Calendar support is in early access." },
  { q: "Is there a free trial for paid plans?", a: "Yes — Professional includes a 14-day free trial with no credit card required. You can upgrade, downgrade, or cancel at any time." },
  { q: "Can my whole team use GraftAI?", a: "Absolutely. Team plans with shared availability templates, RBAC roles, and admin dashboards are available on Pro and Elite tiers." },
  { q: "What AI model powers the scheduling?", a: "GraftAI uses a fine-tuned scheduling model built on top of frontier LLMs, optimized specifically for calendar context, time reasoning, and multi-party coordination." },
];

const MOBILE_TAB_LINKS = [
  { id: "home", label: "Home", href: "#top", icon: Zap },
  { id: "features", label: "Features", href: "#features", icon: Sparkles },
  { id: "pricing", label: "Pricing", href: "#pricing", icon: Crown },
  { id: "faq", label: "FAQ", href: "#faq", icon: Shield },
];

const MOBILE_SHEET_LINKS = [
  { label: "Features", href: "#features" },
  { label: "Pricing", href: "#pricing" },
  { label: "FAQ", href: "#faq" },
];

// ─── Component ─────────────────────────────────────────────────
export default function Home() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [activeMobileTab, setActiveMobileTab] = useState("home");
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ["start start", "end start"] });
  const heroY = useTransform(scrollYProgress, [0, 1], ["0%", "25%"]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.7], [1, 0]);

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 20);
      const triggerY = window.scrollY + window.innerHeight * 0.38;
      const order = ["faq", "pricing", "features"];
      const active = order.find((id) => {
        const el = document.getElementById(id);
        return el ? triggerY >= el.offsetTop : false;
      });
      setActiveMobileTab(active ?? "home");
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (typeof document === "undefined") {
      return;
    }
    document.body.style.overflow = mobileOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  return (
    <div id="top" className="min-h-screen overflow-x-hidden bg-[#070711] pb-[calc(86px+env(safe-area-inset-bottom))] text-slate-200 selection:bg-indigo-500/30 md:pb-0">
      {/* Ambient BG */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -top-[20%] left-[5%] h-[700px] w-[700px] rounded-full bg-indigo-600/8 blur-[140px]" />
        <div className="absolute top-[50%] right-[-5%] h-[500px] w-[500px] rounded-full bg-violet-600/6 blur-[120px]" />
        <div className="absolute bottom-[10%] left-[35%] h-[400px] w-[400px] rounded-full bg-blue-600/5 blur-[100px]" />
        <div className="home-noise-layer absolute inset-0 opacity-[0.035]" />
        <div className="home-grid-layer absolute inset-0 opacity-[0.025]" />
      </div>

      {/* ── Nav ─────────────────────────────────────── */}
      <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled ? "bg-[#070711]/85 backdrop-blur-2xl border-b border-white/[0.06] shadow-2xl shadow-black/30" : ""
      }`}>
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3.5">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/25 transition-shadow group-hover:shadow-indigo-500/50">
              <Zap className="w-4 h-4 text-white fill-white" />
            </div>
            <span className="font-serif text-[15px] font-bold tracking-tight text-white">
              GraftAI
            </span>
          </Link>

          <div className="hidden items-center gap-7 md:flex">
            {[
              { label: "Features", href: "#features" },
              { label: "Pricing", href: "#pricing" },
              { label: "FAQ", href: "#faq" },
            ].map((item) => (
              <Link key={item.label} href={item.href} className="text-sm font-medium text-slate-400 transition-colors hover:text-white">
                {item.label}
              </Link>
            ))}
          </div>

          <div className="hidden items-center gap-2 md:flex">
            <Link href="/login" className="rounded-lg px-4 py-2 text-sm font-medium text-slate-400 transition-all hover:text-white hover:bg-white/5">
              Sign in
            </Link>
            <Link href="/register" className="group relative flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 px-4 py-2 text-sm font-bold text-white shadow-lg shadow-indigo-500/20 transition-all hover:shadow-indigo-500/40 hover:-translate-y-px active:translate-y-0">
              Get started
              <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </div>

          <button
            className="inline-flex h-11 w-11 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-slate-200 md:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </button>
        </nav>

        <AnimatePresence>
          {mobileOpen && (
            <>
              <motion.button
                aria-label="Close mobile menu"
                onClick={() => setMobileOpen(false)}
                className="fixed inset-0 z-[60] bg-black/55 md:hidden"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              />

              <motion.aside
                className="touch-pan-y fixed inset-y-0 right-0 z-[61] w-[min(90vw,380px)] overflow-y-auto border-l border-white/10 bg-[#050919]/95 px-4 pb-[calc(96px+env(safe-area-inset-bottom))] pt-[calc(16px+env(safe-area-inset-top))] backdrop-blur-2xl md:hidden"
                initial={{ x: "100%", opacity: 0.9 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: "100%", opacity: 0.95 }}
                transition={{ duration: 0.24, ease: [0.32, 0.72, 0, 1] }}
              >
                <div className="mb-6 flex items-center justify-between">
                  <div>
                    <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Navigate</p>
                    <h2 className="mt-1 text-base font-semibold text-white">GraftAI Mobile</h2>
                  </div>
                  <button
                    onClick={() => setMobileOpen(false)}
                    className="inline-flex h-11 w-11 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-slate-200"
                    aria-label="Close menu"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>

                <div className="space-y-1.5">
                  {MOBILE_SHEET_LINKS.map((item) => (
                    <Link
                      key={item.label}
                      href={item.href}
                      onClick={() => setMobileOpen(false)}
                      className="flex items-center justify-between rounded-xl border border-white/[0.06] bg-white/[0.03] px-4 py-3.5 text-sm font-medium text-slate-200"
                    >
                      <span>{item.label}</span>
                      <ChevronRight className="h-4 w-4 text-slate-500" />
                    </Link>
                  ))}
                </div>

                <div className="mt-6 flex flex-col gap-2 border-t border-white/[0.08] pt-5">
                  <Link href="/login" onClick={() => setMobileOpen(false)} className="rounded-xl border border-white/10 px-4 py-3 text-center text-sm font-semibold text-slate-200">
                    Sign in
                  </Link>
                  <Link href="/register" onClick={() => setMobileOpen(false)} className="rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 px-4 py-3 text-center text-sm font-bold text-white shadow-lg shadow-indigo-500/20">
                    Get started free
                  </Link>
                </div>
              </motion.aside>
            </>
          )}
        </AnimatePresence>
      </header>

      <div className="mobile-safe-bottom fixed inset-x-0 bottom-0 z-50 px-3 pb-2 md:hidden">
        <nav className="mx-auto flex h-[68px] max-w-md items-center rounded-[24px] border border-white/[0.14] bg-[#040915]/85 px-1.5 backdrop-blur-2xl shadow-2xl shadow-black/45">
          {MOBILE_TAB_LINKS.map((tab) => {
            const isActive = activeMobileTab === tab.id;
            return (
              <Link
                key={tab.id}
                href={tab.href}
                onClick={() => setActiveMobileTab(tab.id)}
                className={`relative flex h-full flex-1 flex-col items-center justify-center gap-0.5 rounded-2xl text-[10px] font-semibold tracking-wide ${
                  isActive ? "text-indigo-300" : "text-slate-400"
                }`}
              >
                {isActive && (
                  <motion.span
                    layoutId="home-mobile-tab"
                    className="absolute inset-1 -z-10 rounded-2xl border border-indigo-400/25 bg-indigo-500/18"
                  />
                )}
                <tab.icon className="h-[19px] w-[19px]" />
                <span>{tab.label}</span>
              </Link>
            );
          })}

          <button
            onClick={() => setMobileOpen(true)}
            aria-expanded={mobileOpen ? "true" : "false"}
            aria-label="Open quick menu"
            className={`relative flex h-full flex-1 flex-col items-center justify-center gap-0.5 rounded-2xl text-[10px] font-semibold tracking-wide ${
              mobileOpen ? "text-indigo-300" : "text-slate-400"
            }`}
          >
            {mobileOpen && <span className="absolute inset-1 -z-10 rounded-2xl border border-indigo-400/25 bg-indigo-500/18" />}
            <Menu className="h-[19px] w-[19px]" />
            <span>Menu</span>
          </button>
        </nav>
      </div>

      <main className="touch-pan-y relative z-10 overscroll-y-contain">
        {/* ── Hero ──────────────────────────────────── */}
        <section ref={heroRef} className="relative flex min-h-[100dvh] flex-col items-center justify-center overflow-hidden px-5 pb-20 pt-28 sm:pt-32">
          <motion.div style={{ y: heroY, opacity: heroOpacity }} className="flex flex-col items-center text-center max-w-5xl mx-auto">
            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="mb-6 inline-flex items-center gap-2 rounded-full border border-indigo-500/25 bg-indigo-500/8 px-4 py-1.5 text-xs font-semibold text-indigo-300 backdrop-blur-sm"
            >
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-indigo-400" />
              Now with autonomous scheduling agents
              <ChevronRight className="h-3 w-3 text-indigo-400/60" />
            </motion.div>

            {/* Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="font-serif text-[2.8rem] font-black leading-[1.04] tracking-[-0.04em] text-white sm:text-6xl lg:text-[5rem]"
            >
              Your calendar,{" "}
              <span className="relative inline-block">
                <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400 bg-clip-text text-transparent">
                  finally smart.
                </span>
                <svg className="absolute -bottom-1 left-0 w-full" viewBox="0 0 300 8" fill="none">
                  <path d="M2 6 C60 2, 120 7, 180 4 C240 1, 280 5, 298 5" stroke="url(#ug)" strokeWidth="2" strokeLinecap="round" />
                  <defs>
                    <linearGradient id="ug" x1="0" y1="0" x2="300" y2="0" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#818cf8" /><stop offset="1" stopColor="#a78bfa" />
                    </linearGradient>
                  </defs>
                </svg>
              </span>
            </motion.h1>

            {/* Subheading */}
            <motion.p
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.22 }}
              className="mt-6 max-w-xl text-balance text-base leading-relaxed text-slate-400 sm:text-lg"
            >
              GraftAI eliminates the scheduling chaos — timezone juggling, double bookings, the endless back-and-forth — so you just show up.
            </motion.p>

            {/* CTAs */}
            <motion.div
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.34 }}
              className="mt-9 flex flex-col items-center gap-3 sm:flex-row"
            >
              <Link
                href="/register"
                className="group relative flex items-center gap-2.5 overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-500 to-violet-500 px-7 py-3.5 text-sm font-bold text-white shadow-2xl shadow-indigo-500/25 transition-all hover:-translate-y-0.5 hover:shadow-indigo-500/40 active:translate-y-0"
              >
                <span>Start for free</span>
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
              </Link>
              <Link
                href="/login"
                className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/4 px-7 py-3.5 text-sm font-semibold text-slate-300 backdrop-blur-sm transition-all hover:border-white/20 hover:text-white hover:bg-white/8"
              >
                Sign in to dashboard
                <ChevronRight className="h-4 w-4 opacity-50" />
              </Link>
            </motion.div>

            {/* Social proof strip */}
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.5 }}
              className="mt-8 flex items-center gap-3 text-xs text-slate-500"
            >
              <div className="flex -space-x-2">
                {["MC", "DR", "AO", "JK", "PL"].map((initials, i) => (
                  <div key={i} className="flex h-6 w-6 items-center justify-center rounded-full border border-slate-700/80 bg-gradient-to-br from-slate-700 to-slate-800 text-[8px] font-bold text-slate-300">
                    {initials}
                  </div>
                ))}
              </div>
              <span>Trusted by <span className="text-slate-300 font-semibold">12,000+</span> teams worldwide</span>
            </motion.div>
          </motion.div>

          {/* Dashboard mockup */}
          <motion.div
            initial={{ opacity: 0, y: 60, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.9, delay: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="relative mx-auto mt-14 w-full max-w-3xl px-4"
          >
            <div className="relative rounded-2xl border border-white/[0.06] bg-slate-900/60 p-1 shadow-2xl shadow-black/60 backdrop-blur-xl ring-1 ring-white/[0.04]">
              {/* Window chrome */}
              <div className="flex items-center gap-1.5 rounded-xl bg-slate-950/70 px-4 py-2.5">
                <div className="h-2.5 w-2.5 rounded-full bg-rose-500/50" />
                <div className="h-2.5 w-2.5 rounded-full bg-amber-500/50" />
                <div className="h-2.5 w-2.5 rounded-full bg-emerald-500/50" />
                <div className="ml-3 h-3.5 flex-1 rounded-full bg-slate-800/60 max-w-[180px]" />
              </div>

              <div className="mt-1 rounded-xl bg-slate-950/40 p-5">
                {/* Calendar header */}
                <div className="mb-4 flex items-center justify-between">
                  <div className="h-4 w-24 rounded-md bg-slate-800/70" />
                  <div className="flex gap-2">
                    <div className="h-7 w-20 rounded-lg bg-indigo-500/20 border border-indigo-500/30" />
                    <div className="h-7 w-7 rounded-lg bg-slate-800/60" />
                  </div>
                </div>

                {/* Cal grid */}
                <div className="grid grid-cols-7 gap-1 text-center">
                  {["S","M","T","W","T","F","S"].map((d, i) => (
                    <div key={i} className="py-1 text-[10px] font-bold text-slate-600">{d}</div>
                  ))}
                  {Array.from({ length: 35 }, (_, i) => {
                    const isEvent = [8, 12, 15, 20, 22].includes(i);
                    const isToday = i === 14;
                    const isSelected = i === 12;
                    return (
                      <div
                        key={i}
                        className={`aspect-square rounded-lg flex items-center justify-center text-[11px] font-medium transition-all ${
                          isSelected ? "bg-indigo-500 text-white shadow-md shadow-indigo-500/40"
                          : isToday ? "border border-indigo-500/40 text-indigo-400"
                          : isEvent ? "bg-slate-800/50 text-slate-300"
                          : "text-slate-700"
                        }`}
                      >
                        {i > 2 ? i - 2 : ""}
                      </div>
                    );
                  })}
                </div>

                {/* AI suggestion chip */}
                <div className="mt-4 flex items-start gap-3 rounded-xl border border-indigo-500/20 bg-indigo-500/8 p-3">
                  <Sparkles className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-indigo-400" />
                  <div>
                    <p className="text-[11px] font-bold text-indigo-300">AI suggests Tuesday 2–3 PM</p>
                    <p className="text-[10px] leading-snug text-slate-500">Best overlap across NYC, London & Singapore</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Floating badges */}
            <motion.div
              animate={{ y: [-5, 5, -5] }}
              transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
              className="absolute -right-3 -top-4 hidden sm:flex items-center gap-2 rounded-2xl border border-emerald-500/25 bg-[#070711]/90 backdrop-blur-xl px-3.5 py-2.5 shadow-2xl"
            >
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              <span className="text-[11px] font-bold text-emerald-300">No conflicts found</span>
            </motion.div>
            <motion.div
              animate={{ y: [5, -5, 5] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 1 }}
              className="absolute -left-3 bottom-10 hidden sm:flex items-center gap-2 rounded-2xl border border-violet-500/25 bg-[#070711]/90 backdrop-blur-xl px-3.5 py-2.5 shadow-2xl"
            >
              <Clock className="h-3.5 w-3.5 text-violet-400" />
              <span className="text-[11px] font-bold text-violet-300">Saved 2.5 hrs this week</span>
            </motion.div>
          </motion.div>
        </section>

        {/* ── Logo strip ────────────────────────────── */}
        <section className="border-y border-white/[0.04] bg-white/[0.015] py-10 backdrop-blur-sm overflow-hidden">
          <p className="text-center text-[11px] font-bold uppercase tracking-[0.2em] text-slate-600 mb-7">
            Trusted by teams at
          </p>
          <div className="touch-pan-x -mx-5 overflow-x-auto px-5 md:mx-0 md:overflow-visible md:px-6">
            <div className="mx-auto flex w-max min-w-full items-center justify-start gap-8 px-1 md:w-auto md:min-w-0 md:flex-wrap md:justify-center md:gap-10 md:px-0">
            {LOGOS.map((logo) => (
              <span key={logo} className="snap-start shrink-0 rounded-xl border border-white/[0.06] bg-white/[0.02] px-4 py-2 text-sm font-bold tracking-wide text-slate-600 transition-colors hover:text-slate-400 md:border-0 md:bg-transparent md:px-0 md:py-0">
                {logo}
              </span>
            ))}
            </div>
          </div>
        </section>

        {/* ── Stats ─────────────────────────────────── */}
        <section className="py-20 px-5">
          <div className="mx-auto grid max-w-4xl grid-cols-2 gap-6 sm:grid-cols-4">
            {STATS.map((s, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.07 }}
                className="flex flex-col items-center gap-2 text-center p-6 rounded-2xl border border-white/[0.05] bg-white/[0.015] hover:bg-white/[0.03] hover:border-white/[0.08] transition-all group"
              >
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 group-hover:bg-indigo-500/15 transition-colors">
                  {s.icon}
                </div>
                <span className="font-serif text-3xl font-black text-white sm:text-4xl">
                  {s.value}
                </span>
                <span className="text-xs font-medium text-slate-500">{s.label}</span>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ── Features Bento ────────────────────────── */}
        <section id="features" className="mx-auto max-w-6xl px-5 py-10 pb-28">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-14 max-w-xl"
          >
            <p className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-indigo-400">What you get</p>
            <h2 className="font-serif text-4xl font-black leading-tight text-white sm:text-5xl">
              Built around how people actually work
            </h2>
            <p className="mt-4 text-base leading-relaxed text-slate-400">
              We spent a long time talking to engineers, founders, and operators before writing a single line of product code.
            </p>
          </motion.div>

          <div className="grid gap-4 md:grid-cols-3">
            {FEATURES_BENTO.map((f, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: (i % 3) * 0.07 }}
                whileHover={{ y: -4, transition: { duration: 0.2 } }}
                className={`group relative overflow-hidden rounded-2xl border bg-gradient-to-br p-6 transition-all hover:shadow-2xl hover:shadow-black/40 ${f.colspan} ${f.bg} ${f.border}`}
              >
                <div className={`mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900/70 border border-white/5 ${f.accent}`}>
                  {f.icon}
                </div>
                <span className={`inline-flex mb-2 rounded-full border px-2 py-0.5 text-[9px] font-black uppercase tracking-[0.15em] ${f.border} ${f.accent} bg-slate-900/40`}>
                  {f.tag}
                </span>
                <h3 className="mt-1 text-[15px] font-bold text-white leading-snug">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">{f.desc}</p>
                {f.visual}
              </motion.div>
            ))}
          </div>
        </section>

        {/* ── Testimonials ──────────────────────────── */}
        <section className="border-y border-white/[0.04] bg-white/[0.01] py-24 px-5">
          <div className="mx-auto max-w-6xl">
            <motion.div
              initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }} className="mb-14 text-center"
            >
              <p className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-indigo-400">In their own words</p>
              <h2 className="font-serif text-3xl font-black text-white sm:text-4xl">
                People seem to like it
              </h2>
            </motion.div>

            <div className="grid gap-5 sm:grid-cols-3">
              {TESTIMONIALS.map((t, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }} transition={{ delay: i * 0.1 }}
                  className={`flex flex-col gap-4 rounded-2xl border border-white/[0.06] bg-gradient-to-br ${t.color} p-6 backdrop-blur-sm hover:border-white/[0.1] transition-all`}
                >
                  <div className="flex gap-0.5">
                    {Array.from({ length: t.stars }).map((_, j) => (
                      <Star key={j} className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                    ))}
                  </div>
                  <p className="flex-1 text-sm leading-relaxed text-slate-200">&ldquo;{t.quote}&rdquo;</p>
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500/40 to-violet-500/40 text-xs font-bold text-white border border-white/10">
                      {t.avatar}
                    </div>
                    <div>
                      <p className="text-[13px] font-semibold text-white">{t.name}</p>
                      <p className="text-[11px] text-slate-400">{t.role}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Pricing ──────────────────────────────── */}
        <section id="pricing" className="mx-auto max-w-6xl px-5 py-28">
          <div className="mb-16 text-center">
            <p className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-indigo-400">Pricing</p>
            <h2 className="font-serif text-4xl font-black text-white sm:text-5xl">
              Simple, transparent pricing.
            </h2>
            <p className="mt-4 text-base text-slate-400 max-w-xl mx-auto">
              Start free. Upgrade when you&apos;re ready. No hidden fees, ever.
            </p>
          </div>

          <div className="grid gap-5 md:grid-cols-3 max-w-5xl mx-auto items-start">
            {PRICING_TIERS.map((pt, i) => (
              <motion.div
                key={pt.id}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className={`relative flex flex-col rounded-3xl p-7 transition-all ${
                  pt.highlight
                    ? "bg-gradient-to-b from-slate-800/80 to-slate-900/80 border border-indigo-500/40 shadow-2xl shadow-indigo-500/10 ring-1 ring-indigo-500/20"
                    : "bg-slate-900/30 border border-white/[0.06] hover:border-white/[0.1]"
                }`}
              >
                {pt.highlight && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-3.5 py-1 bg-gradient-to-r from-indigo-500 to-violet-500 text-white text-[10px] font-black uppercase tracking-wider rounded-full shadow-lg">
                    Most Popular
                  </div>
                )}

                <div className="flex items-center gap-2.5 mb-5">
                  <div className="p-2 rounded-xl bg-slate-950/60 border border-white/[0.06]">
                    {pt.icon}
                  </div>
                  <h3 className="text-lg font-bold text-white">{pt.name}</h3>
                </div>

                <div className="flex items-end gap-1.5 mb-2">
                  <span className="text-4xl font-black text-white">{pt.price}</span>
                  {pt.per && <span className="text-slate-500 text-sm mb-1">{pt.per}</span>}
                </div>
                <p className="text-[13px] text-slate-400 mb-7 leading-relaxed">{pt.description}</p>

                <div className="flex-1 space-y-3.5 mb-8">
                  {pt.features.map((feat) => (
                    <div key={feat} className="flex gap-3 text-sm text-slate-300">
                      <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                      {feat}
                    </div>
                  ))}
                </div>

                <Link
                  href={pt.href}
                  className={`w-full py-3.5 rounded-xl text-center text-sm font-bold transition-all active:scale-[0.98] ${
                    pt.highlight
                      ? "bg-gradient-to-r from-indigo-500 to-violet-500 text-white shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/40 hover:-translate-y-px"
                      : "bg-white/5 border border-white/10 text-white hover:bg-white/10"
                  }`}
                >
                  {pt.cta}
                </Link>
              </motion.div>
            ))}
          </div>

          <p className="mt-8 text-center text-xs text-slate-600">
            All plans include a 14-day money-back guarantee. No credit card required for Standard.
          </p>
        </section>

        {/* ── FAQ ───────────────────────────────────── */}
        <section id="faq" className="mx-auto max-w-3xl px-5 pb-28">
          <motion.div
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} className="mb-12 text-center"
          >
            <p className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-indigo-400">FAQ</p>
            <h2 className="font-serif text-3xl font-black text-white sm:text-4xl">
              Common questions
            </h2>
          </motion.div>

          <div className="space-y-2">
            {FAQS.map((faq, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }} transition={{ delay: i * 0.05 }}
                className="rounded-2xl border border-white/[0.06] bg-white/[0.02] overflow-hidden"
              >
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left text-sm font-semibold text-slate-200 hover:text-white transition-colors"
                >
                  <span>{faq.q}</span>
                  <ChevronDown className={`h-4 w-4 shrink-0 text-slate-500 transition-transform duration-200 ${openFaq === i ? "rotate-180" : ""}`} />
                </button>
                <AnimatePresence>
                  {openFaq === i && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <p className="px-5 pb-4 text-sm leading-relaxed text-slate-400">{faq.a}</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ── CTA Banner ───────────────────────────── */}
        <section className="mx-auto max-w-6xl px-5 pb-32">
          <motion.div
            initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="relative overflow-hidden rounded-3xl border border-indigo-500/20 bg-gradient-to-br from-indigo-600/12 via-slate-900/60 to-violet-600/10 p-10 text-center sm:p-16"
          >
            <div className="pointer-events-none absolute inset-0">
              <div className="absolute left-1/4 top-0 h-64 w-64 rounded-full bg-indigo-500/10 blur-3xl" />
              <div className="absolute bottom-0 right-1/4 h-64 w-64 rounded-full bg-violet-500/10 blur-3xl" />
            </div>
            <div className="relative">
              <p className="mb-4 text-xs font-bold uppercase tracking-[0.2em] text-indigo-400">Get access</p>
              <h2 className="font-serif mb-5 text-4xl font-black text-white sm:text-5xl">
                Ready to reclaim your time?
              </h2>
              <p className="mx-auto mb-9 max-w-md text-base leading-relaxed text-slate-400">
                Free to start. No credit card. Cancel literally whenever.
              </p>
              <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
                <Link
                  href="/register"
                  className="group flex items-center gap-2.5 rounded-2xl bg-gradient-to-r from-indigo-500 to-violet-500 px-8 py-4 text-sm font-bold text-white shadow-2xl shadow-indigo-500/25 transition-all hover:-translate-y-0.5 hover:shadow-indigo-500/40"
                >
                  Create free account
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                </Link>
                <Link
                  href="/login"
                  className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/4 px-8 py-4 text-sm font-semibold text-slate-300 backdrop-blur-sm transition-all hover:border-white/20 hover:text-white"
                >
                  Already have an account
                  <ChevronRight className="h-4 w-4 opacity-50" />
                </Link>
              </div>
              <p className="mt-7 flex flex-wrap items-center justify-center gap-4 text-xs text-slate-600">
                {["Free plan forever", "No CC required", "Cancel anytime", "14-day Pro trial"].map((item) => (
                  <span key={item} className="flex items-center gap-1.5">
                    <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                    {item}
                  </span>
                ))}
              </p>
            </div>
          </motion.div>
        </section>
      </main>

      {/* ── Footer ──────────────────────────────────── */}
      <footer className="border-t border-white/[0.04] py-14">
        <div className="mx-auto max-w-6xl px-5">
          <div className="flex flex-col items-center justify-between gap-8 md:flex-row md:items-start">
            <div>
              <Link href="/" className="flex items-center gap-2.5 group mb-3">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 shadow-md shadow-indigo-500/20">
                  <Zap className="w-3.5 h-3.5 text-white fill-white" />
                </div>
                <span className="font-serif text-sm font-bold text-slate-300">
                  GraftAI
                </span>
              </Link>
              <p className="text-xs text-slate-600 max-w-[200px] leading-relaxed">
                AI-powered scheduling for humans who have better things to do.
              </p>
            </div>

            <div className="flex flex-wrap justify-center gap-x-10 gap-y-4 text-xs font-medium text-slate-500 md:justify-end">
              <div className="flex flex-col gap-3">
                <span className="text-[10px] font-bold uppercase tracking-widest text-slate-600">Product</span>
                <Link href="#features" className="hover:text-slate-300 transition-colors">Features</Link>
                <Link href="#pricing" className="hover:text-slate-300 transition-colors">Pricing</Link>
                <Link href="#faq" className="hover:text-slate-300 transition-colors">FAQ</Link>
              </div>
              <div className="flex flex-col gap-3">
                <span className="text-[10px] font-bold uppercase tracking-widest text-slate-600">Account</span>
                <Link href="/login" className="hover:text-slate-300 transition-colors">Sign in</Link>
                <Link href="/register" className="hover:text-slate-300 transition-colors">Register</Link>
                <Link href="/dashboard" className="hover:text-slate-300 transition-colors">Dashboard</Link>
              </div>
              <div className="flex flex-col gap-3">
                <span className="text-[10px] font-bold uppercase tracking-widest text-slate-600">Legal</span>
                <Link href="/privacy-policy" className="hover:text-slate-300 transition-colors">Privacy Policy</Link>
                <Link href="/terms-of-service" className="hover:text-slate-300 transition-colors">Terms of Service</Link>
              </div>
            </div>
          </div>

          <div className="mt-10 pt-6 border-t border-white/[0.04] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-700">
            <span>© 2026 GraftAI. All rights reserved.</span>
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>All systems operational</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
