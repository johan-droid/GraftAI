"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  Calendar,
  CheckCircle2,
  Clock,
  Menu,
  MessageSquare,
  ShieldCheck,
  Sparkles,
  Users,
  X,
  Zap,
  BarChart3,
  Bot,
  Globe,
} from "lucide-react";
import { BentoCard } from "@/components/landing/BentoCard";

/* ─── Data ─────────────────────────────────────────────────────────── */

const previewSteps = [
  { step: "01", title: "Share one link", text: "Invite people without the back-and-forth." },
  { step: "02", title: "Pick a time", text: "Availability stays readable and current." },
  { step: "03", title: "Confirm instantly", text: "Automated follow-up keeps the handoff calm." },
];

const liveSignals = [
  { label: "Real-time sync", title: "Calendars stay aligned", text: "Availability updates quietly as calendars change, so the page always feels current.", accent: "blue" as const },
  { label: "Confirmations", title: "Every booking gets a clear handoff", text: "The system answers with a polished confirmation state instead of a dead-end screen.", accent: "green" as const },
  { label: "Mobile flow", title: "Designed to breathe on phones", text: "Primary actions stay easy to find, tap, and understand on smaller screens.", accent: "amber" as const },
];

const automationFlow = [
  { step: "01", label: "Signal", title: "Listen for the event", text: "New bookings, changes, and webhook calls enter the same calm pipeline.", accent: "blue" as const, icon: Sparkles },
  { step: "02", label: "Decide", title: "Apply safe rules", text: "Confidence thresholds, approval states, and defaults keep the engine predictable.", accent: "green" as const, icon: ShieldCheck },
  { step: "03", label: "Act", title: "Execute the quiet action", text: "Send confirmations, reminders, or calendar updates with no extra noise.", accent: "amber" as const, icon: CheckCircle2 },
  { step: "04", label: "Audit", title: "Leave a readable trace", text: "Store a human-friendly execution trail so every run can be explained later.", accent: "red" as const, icon: MessageSquare },
] as const;

const faqItems = [
  { question: "Does this work well on mobile?", answer: "Yes. The layout is built mobile-first, with cards, CTAs, and spacing tuned to stay readable at phone widths." },
  { question: "Can we keep using our existing calendars?", answer: "GraftAI layers over your calendar tools — Google, Outlook, and iCloud all stay connected." },
  { question: "What happens after install?", answer: "The PWA opens into the dashboard flow, which makes the install experience feel more useful on first launch." },
  { question: "Is there a free plan?", answer: "Yes — the Standard plan gives you 10 AI messages per day, calendar sync, and all core scheduling features at no cost." },
];

const signalAccentStyles = {
  blue:  { badge: "border-[#D2E3FC] bg-[#E8F0FE] text-[#1967D2]", chip: "bg-[#1A73E8]" },
  green: { badge: "border-[#CDE7D6] bg-[#E6F4EA] text-[#137333]", chip: "bg-[#34A853]" },
  amber: { badge: "border-[#F9E0B5] bg-[#FEF7E0] text-[#E37400]", chip: "bg-[#E37400]" },
  red:   { badge: "border-[#F9E0E3] bg-[#FCE8E6] text-[#D93025]", chip: "bg-[#D93025]" },
} as const;

const marqueePills = [
  "Live sync", "Capsule UI", "One-link scheduling", "Instant confirmation",
  "Mobile-first", "Calendar-aware", "Polite follow-up", "AI copilot",
];

/* ─── Helpers ──────────────────────────────────────────────────────── */

function SectionHeader({ kicker, title, description }: { kicker: string; title: string; description: string }) {
  return (
    <motion.div
      className="max-w-2xl"
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.45 }}
    >
      <p className="inline-flex items-center rounded-full border border-[#D2E3FC] bg-white px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.28em] text-[#1967D2] shadow-sm">
        {kicker}
      </p>
      <h2 className="mt-4 text-2xl font-normal tracking-tight text-[#202124] sm:text-3xl lg:text-[2.1rem]">
        {title}
      </h2>
      <p className="mt-4 text-sm leading-relaxed text-[#5F6368] sm:text-base">
        {description}
      </p>
    </motion.div>
  );
}

/* ─── Page ─────────────────────────────────────────────────────────── */

