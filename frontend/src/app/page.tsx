"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Calendar, CheckCircle2, Clock, MessageSquare, ShieldCheck, Sparkles, Users } from "lucide-react";

const promiseCards = [
  {
    icon: MessageSquare,
    title: "Feels human",
    text: "Less form-filling, more conversation.",
    tone: "bg-[#E8F0FE] text-[#1967D2]",
  },
  {
    icon: CheckCircle2,
    title: "Mobile-first",
    text: "Buttons stack and breathe on smaller screens.",
    tone: "bg-[#E6F4EA] text-[#137333]",
  },
  {
    icon: Clock,
    title: "No schedule math",
    text: "We quietly handle time zones and buffers.",
    tone: "bg-[#FEF7E0] text-[#E37400]",
  },
];

const agendaCards = [
  {
    time: "09:30",
    title: "Team standup",
    note: "A short check-in with room to breathe.",
  },
  {
    time: "11:00",
    title: "Client follow-up",
    note: "Shared timing and polite reminders included.",
  },
  {
    time: "14:00",
    title: "Focus block",
    note: "Protected from last-minute meeting drift.",
  },
  {
    time: "16:30",
    title: "Wrap-up",
    note: "A soft end to the day and a cleaner tomorrow.",
  },
];

const featureCards = [
  {
    icon: Calendar,
    title: "Smart Calendar Sync",
    description: "Keeps Google and Microsoft calendars in sync so nobody double-books or chases updates.",
    color: "text-blue-600",
    bg: "bg-blue-50",
  },
  {
    icon: Users,
    title: "Team Routing",
    description: "Finds the right person and the right time without making you coordinate every reply.",
    color: "text-green-600",
    bg: "bg-green-50",
  },
  {
    icon: Clock,
    title: "Time Zone Intelligence",
    description: "Handles time-zone math quietly, so meetings feel local for everyone.",
    color: "text-orange-600",
    bg: "bg-orange-50",
  },
];

