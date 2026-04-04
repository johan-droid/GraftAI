"use client";

import Link from "next/link";
import { useState, useEffect, useRef } from "react";
import { motion, useScroll, useTransform, AnimatePresence } from "framer-motion";
import {
  Bot,
  Sparkles,
  Globe,
  Zap,
  Lock,
  ChevronRight,
  ArrowRight,
  CheckCircle2,
  Clock,
  Star,
  Menu,
  X,
  Play,
  Shield,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

// ─── tiny noise svg as data url ───
const NOISE_SVG = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='0.08'/%3E%3C/svg%3E")`;

const FEATURES = [
  {
    icon: <Bot className="w-5 h-5" />,
    title: "AI that actually listens",
    desc: "Not another chatbot. A real scheduling brain that remembers context, tracks your preferences, and handles the back-and-forth so you don't have to.",
    tag: "Copilot",
    color: "from-violet-500/10 to-indigo-500/5",
    accent: "text-violet-400",
    border: "border-violet-500/20",
  },
  {
    icon: <Globe className="w-5 h-5" />,
    title: "Timezones, handled.",
    desc: "\"What time works for you?\" — a question you'll never dread again. GraftAI finds the overlap and proposes it instantly.",
    tag: "Global",
    color: "from-blue-500/10 to-cyan-500/5",
    accent: "text-blue-400",
    border: "border-blue-500/20",
  },
  {
    icon: <Lock className="w-5 h-5" />,
    title: "Your data, your rules",
    desc: "Passkey auth, granular consent controls, zero third-party trackers. We're building the scheduler we'd want to use ourselves.",
    tag: "Privacy",
    color: "from-emerald-500/10 to-teal-500/5",
    accent: "text-emerald-400",
    border: "border-emerald-500/20",
  },
  {
    icon: <Zap className="w-5 h-5" />,
    title: "Live calendar sync",
    desc: "Changes propagate instantly. No stale data, no double bookings. Just a calendar that stays true to your life in real time.",
    tag: "Realtime",
    color: "from-amber-500/10 to-orange-500/5",
    accent: "text-amber-400",
    border: "border-amber-500/20",
  },
  {
    icon: <Sparkles className="w-5 h-5" />,
    title: "Proactive, not reactive",
    desc: "Before you even open the app, GraftAI has already flagged your tight Tuesdays and suggested buffer time after the big presentation.",
    tag: "Proactive",
    color: "from-rose-500/10 to-pink-500/5",
    accent: "text-rose-400",
    border: "border-rose-500/20",
  },
  {
    icon: <Shield className="w-5 h-5" />,
    title: "Enterprise-ready",
    desc: "SSO, MFA, RBAC, custom domains. Everything your IT team needs to say yes. Nothing they don't.",
    tag: "Enterprise",
    color: "from-slate-500/10 to-slate-600/5",
    accent: "text-slate-400",
    border: "border-slate-500/20",
  },
];

const TESTIMONIALS = [
  {
    quote: "We cut scheduling overhead by half in the first week. Feels almost unfair.",
    name: "Mia Chen",
    role: "Eng Lead @ Stripe",
    avatar: "MC",
    stars: 5,
  },
  {
    quote: "Finally a calendar tool that doesn't feel like it was designed by a committee.",
    name: "Dev Ramirez",
    role: "Solo founder",
    avatar: "DR",
    stars: 5,
  },
  {
    quote: "The timezone handling alone is worth the price. Our distributed team swears by it.",
    name: "Anaya Osei",
    role: "Head of Ops @ Linear",
    avatar: "AO",
    stars: 5,
  },
];

const STATS = [
  { value: "40%", label: "less time scheduling" },
  { value: "12k+", label: "active teams" },
  { value: "99.9%", label: "uptime" },
  { value: "4.9★", label: "avg rating" },
];

export default function Home() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ["start start", "end start"] });
  const heroY = useTransform(scrollYProgress, [0, 1], ["0%", "30%"]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.6], [1, 0]);
  const { toast } = useToast();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const handleWaitlist = () => {
    toast.success("You're on the list! We'll reach out soon ✦");
  };

  return (
    <div
      className="min-h-screen bg-[#070711] text-slate-200 overflow-x-hidden"
      style={{ fontFamily: "'DM Sans', 'Inter', system-ui, sans-serif" }}
    >
      {/* ── Ambient bg ── */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -top-[30%] left-[10%] h-[600px] w-[600px] rounded-full bg-indigo-600/10 blur-[120px]" />
        <div className="absolute top-[40%] right-[-10%] h-[500px] w-[500px] rounded-full bg-violet-600/8 blur-[100px]" />
        <div className="absolute bottom-0 left-[30%] h-[400px] w-[400px] rounded-full bg-blue-600/6 blur-[100px]" />
        {/* Noise overlay */}
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{ backgroundImage: NOISE_SVG, backgroundRepeat: "repeat" }}
        />
        {/* Grid lines */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(148,163,184,1) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,1) 1px, transparent 1px)",
            backgroundSize: "80px 80px",
          }}
        />
      </div>

      {/* ── Nav ── */}
      <header
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrolled
            ? "bg-[#070711]/90 backdrop-blur-xl border-b border-slate-800/50 shadow-2xl shadow-black/20"
            : ""
        }`}
      >
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/20 group-hover:shadow-indigo-500/40 transition-shadow">
              <span className="text-sm font-black text-white leading-none">G</span>
            </div>
            <span
              className="text-base font-bold tracking-tight text-white"
              style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}
            >
              GraftAI
            </span>
          </Link>

          <div className="hidden items-center gap-8 md:flex">
            {['Features', 'Pricing', 'Changelog'].map((item) => (
              <Link
                key={item}
                href={`#${item.toLowerCase()}`}
                className="text-sm font-medium text-slate-400 transition-colors hover:text-white"
              >
                {item}
              </Link>
            ))}
          </div>

          <div className="hidden items-center gap-3 md:flex">
            <Link
              href="/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-slate-300 transition-colors hover:text-white"
            >
              Sign in
            </Link>
            <Link
              href="/register"
              className="rounded-xl bg-white px-4 py-2 text-sm font-semibold text-slate-900 transition-all hover:bg-slate-100 shadow-lg"
            >
              Get started free
            </Link>
          </div>

          <button
            className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-800/50 hover:text-white md:hidden"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </nav>

        {/* Mobile menu */}
        <AnimatePresence>
          {mobileOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden border-t border-slate-800/50 bg-[#070711]/95 backdrop-blur-xl md:hidden"
            >
              <div className="flex flex-col gap-1 p-4">
                {['Features', 'Pricing', 'Changelog'].map((item) => (
                  <Link
                    key={item}
                    href={`#${item.toLowerCase()}`}
                    onClick={() => setMobileOpen(false)}
                    className="rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800/50 hover:text-white"
                  >
                    {item}
                  </Link>
                ))}
                <div className="mt-3 flex flex-col gap-2 border-t border-slate-800/50 pt-3">
                  <Link
                    href="/login"
                    className="rounded-xl border border-slate-700/50 px-4 py-3 text-center text-sm font-medium text-slate-300"
                  >
                    Sign in
                  </Link>
                  <Link
                    href="/register"
                    className="rounded-xl bg-white px-4 py-3 text-center text-sm font-semibold text-slate-900"
                  >
                    Get started free
                  </Link>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      <main className="relative z-10">
        {/* ── Hero ── */}
        <section
          ref={heroRef}
          className="relative flex min-h-[100dvh] flex-col items-center justify-center overflow-hidden px-5 pb-16 pt-32"
        >
          <motion.div style={{ y: heroY, opacity: heroOpacity }} className="flex flex-col items-center text-center">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="mb-8 inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/8 px-4 py-1.5 text-xs font-semibold text-indigo-300 backdrop-blur-sm"
            >
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-indigo-400" />
              Now with autonomous scheduling agents
              <ChevronRight className="h-3 w-3 text-indigo-400/60" />
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.2 }}
              className="max-w-4xl text-balance text-[2.6rem] font-black leading-[1.05] tracking-[-0.03em] text-white sm:text-6xl lg:text-7xl"
              style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}
            >
              Your calendar,{' '}
              <span className="relative inline-block">
                <span className="relative z-10 bg-gradient-to-r from-indigo-400 via-violet-400 to-indigo-300 bg-clip-text text-transparent">
                  finally smart.
                </span>
                <svg
                  className="absolute -bottom-2 left-0 w-full"
                  viewBox="0 0 300 12"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M3 9 C60 3, 120 11, 180 6 C240 1, 280 8, 297 7"
                    stroke="url(#underline-grad)"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    fill="none"
                  />
                  <defs>
                    <linearGradient id="underline-grad" x1="0" y1="0" x2="300" y2="0" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#818cf8" />
                      <stop offset="1" stopColor="#a78bfa" />
                    </linearGradient>
                  </defs>
                </svg>
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.35 }}
              className="mt-7 max-w-xl text-balance text-base leading-relaxed text-slate-400 sm:text-lg"
            >
              GraftAI handles the scheduling chaos — timezone juggling, double bookings, the endless
              back-and-forth — so you can just show up to things that matter.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.5 }}
              className="mt-10 flex flex-col items-center gap-3 sm:flex-row sm:gap-4"
            >
              <Link
                href="/register"
                className="group relative flex items-center gap-2.5 overflow-hidden rounded-2xl bg-white px-7 py-3.5 text-sm font-bold text-slate-900 shadow-xl transition-all hover:-translate-y-0.5 hover:shadow-2xl hover:shadow-white/10"
              >
                Start for free
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
              <button
                onClick={handleWaitlist}
                className="flex items-center gap-2 rounded-2xl border border-slate-700/60 bg-white/4 px-7 py-3.5 text-sm font-semibold text-slate-300 backdrop-blur-sm transition-all hover:border-slate-600 hover:text-white hover:bg-white/8"
              >
                <Play className="h-3.5 w-3.5" />
                Watch demo
              </button>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.7 }}
              className="mt-8 flex items-center gap-3 text-xs text-slate-500"
            >
              <div className="flex -space-x-2">
                {['MC', 'DR', 'AO', 'JK', 'PL'].map((initials, i) => (
                  <div
                    key={i}
                    className="flex h-6 w-6 items-center justify-center rounded-full border border-slate-800 bg-gradient-to-br from-slate-700 to-slate-800 text-[9px] font-bold text-slate-300"
                  >
                    {initials}
                  </div>
                ))}
              </div>
              <span>Trusted by 12,000+ teams worldwide</span>
            </motion.div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 60, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 1, delay: 0.6, ease: [0.22, 1, 0.36, 1] }}
            className="relative mx-auto mt-16 w-full max-w-3xl px-4"
          >
            <div className="relative rounded-2xl border border-slate-700/40 bg-slate-900/60 p-1 shadow-2xl shadow-black/60 backdrop-blur-xl ring-1 ring-white/5">
              <div className="flex items-center gap-1.5 rounded-xl bg-slate-950/60 px-4 py-3">
                <div className="h-2.5 w-2.5 rounded-full bg-rose-500/60" />
                <div className="h-2.5 w-2.5 rounded-full bg-amber-500/60" />
                <div className="h-2.5 w-2.5 rounded-full bg-emerald-500/60" />
                <div className="ml-3 h-4 flex-1 rounded bg-slate-800/60" />
              </div>

              <div className="mt-1 rounded-xl bg-slate-950/40 p-5">
                <div className="mb-4 flex items-center justify-between">
                  <div className="h-4 w-28 rounded bg-slate-800/80" />
                  <div className="flex gap-2">
                    <div className="h-6 w-6 rounded bg-slate-800/60" />
                    <div className="h-6 w-6 rounded bg-slate-800/60" />
                  </div>
                </div>
                <div className="grid grid-cols-7 gap-1 text-center">
                  {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((d) => (
                    <div key={d} className="py-1 text-[10px] font-semibold text-slate-600">{d}</div>
                  ))}
                  {Array.from({ length: 35 }, (_, i) => {
                    const isEvent = [8, 12, 15, 20, 22].includes(i);
                    const isToday = i === 14;
                    const isSelected = i === 12;
                    return (
                      <div
                        key={i}
                        className={`aspect-square rounded-xl flex items-center justify-center text-xs font-medium transition-all ${
                          isSelected
                            ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/30'
                            : isToday
                            ? 'border border-indigo-500/40 text-indigo-400'
                            : isEvent
                            ? 'bg-slate-800/60 text-slate-300'
                            : 'text-slate-600'
                        }`}
                      >
                        {i > 2 ? i - 2 : ''}
                        {isEvent && !isSelected && (
                          <span className="absolute mt-5 h-1 w-1 rounded-full bg-indigo-400" />
                        )}
                      </div>
                    );
                  })}
                </div>

                <div className="mt-4 flex items-start gap-3 rounded-xl border border-indigo-500/20 bg-indigo-500/8 p-3">
                  <Sparkles className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-indigo-400" />
                  <div>
                    <p className="text-[11px] font-semibold text-indigo-300">AI suggests Tuesday 2–3pm</p>
                    <p className="text-[10px] leading-snug text-slate-500">
                      Best overlap for all attendees across NYC, London & Singapore
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <motion.div
              animate={{ y: [-4, 4, -4] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute -right-4 -top-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-[11px] font-bold text-emerald-400 shadow-xl backdrop-blur-sm hidden sm:flex items-center gap-1.5"
            >
              <CheckCircle2 className="h-3 w-3" /> No conflicts found
            </motion.div>
            <motion.div
              animate={{ y: [4, -4, 4] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
              className="absolute -left-4 bottom-8 rounded-2xl border border-violet-500/20 bg-violet-500/10 px-3 py-2 text-[11px] font-bold text-violet-400 shadow-xl backdrop-blur-sm hidden sm:flex items-center gap-1.5"
            >
              <Clock className="h-3 w-3" /> Saved 2.5 hrs this week
            </motion.div>
          </motion.div>
        </section>

        <section className="relative border-y border-slate-800/40 bg-slate-900/20 py-14 backdrop-blur-sm">
          <div className="mx-auto grid max-w-4xl grid-cols-2 gap-8 px-5 sm:grid-cols-4">
            {STATS.map((s, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className="flex flex-col items-center gap-1 text-center"
              >
                <span
                  className="text-3xl font-black text-white sm:text-4xl"
                  style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}
                >
                  {s.value}
                </span>
                <span className="text-xs font-medium text-slate-500">{s.label}</span>
              </motion.div>
            ))}
          </div>
        </section>

        <section id="features" className="mx-auto max-w-6xl px-5 py-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-16 max-w-2xl"
          >
            <p className="mb-3 text-xs font-bold uppercase tracking-widest text-indigo-400">What you actually get</p>
            <h2
              className="text-4xl font-black text-white sm:text-5xl"
              style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}
            >
              Built around how people actually work
            </h2>
            <p className="mt-4 text-base leading-relaxed text-slate-400">
              We spent a long time talking to engineers, founders, and operators before writing a single line of product code. Here&apos;s what came out of that.
            </p>
          </motion.div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: (i % 3) * 0.08 }}
                whileHover={{ y: -3 }}
                className={`group relative overflow-hidden rounded-2xl border bg-gradient-to-br p-6 transition-all hover:shadow-xl ${f.color} ${f.border} hover:border-opacity-60`}
              >
                <div
                  className={`mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900/60 ${f.accent}`}
                >
                  {f.icon}
                </div>
                <div className="mb-2 flex items-start justify-between gap-2">
                  <h3 className="text-base font-bold text-white">{f.title}</h3>
                  <span className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${f.border} ${f.accent} bg-slate-900/40`}>
                    {f.tag}
                  </span>
                </div>
                <p className="text-sm leading-relaxed text-slate-400">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </section>

        <section className="border-y border-slate-800/30 bg-slate-900/15 py-20">
          <div className="mx-auto max-w-6xl px-5">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="mb-12 text-center"
            >
              <p className="mb-3 text-xs font-bold uppercase tracking-widest text-indigo-400">In their own words</p>
              <h2
                className="text-3xl font-black text-white sm:text-4xl"
                style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}
              >
                People seem to like it
              </h2>
            </motion.div>

            <div className="grid gap-5 sm:grid-cols-3">
              {TESTIMONIALS.map((t, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="flex flex-col gap-4 rounded-2xl border border-slate-700/30 bg-slate-900/40 p-6 backdrop-blur-sm"
                >
                  <div className="flex gap-0.5">
                    {Array.from({ length: t.stars }).map((_, j) => (
                      <Star key={j} className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                    ))}
                  </div>
                  <p className="flex-1 text-sm leading-relaxed text-slate-300">&ldquo;{t.quote}&rdquo;</p>
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500/30 to-violet-500/30 text-xs font-bold text-slate-200 border border-slate-700">
                      {t.avatar}
                    </div>
                    <div>
                      <p className="text-[13px] font-semibold text-white">{t.name}</p>
                      <p className="text-[11px] text-slate-500">{t.role}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-5 py-24">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="relative overflow-hidden rounded-3xl border border-indigo-500/15 bg-gradient-to-br from-indigo-600/10 via-slate-900/60 to-violet-600/8 p-10 text-center sm:p-16"
          >
            <div className="pointer-events-none absolute inset-0">
              <div className="absolute left-1/4 top-0 h-48 w-48 rounded-full bg-indigo-500/10 blur-3xl" />
              <div className="absolute bottom-0 right-1/4 h-48 w-48 rounded-full bg-violet-500/10 blur-3xl" />
            </div>

            <div className="relative">
              <p className="mb-4 text-xs font-bold uppercase tracking-widest text-indigo-400">Get access</p>
              <h2
                className="mb-5 text-4xl font-black text-white sm:text-5xl"
                style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}
              >
                Ready to reclaim your time?
              </h2>
              <p className="mx-auto mb-8 max-w-md text-base leading-relaxed text-slate-400">
                Free to start. No credit card. Cancel literally whenever.
              </p>

              <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
                <Link
                  href="/register"
                  className="group flex items-center gap-2.5 rounded-2xl bg-white px-8 py-4 text-sm font-bold text-slate-900 shadow-xl transition-all hover:-translate-y-0.5 hover:shadow-2xl"
                >
                  Create free account
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Link>
                <Link
                  href="/login"
                  className="flex items-center gap-2 rounded-2xl border border-slate-700/50 px-8 py-4 text-sm font-semibold text-slate-300 backdrop-blur-sm transition-all hover:border-slate-600 hover:text-white"
                >
                  Already have an account
                </Link>
              </div>

              <p className="mt-6 flex items-center justify-center gap-4 text-xs text-slate-600">
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3 text-emerald-500" /> Free plan forever
                </span>
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3 text-emerald-500" /> No CC required
                </span>
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3 text-emerald-500" /> Cancel anytime
                </span>
              </p>
            </div>
          </motion.div>
        </section>
      </main>

      <footer className="border-t border-slate-800/40 py-12">
        <div className="mx-auto max-w-6xl px-5">
          <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
            <div className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600">
                <span className="text-xs font-black text-white">G</span>
              </div>
              <span
                className="text-sm font-bold text-slate-400"
                style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}
              >
                GraftAI
              </span>
              <span className="text-xs text-slate-700">© 2026</span>
            </div>
            <div className="flex gap-6 text-xs font-medium text-slate-600">
              {['Privacy', 'Terms', 'Status', 'GitHub'].map((item) => (
                <Link key={item} href="#" className="transition-colors hover:text-slate-400">
                  {item}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