export default function LandingPage() {
  const shouldReduceMotion = useReducedMotion();
  const [activeSignalIndex, setActiveSignalIndex] = useState(0);
  const [activePreviewIndex, setActivePreviewIndex] = useState(0);
  const [activeAutomationIndex, setActiveAutomationIndex] = useState(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const activeSignal = liveSignals[activeSignalIndex];
  const activeAutomation = automationFlow[activeAutomationIndex];

  useEffect(() => {
    if (shouldReduceMotion) return;
    const id = window.setInterval(() => {
      setActiveSignalIndex((i) => (i + 1) % liveSignals.length);
      setActivePreviewIndex((i) => (i + 1) % previewSteps.length);
      setActiveAutomationIndex((i) => (i + 1) % automationFlow.length);
    }, 3800);
    return () => window.clearInterval(id);
  }, [shouldReduceMotion]);

  const fadeUp = {
    initial: { opacity: 0, y: 18 },
    whileInView: { opacity: 1, y: 0 },
    viewport: { once: true, margin: "-60px" as const },
  };

  return (
    <div className="relative min-h-dvh overflow-hidden bg-[radial-gradient(circle_at_top_left,rgba(26,115,232,0.1),transparent_28%),radial-gradient(circle_at_top_right,rgba(52,168,83,0.06),transparent_24%),linear-gradient(180deg,#F8F9FA_0%,#FFFFFF_52%,#F8F9FA_100%)] text-[#202124] font-sans selection:bg-[#D2E3FC]">

      {/* ─── Ambient Glows ─── */}
      <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
        <motion.div
          animate={shouldReduceMotion ? undefined : { x: [0, 18, 0], y: [0, 10, 0], opacity: [0.08, 0.14, 0.08] }}
          transition={shouldReduceMotion ? undefined : { duration: 18, repeat: Infinity, ease: "easeInOut" }}
          className="absolute -top-24 left-[-8rem] h-80 w-80 rounded-full bg-[#1A73E8]/10 blur-3xl"
        />
        <motion.div
          animate={shouldReduceMotion ? undefined : { x: [0, -14, 0], y: [0, 16, 0], opacity: [0.06, 0.12, 0.06] }}
          transition={shouldReduceMotion ? undefined : { duration: 22, repeat: Infinity, ease: "easeInOut" }}
          className="absolute right-[-6rem] top-40 h-72 w-72 rounded-full bg-[#34A853]/10 blur-3xl"
        />
      </div>

      {/* ════════════════════════════════════════════════════════════
           NAVBAR
         ════════════════════════════════════════════════════════════ */}
      <div className="sticky top-0 z-50 px-4 pt-3 sm:px-6 sm:pt-4">
        <nav className="mx-auto max-w-7xl rounded-full border border-[#DADCE0] bg-white/92 px-4 py-2.5 shadow-[0_4px_24px_-8px_rgba(32,33,36,0.12)] backdrop-blur-2xl">
          <div className="flex items-center justify-between gap-3">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#1A73E8] text-xs font-bold text-white shadow-sm">G</div>
              <span className="text-lg font-medium tracking-tight text-[#202124]">GraftAI</span>
            </Link>

            {/* Desktop nav */}
            <div className="hidden md:flex items-center gap-1 rounded-full border border-[#DADCE0] bg-[#F8F9FA] p-1 text-sm font-medium text-[#5F6368]">
              {[
                { href: "#features", label: "Features" },
                { href: "#proof", label: "Proof" },
                { href: "#automation", label: "Automation" },
                { href: "#faq", label: "FAQ" },
                { href: "/pricing", label: "Pricing" },
              ].map((link) => (
                <Link key={link.href} href={link.href} className="rounded-full px-4 py-2 transition-colors hover:bg-white hover:text-[#202124] hover:shadow-sm">
                  {link.label}
                </Link>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <Link href="/login" className="hidden sm:inline-flex rounded-full border border-[#DADCE0] bg-white px-4 py-2 text-sm font-medium text-[#1A73E8] shadow-sm transition-colors hover:bg-[#F8F9FA]">
                Sign in
              </Link>
              <Link href="/signup" className="inline-flex items-center gap-1.5 rounded-full bg-[#1A73E8] px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-[#1557B0] sm:px-5">
                Get started
              </Link>
              {/* Mobile hamburger */}
              <button
                type="button"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 rounded-full hover:bg-[#F1F3F4] text-[#5F6368] transition-colors"
                aria-label="Toggle menu"
              >
                {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            </div>
          </div>

          {/* Mobile menu dropdown */}
          <AnimatePresence>
            {mobileMenuOpen && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="md:hidden overflow-hidden"
              >
                <div className="flex flex-col gap-1 pt-3 pb-2">
                  {[
                    { href: "#features", label: "Features" },
                    { href: "#proof", label: "Proof" },
                    { href: "#automation", label: "Automation" },
                    { href: "#faq", label: "FAQ" },
                    { href: "/pricing", label: "Pricing" },
                    { href: "/login", label: "Sign in" },
                  ].map((link) => (
                    <Link
                      key={link.href}
                      href={link.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className="rounded-xl px-4 py-2.5 text-sm font-medium text-[#5F6368] hover:bg-[#F1F3F4] hover:text-[#202124] transition-colors"
                    >
                      {link.label}
                    </Link>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </nav>
      </div>

      {/* ════════════════════════════════════════════════════════════
           HERO — Dynamic Bento Grid
         ════════════════════════════════════════════════════════════ */}
      <main className="mx-auto max-w-7xl px-4 pb-16 pt-8 sm:px-6 sm:pb-20 sm:pt-12">

        {/* Hero top row: 2-column on lg */}
        <div className="grid gap-5 lg:grid-cols-12 lg:items-start">

          {/* Left column: headline + CTA + live signal */}
          <motion.section
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="lg:col-span-5 flex flex-col gap-5"
          >
            {/* Badge */}
            <div className="inline-flex self-start items-center gap-2 rounded-full border border-[#D2E3FC] bg-white/90 px-3 py-1 text-xs font-medium text-[#1967D2] shadow-sm">
              <Sparkles size={14} />
              <span>Now in public beta</span>
            </div>

            {/* Headline */}
            <h1 className="max-w-lg text-[2.2rem] sm:text-5xl lg:text-[3.2rem] font-normal leading-[1.06] tracking-tight text-[#202124]">
              Scheduling that feels calmer, clearer, and more refined.
            </h1>

            {/* Sub */}
            <p className="max-w-md text-base leading-relaxed text-[#5F6368] sm:text-lg">
              GraftAI keeps meetings moving without the back-and-forth — handling routing,
              time zones, and confirmations automatically.
            </p>

            {/* CTA buttons */}
            <div className="flex flex-col gap-3 sm:flex-row">
              <Link href="/signup" className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-[#1A73E8] px-7 py-3.5 text-base font-medium text-white shadow-sm transition-all hover:bg-[#1557B0] hover:shadow-md sm:w-auto">
                Start for free <ArrowRight size={18} />
              </Link>
              <Link href="/docs" className="inline-flex w-full items-center justify-center rounded-full border border-[#DADCE0] bg-white px-7 py-3.5 text-base font-medium text-[#5F6368] transition-colors hover:bg-[#F8F9FA] sm:w-auto">
                Read the docs
              </Link>
            </div>

            {/* Live Signal Card */}
            <div className="rounded-3xl border border-[#DADCE0] bg-white/90 p-5 shadow-[0_2px_12px_-4px_rgba(32,33,36,0.12)] backdrop-blur-sm">
              <div className="flex items-center justify-between gap-3 mb-4">
                <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">Live signal</p>
                <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] ${signalAccentStyles[activeSignal.accent].badge}`}>
                  <span className={`h-1.5 w-1.5 rounded-full ${signalAccentStyles[activeSignal.accent].chip}`} />
                  Live
                </span>
              </div>

              <AnimatePresence mode="wait">
                <motion.div
                  key={activeSignal.title}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.25 }}
                >
                  <p className="text-lg font-medium text-[#202124]">{activeSignal.title}</p>
                  <p className="mt-1.5 text-sm leading-relaxed text-[#5F6368]">{activeSignal.text}</p>
                </motion.div>
              </AnimatePresence>

              <div className="mt-4 grid gap-2 grid-cols-3">
                {liveSignals.map((signal, index) => (
                  <button
                    key={signal.label}
                    type="button"
                    onClick={() => setActiveSignalIndex(index)}
                    className={`rounded-2xl border px-3 py-2.5 text-left transition-all ${
                      index === activeSignalIndex
                        ? `${signalAccentStyles[signal.accent].badge} shadow-sm`
                        : "border-[#DADCE0] bg-[#F8F9FA] hover:bg-white"
                    }`}
                  >
                    <p className="text-[9px] sm:text-[10px] font-semibold uppercase tracking-[0.2em] text-[#5F6368]">{signal.label}</p>
                  </button>
                ))}
              </div>
            </div>
          </motion.section>

          {/* Right column: Bento hero grid */}
          <motion.section
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.08 }}
            className="lg:col-span-7"
          >
            {/* 2×2 Dynamic Bento Grid */}
            <div className="grid gap-4 grid-cols-1 sm:grid-cols-2">

              {/* Large feature card — spans full width */}
              <BentoCard
                className="sm:col-span-2"
                tone="blue"
                eyebrow="Live preview"
                title="A calmer booking flow"
                description="The product story is shown in a compact rhythm: a clear path, less noise, and stronger hierarchy."
              >
                <div className="space-y-3">
                  <div className="rounded-2xl border border-[#DADCE0] bg-[#F8F9FA] p-4">
                    <div className="flex items-center justify-between gap-3 mb-3">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">
                        Step {previewSteps[activePreviewIndex].step}
                      </p>
                      <span className="rounded-full bg-white px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-[#1967D2] shadow-sm border border-[#D2E3FC]">
                        Auto-advancing
                      </span>
                    </div>
                    <AnimatePresence mode="wait">
                      <motion.div
                        key={previewSteps[activePreviewIndex].step}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -8 }}
                        transition={{ duration: 0.22 }}
                      >
                        <p className="text-lg font-medium text-[#202124]">{previewSteps[activePreviewIndex].title}</p>
                        <p className="mt-1.5 text-sm leading-relaxed text-[#5F6368]">{previewSteps[activePreviewIndex].text}</p>
                      </motion.div>
                    </AnimatePresence>
                  </div>

                  <div className="grid gap-2 grid-cols-3">
                    {previewSteps.map((step, index) => (
                      <button
                        key={step.step}
                        type="button"
                        onClick={() => setActivePreviewIndex(index)}
                        className={`rounded-2xl border p-3 text-left transition-all ${
                          index === activePreviewIndex
                            ? "border-[#D2E3FC] bg-[#E8F0FE] shadow-sm"
                            : "border-[#DADCE0] bg-white hover:bg-[#F8F9FA]"
                        }`}
                      >
                        <p className="text-[9px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">{step.step}</p>
                        <p className="mt-1.5 text-sm font-medium text-[#202124] leading-snug">{step.title}</p>
                      </button>
                    ))}
                  </div>
                </div>
              </BentoCard>

              {/* Two smaller cards */}
              <BentoCard
                tone="green"
                eyebrow="Always local"
                title="Time zones stay readable"
                description="Guests get a clear local-time experience instead of offset math."
                icon={Clock}
              />

              <BentoCard
                tone="amber"
                eyebrow="Routing"
                title="Teams get the right handoff"
                description="Requests move cleanly to the right person, transparently."
                icon={Users}
              />
            </div>
          </motion.section>
        </div>

        {/* Marquee */}
        <div className="mask-fade mt-8 overflow-hidden rounded-full border border-[#DADCE0] bg-white/85 px-2 py-2 shadow-sm">
          <div className={`flex w-max items-center gap-3 whitespace-nowrap ${shouldReduceMotion ? "" : "animate-marquee"}`}>
            {[...marqueePills, ...marqueePills].map((pill, index) => (
              <span key={`${pill}-${index}`} className="inline-flex items-center rounded-full border border-[#DADCE0] bg-white px-4 py-2 text-[11px] font-medium text-[#5F6368] shadow-sm">
                {pill}
              </span>
            ))}
          </div>
        </div>
      </main>

      {/* ════════════════════════════════════════════════════════════
           FEATURES — Asymmetric Bento Grid
         ════════════════════════════════════════════════════════════ */}
      <section id="features" className="border-y border-[#DADCE0]/80 bg-white/90 py-16 sm:py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <SectionHeader
            kicker="What gets better"
            title="Bento overview — product depth without the clutter."
            description="Each card surface maps to a real product capability, not marketing decoration."
          />

          {/* Asymmetric 3-col bento grid */}
          <div className="mt-10 grid gap-4 grid-cols-1 md:grid-cols-6">
            {/* Wide card */}
            <motion.div {...fadeUp} transition={{ duration: 0.4 }} className="md:col-span-4">
              <BentoCard
                tone="blue"
                eyebrow="Calendar sync"
                title="Keeps availability current"
                description="Google and Microsoft calendars stay aligned so the page never feels like a settings maze."
                icon={Calendar}
              >
                <div className="grid gap-2 grid-cols-3">
                  {["Live sync", "Conflict checks", "Clear confirmations"].map((b) => (
                    <div key={b} className="rounded-2xl border border-[#DADCE0] bg-[#F8F9FA] px-3 py-2.5 text-xs font-medium text-[#5F6368] text-center">
                      {b}
                    </div>
                  ))}
                </div>
              </BentoCard>
            </motion.div>

            {/* Narrow card */}
            <motion.div {...fadeUp} transition={{ duration: 0.4, delay: 0.05 }} className="md:col-span-2">
              <BentoCard tone="green" eyebrow="Routing" title="Finds the right host" description="Requests move to the right person without forcing the visitor to understand the org chart." icon={Users} />
            </motion.div>

            {/* Bottom row — 3 equal cards */}
            <motion.div {...fadeUp} transition={{ duration: 0.4, delay: 0.08 }} className="md:col-span-2">
              <BentoCard tone="amber" eyebrow="Timezones" title="Keeps local time obvious" description="Every invite resolves to a readable local-time experience." icon={Clock} />
            </motion.div>

            <motion.div {...fadeUp} transition={{ duration: 0.4, delay: 0.12 }} className="md:col-span-2">
              <BentoCard tone="violet" eyebrow="Follow-up" title="Sends polite reminders" description="The handoff stays polished and quiet instead of turning into a noisy chase." icon={MessageSquare} />
            </motion.div>

            <motion.div {...fadeUp} transition={{ duration: 0.4, delay: 0.16 }} className="md:col-span-2">
              <BentoCard tone="blue" eyebrow="AI Copilot" title="Chat to action" description="Ask your copilot to schedule, prep, or optimize — it reads your calendar context." icon={Bot} />
            </motion.div>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════
           PROOF — Mosaic Grid
         ════════════════════════════════════════════════════════════ */}
      <section id="proof" className="py-16 sm:py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <div className="grid gap-4 grid-cols-1 lg:grid-cols-12">

            {/* Wide proof card */}
            <motion.div {...fadeUp} transition={{ duration: 0.45 }} className="lg:col-span-7">
              <BentoCard
                tone="violet"
                eyebrow="Why it feels different"
                title="Structured, calm, and easy to scan."
                description="This section shows why the product feels more polished than a generic scheduling page."
              >
                <div className="grid gap-3 grid-cols-1 sm:grid-cols-3">
                  {[
                    { title: "Less coordination", text: "A single link replaces repeated message threads." },
                    { title: "Clear next step", text: "The page makes the action obvious within seconds." },
                    { title: "Thumb-friendly", text: "Primary actions stay accessible on small screens." },
                  ].map((item) => (
                    <div key={item.title} className="rounded-2xl border border-[#DADCE0] bg-[#F8F9FA] p-4">
                      <p className="text-sm font-medium text-[#202124]">{item.title}</p>
                      <p className="mt-1 text-sm leading-relaxed text-[#5F6368]">{item.text}</p>
                    </div>
                  ))}
                </div>
              </BentoCard>
            </motion.div>

            {/* Stack of 2 cards */}
            <div className="grid gap-4 lg:col-span-5">
              <motion.div {...fadeUp} transition={{ duration: 0.45, delay: 0.05 }}>
                <BentoCard tone="green" eyebrow="Mobile flow" title="Buttons stay thumb-friendly" description="Spacing and hierarchy collapse into a readable vertical path on phones." icon={CheckCircle2} />
              </motion.div>
              <motion.div {...fadeUp} transition={{ duration: 0.45, delay: 0.1 }}>
                <BentoCard tone="amber" eyebrow="Installable" title="The PWA opens somewhere useful" description="The install path starts in the dashboard flow, making the app feel purposeful on first launch." icon={Sparkles} />
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════
           AUTOMATION — Dashboard-style Bento
         ════════════════════════════════════════════════════════════ */}
      <section id="automation" className="py-16 sm:py-20 bg-white/60">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <SectionHeader
            kicker="Automation system"
            title="Automation that feels like Google: quiet by default, clear when it acts."
            description="The engine listens to real booking events, applies conservative rules, and keeps a readable trail."
          />

          <div className="mt-10 grid gap-4 grid-cols-1 lg:grid-cols-12">

            {/* Pipeline steps */}
            <motion.div {...fadeUp} transition={{ duration: 0.45 }} className="lg:col-span-7">
              <BentoCard
                tone="blue"
                eyebrow="Google philosophy"
                title="A calm automation layer, not a noisy robot."
                description="Obvious defaults, human override when needed, and a readable result at the end."
              >
                <div className="grid gap-3 grid-cols-1 sm:grid-cols-2">
                  {automationFlow.map((stage, index) => {
                    const isActive = index === activeAutomationIndex;
                    const StageIcon = stage.icon;
                    return (
                      <motion.button
                        key={stage.step}
                        type="button"
                        whileTap={{ scale: 0.98 }}
                        onClick={() => setActiveAutomationIndex(index)}
                        className={`rounded-2xl border p-4 text-left transition-all ${
                          isActive
                            ? `${signalAccentStyles[stage.accent].badge} shadow-sm`
                            : "border-[#DADCE0] bg-[#F8F9FA] hover:bg-white"
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <div className="flex items-center gap-2">
                            <div className={`flex h-8 w-8 items-center justify-center rounded-xl ${signalAccentStyles[stage.accent].badge}`}>
                              <StageIcon size={14} />
                            </div>
                            <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#5F6368]">{stage.label}</span>
                          </div>
                          <span className="rounded-full border border-[#DADCE0] bg-white px-2 py-0.5 text-[10px] font-semibold text-[#5F6368]">{stage.step}</span>
                        </div>
                        <p className="text-sm font-medium text-[#202124]">{stage.title}</p>
                        <p className="mt-1 text-xs leading-relaxed text-[#5F6368]">{stage.text}</p>
                      </motion.button>
                    );
                  })}
                </div>
              </BentoCard>
            </motion.div>

            {/* Live automation preview */}
            <motion.div {...fadeUp} transition={{ duration: 0.5, delay: 0.08 }} className="lg:col-span-5">
              <div className="rounded-3xl border border-[#DADCE0] bg-white/90 p-5 shadow-[0_2px_12px_-4px_rgba(32,33,36,0.12)] backdrop-blur-sm h-full flex flex-col">
                <div className="flex items-center justify-between gap-3 mb-5">
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">Live automation</p>
                    <p className="mt-1 text-sm text-[#5F6368]">Four-step engine preview</p>
                  </div>
                  <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] ${signalAccentStyles[activeAutomation.accent].badge}`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${signalAccentStyles[activeAutomation.accent].chip}`} />
                    Running
                  </span>
                </div>

                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeAutomation.step}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.25 }}
                    className="flex-1"
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <activeAutomation.icon className="h-4 w-4 text-[#1A73E8]" />
                      <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">{activeAutomation.label}</p>
                    </div>
                    <p className="text-xl font-medium tracking-tight text-[#202124]">{activeAutomation.title}</p>
                    <p className="mt-2 text-sm leading-relaxed text-[#5F6368]">{activeAutomation.text}</p>

                    <div className="mt-5 grid gap-2 grid-cols-2">
                      {[
                        { label: "Trigger", value: "Booking events" },
                        { label: "Decision", value: "Safe thresholds" },
                        { label: "Action", value: "Confirmations & sync" },
                        { label: "Audit", value: "Readable history" },
                      ].map((item) => (
                        <div key={item.label} className="rounded-2xl border border-[#DADCE0] bg-[#F8F9FA] p-3">
                          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#5F6368]">{item.label}</p>
                          <p className="mt-1.5 text-sm font-medium text-[#202124]">{item.value}</p>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                </AnimatePresence>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════
           SOCIAL PROOF — Metric Bento Strip
         ════════════════════════════════════════════════════════════ */}
      <section className="border-y border-[#DADCE0]/60 bg-[#F8F9FA] py-12 sm:py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { icon: Globe, value: "180+", label: "Countries served", tone: "blue" },
              { icon: Zap, value: "< 80ms", label: "Response time", tone: "green" },
              { icon: BarChart3, value: "99.9%", label: "Uptime SLA", tone: "amber" },
              { icon: ShieldCheck, value: "SOC 2", label: "Certified", tone: "blue" },
            ].map((stat) => {
              const StatIcon = stat.icon;
              return (
                <motion.div
                  key={stat.label}
                  {...fadeUp}
                  transition={{ duration: 0.35 }}
                  className="rounded-2xl border border-[#DADCE0] bg-white p-5 text-center shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="flex justify-center mb-3">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${signalAccentStyles[stat.tone as keyof typeof signalAccentStyles].badge}`}>
                      <StatIcon size={18} />
                    </div>
                  </div>
                  <p className="text-2xl font-semibold text-[#202124]">{stat.value}</p>
                  <p className="mt-1 text-xs font-medium text-[#5F6368] uppercase tracking-wider">{stat.label}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════
           FAQ — Bento Cards
         ════════════════════════════════════════════════════════════ */}
      <section id="faq" className="py-16 sm:py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <SectionHeader
            kicker="Common questions"
            title="Quick answers to help you decide."
            description="Everything you need to know about getting started with GraftAI."
          />

          <div className="mt-10 grid gap-4 grid-cols-1 md:grid-cols-2">
            {faqItems.map((item, index) => (
              <motion.div
                key={item.question}
                {...fadeUp}
                transition={{ duration: 0.4, delay: index * 0.06 }}
              >
                <details className="group rounded-3xl border border-[#DADCE0] bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
                  <summary className="cursor-pointer list-none text-[15px] font-medium text-[#202124] outline-none">
                    <span className="flex items-center justify-between gap-4">
                      <span>{item.question}</span>
                      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#F1F3F4] text-[#1A73E8] text-sm font-bold transition-transform group-open:rotate-45">+</span>
                    </span>
                  </summary>
                  <p className="mt-4 text-sm leading-relaxed text-[#5F6368]">{item.answer}</p>
                </details>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════
           CTA — Final
         ════════════════════════════════════════════════════════════ */}
      <section className="px-4 pb-16 sm:px-6 sm:pb-24">
        <div className="mx-auto max-w-7xl">
          <motion.div
            {...fadeUp}
            transition={{ duration: 0.5 }}
            className="rounded-3xl border border-[#1A73E8]/30 bg-[#1A73E8] p-6 sm:p-10 text-white shadow-[0_24px_80px_-50px_rgba(26,115,232,0.55)] overflow-hidden relative"
          >
            {/* Subtle gradient orbs */}
            <div aria-hidden className="pointer-events-none absolute inset-0">
              <div className="absolute -top-20 -right-20 w-60 h-60 rounded-full bg-white/5 blur-3xl" />
              <div className="absolute -bottom-16 -left-16 w-48 h-48 rounded-full bg-white/5 blur-3xl" />
            </div>

            <div className="relative z-10 grid gap-8 lg:grid-cols-[1.3fr_0.7fr] lg:items-center">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-white/70">
                  Ready when you are
                </p>
                <h2 className="mt-4 text-2xl sm:text-3xl lg:text-4xl font-normal tracking-tight text-white leading-[1.15]">
                  Make your scheduling feel as polished as your product.
                </h2>
                <p className="mt-4 max-w-2xl text-sm sm:text-base leading-relaxed text-white/80">
                  Join teams that moved from chaotic calendars to calm, automated scheduling workflows.
                </p>
                <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                  <Link href="/signup" className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-medium text-[#1A73E8] transition-colors hover:bg-[#F8F9FA] sm:w-auto">
                    Start for free <ArrowRight size={16} />
                  </Link>
                  <Link href="/docs" className="inline-flex w-full items-center justify-center rounded-full border border-white/20 bg-white/10 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-white/15 sm:w-auto">
                    Explore documentation
                  </Link>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
                {["Clear hierarchy", "Better mobile flow", "Bento-style proof"].map((item) => (
                  <div key={item} className="rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm font-medium text-white/90 backdrop-blur-sm">
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════
           FOOTER
         ════════════════════════════════════════════════════════════ */}
      <footer className="border-t border-[#DADCE0] bg-[#F8F9FA] py-10">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 text-center md:flex-row md:px-6 md:text-left">
          <div className="flex items-center gap-2 text-[#5F6368]">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[#DADCE0] text-[10px] font-bold text-white">G</div>
            <span className="text-xs font-medium">© {new Date().getFullYear()} GraftAI. Built for calmer scheduling.</span>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs font-medium text-[#5F6368] md:justify-end">
            <Link href="/terms" className="transition-colors hover:text-[#202124]">Terms</Link>
            <Link href="/privacy" className="transition-colors hover:text-[#202124]">Privacy Policy</Link>
            <div className="flex items-center gap-1">
              <ShieldCheck size={14} />
              <span>SOC2 Compliant</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