export default function LandingPage() {
  return (
    <div className="relative min-h-dvh overflow-x-hidden bg-[radial-gradient(circle_at_top_left,rgba(26,115,232,0.12),transparent_28%),radial-gradient(circle_at_top_right,rgba(52,168,83,0.08),transparent_24%),linear-gradient(180deg,#F8F9FA_0%,#FFFFFF_52%,#F8F9FA_100%)] text-[#202124] font-sans selection:bg-[#D2E3FC]">
      <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-24 left-[-8rem] h-80 w-80 rounded-full bg-[#1A73E8]/10 blur-3xl" />
        <div className="absolute right-[-6rem] top-40 h-72 w-72 rounded-full bg-[#34A853]/10 blur-3xl" />
        <div className="absolute bottom-0 left-1/2 h-64 w-64 -translate-x-1/2 rounded-full bg-white/60 blur-3xl" />
      </div>

      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-[#DADCE0]/80 bg-white/75 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-[#1A73E8] flex items-center justify-center text-white font-bold text-xs">
              G
            </div>
            <span className="text-lg font-medium tracking-tight text-[#202124]">
              GraftAI
            </span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-[#5F6368]">
            <Link href="#features" className="hover:text-[#202124] transition-colors">Features</Link>
            <Link href="/pricing" className="hover:text-[#202124] transition-colors">Pricing</Link>
            <Link href="/docs" className="hover:text-[#202124] transition-colors">Documentation</Link>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <Link 
              href="/login" 
              className="hidden sm:inline-flex text-sm font-medium text-[#1A73E8] hover:bg-[#E8F0FE] px-4 py-2 rounded-full transition-colors"
            >
              Sign in
            </Link>
            <Link 
              href="/signup" 
              className="inline-flex items-center gap-1.5 text-sm font-medium bg-[#1A73E8] text-white hover:bg-[#1557B0] px-4 py-2 rounded-full transition-colors shadow-sm sm:px-5"
            >
              Get started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="mx-auto max-w-6xl px-4 pb-16 pt-10 sm:px-6 sm:pb-20 sm:pt-20">
        <div className="grid gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
          <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center lg:text-left"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#E8F0FE] text-[#1967D2] text-xs font-medium mb-6">
            <Sparkles size={14} />
            <span>Now in public beta</span>
          </div>
          <h1 className="mx-auto max-w-2xl text-4xl font-normal leading-[1.08] tracking-tight text-[#202124] sm:text-5xl md:text-6xl lg:mx-0">
            Scheduling that feels more human.
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-base leading-relaxed text-[#5F6368] sm:text-lg lg:mx-0">
            GraftAI keeps meetings moving without the back-and-forth. It handles routing, time zones, and follow-ups so people can stay focused on the work and the conversation.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center lg:justify-start">
            <Link 
              href="/signup" 
              className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-[#1A73E8] px-7 py-3 text-base font-medium text-white shadow-sm transition-colors hover:bg-[#1557B0] sm:w-auto"
            >
              Start for free
              <ArrowRight size={18} />
            </Link>
            <Link 
              href="/docs" 
              className="inline-flex w-full items-center justify-center rounded-full border border-[#DADCE0] bg-white px-7 py-3 text-base font-medium text-[#5F6368] transition-colors hover:bg-[#F8F9FA] sm:w-auto"
            >
              Read the docs
            </Link>
          </div>
          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            {promiseCards.map((card) => (
              <div key={card.title} className="rounded-2xl border border-[#DADCE0] bg-white/80 p-4 text-left shadow-sm backdrop-blur-sm">
                <div className={`mb-3 flex h-10 w-10 items-center justify-center rounded-2xl ${card.tone}`}>
                  <card.icon size={18} />
                </div>
                <h3 className="text-sm font-semibold text-[#202124]">{card.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-[#5F6368]">{card.text}</p>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.1 }}
          className="relative"
        >
          <div className="absolute inset-0 -z-10 rounded-[32px] bg-[#1A73E8]/5 blur-3xl" />
          <div className="rounded-[32px] border border-[#DADCE0] bg-white/80 p-4 shadow-[0_30px_90px_-45px_rgba(32,33,36,0.35)] backdrop-blur-xl sm:p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[11px] uppercase tracking-[0.3em] text-[#5F6368]">Today at a glance</p>
                <h2 className="mt-2 text-xl font-medium text-[#202124]">A calmer schedule, not a louder app.</h2>
              </div>
              <div className="rounded-full bg-[#E8F0FE] px-3 py-1 text-xs font-medium text-[#1967D2]">4 items</div>
            </div>

            <div className="mt-5 space-y-3">
              {agendaCards.map((item) => (
                <div key={item.time} className="flex items-start gap-4 rounded-2xl border border-[#DADCE0] bg-[#F8F9FA] p-4">
                  <div className="min-w-[4.5rem] rounded-2xl bg-white px-3 py-2 text-center shadow-sm">
                    <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[#5F6368]">{item.time}</div>
                  </div>
                  <div>
                    <p className="font-medium text-[#202124]">{item.title}</p>
                    <p className="mt-1 text-sm leading-relaxed text-[#5F6368]">{item.note}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-5 rounded-3xl border border-[#DADCE0] bg-[#F8F9FA] p-4">
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#1A73E8]/10 text-[#1A73E8]">
                  <MessageSquare className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-medium text-[#202124]">&ldquo;Could you make this feel less rushed?&rdquo;</p>
                  <p className="mt-1 text-sm text-[#5F6368]">
                    GraftAI turns that request into a clean schedule with room to breathe.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
        </div>
      </main>

      {/* Features Grid */}
      <section id="features" className="border-t border-[#DADCE0]/80 bg-white/90 py-16 sm:py-24">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-[#5F6368]">Less admin, more momentum</p>
            <h2 className="mt-4 text-2xl font-normal tracking-tight text-[#202124] sm:text-3xl">
              Everything you need to manage time without feeling boxed in.
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-[#5F6368] sm:text-base">
              A calmer scheduling flow for teams that want speed, clarity, and a little more breathing room in the week.
            </p>
          </div>

          <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-3">
            {featureCards.map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 15 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
                whileHover={{ y: -4 }}
                className="rounded-3xl border border-[#DADCE0] bg-white p-6 shadow-sm transition-shadow"
              >
                <div className={`mb-5 flex h-12 w-12 items-center justify-center rounded-2xl ${feature.bg} ${feature.color}`}>
                  <feature.icon size={24} />
                </div>
                <h3 className="mb-2 text-lg font-medium text-[#202124]">{feature.title}</h3>
                <p className="text-sm leading-relaxed text-[#5F6368]">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#DADCE0] bg-[#F8F9FA] py-12">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 text-center md:flex-row md:px-6 md:text-left">
          <div className="flex items-center gap-2 text-[#5F6368]">
            <div className="w-5 h-5 rounded bg-[#DADCE0] flex items-center justify-center text-white font-bold text-[10px]">
              G
            </div>
            <span className="text-xs font-medium">© {new Date().getFullYear()} GraftAI. Built for calmer scheduling.</span>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs font-medium text-[#5F6368] md:justify-end">
            <Link href="/terms" className="hover:text-[#202124] transition-colors">Terms</Link>
            <Link href="/privacy" className="hover:text-[#202124] transition-colors">Privacy Policy</Link>
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
