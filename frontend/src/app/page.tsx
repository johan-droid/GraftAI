"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Calendar,
  CheckCircle2,
  Clock,
  MessageSquare,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import { BentoCard } from "@/components/landing/BentoCard";

const heroSignals = [
  {
    title: "Feels human",
    text: "Less form-filling, more conversation.",
  },
  {
    title: "Mobile-first",
    text: "Buttons stack and breathe on smaller screens.",
  },
  {
    title: "No schedule math",
    text: "Time zones and buffers are handled quietly.",
  },
];

const previewSteps = [
  {
    step: "01",
    title: "Share one link",
    text: "Invite people without the back-and-forth.",
  },
  {
    step: "02",
    title: "Pick a time",
    text: "Availability stays readable and current.",
  },
  {
    step: "03",
    title: "Confirm instantly",
    text: "Automated follow-up keeps the handoff calm.",
  },
];

const featureCards = [
  {
    eyebrow: "Calendar sync",
    title: "Keeps availability current",
    description:
      "Google and Microsoft calendars stay aligned so the page never feels like a settings maze.",
    icon: Calendar,
    tone: "blue" as const,
    className: "md:col-span-2 xl:col-span-2",
    bullets: ["Live sync", "Conflict checks", "Clear confirmations"],
  },
  {
    eyebrow: "Routing",
    title: "Finds the right host",
    description:
      "Requests move to the right person without forcing the visitor to understand the org chart.",
    icon: Users,
    tone: "green" as const,
  },
  {
    eyebrow: "Timezones",
    title: "Keeps local time obvious",
    description:
      "Every invite resolves to a readable local-time experience with fewer surprises.",
    icon: Clock,
    tone: "amber" as const,
  },
  {
    eyebrow: "Follow-up",
    title: "Sends polite reminders",
    description:
      "The handoff stays polished and quiet instead of turning into a noisy chase.",
    icon: MessageSquare,
    tone: "violet" as const,
  },
];

const faqItems = [
  {
    question: "Does this work well on mobile?",
    answer:
      "Yes. The layout is built mobile-first, with cards, CTAs, and spacing tuned to stay readable at phone widths.",
  },
  {
    question: "Can we keep using our existing calendars?",
    answer:
      "The homepage positions GraftAI as a layer over your calendar tools, not a replacement for them.",
  },
  {
    question: "What happens after install?",
    answer:
      "The PWA opens into the dashboard flow, which makes the install experience feel more useful on first launch.",
  },
];

function SectionHeader({
  kicker,
  title,
  description,
}: {
  kicker: string;
  title: string;
  description: string;
}) {
  return (
    <div className="max-w-2xl">
      <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-[#5F6368]">
        {kicker}
      </p>
      <h2 className="mt-4 text-2xl font-normal tracking-tight text-[#202124] sm:text-3xl">
        {title}
      </h2>
      <p className="mt-4 text-sm leading-relaxed text-[#5F6368] sm:text-base">
        {description}
      </p>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="relative min-h-dvh overflow-hidden bg-[radial-gradient(circle_at_top_left,rgba(26,115,232,0.12),transparent_28%),radial-gradient(circle_at_top_right,rgba(52,168,83,0.08),transparent_24%),linear-gradient(180deg,#F8F9FA_0%,#FFFFFF_52%,#F8F9FA_100%)] text-[#202124] font-sans selection:bg-[#D2E3FC]">
      <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-24 left-[-8rem] h-80 w-80 rounded-full bg-[#1A73E8]/10 blur-3xl" />
        <div className="absolute right-[-6rem] top-40 h-72 w-72 rounded-full bg-[#34A853]/10 blur-3xl" />
        <div className="absolute bottom-0 left-1/2 h-64 w-64 -translate-x-1/2 rounded-full bg-white/60 blur-3xl" />
      </div>

      <nav className="sticky top-0 z-50 border-b border-[#DADCE0]/80 bg-white/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-[#1A73E8] text-xs font-bold text-white">
              G
            </div>
            <span className="text-lg font-medium tracking-tight text-[#202124]">
              GraftAI
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-[#5F6368]">
            <Link href="#features" className="transition-colors hover:text-[#202124]">
              Features
            </Link>
            <Link href="#proof" className="transition-colors hover:text-[#202124]">
              Proof
            </Link>
            <Link href="#faq" className="transition-colors hover:text-[#202124]">
              FAQ
            </Link>
            <Link href="/pricing" className="transition-colors hover:text-[#202124]">
              Pricing
            </Link>
            <Link href="/docs" className="transition-colors hover:text-[#202124]">
              Documentation
            </Link>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <Link
              href="/login"
              className="hidden rounded-full px-4 py-2 text-sm font-medium text-[#1A73E8] transition-colors hover:bg-[#E8F0FE] sm:inline-flex"
            >
              Sign in
            </Link>
            <Link
              href="/signup"
              className="inline-flex items-center gap-1.5 rounded-full bg-[#1A73E8] px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-[#1557B0] sm:px-5"
            >
              Get started
            </Link>
          </div>
        </div>
      </nav>

      <main className="mx-auto max-w-7xl px-4 pb-16 pt-10 sm:px-6 sm:pb-20 sm:pt-14">
        <div className="grid gap-8 lg:grid-cols-12 lg:items-start">
          <motion.section
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="lg:col-span-6"
          >
            <div className="inline-flex items-center gap-2 rounded-full bg-[#E8F0FE] px-3 py-1 text-xs font-medium text-[#1967D2]">
              <Sparkles size={14} />
              <span>Now in public beta</span>
            </div>

            <h1 className="mt-5 max-w-2xl text-4xl font-normal leading-[1.06] tracking-tight text-[#202124] sm:text-5xl md:text-6xl">
              Scheduling that feels calmer, clearer, and more refined.
            </h1>

            <p className="mt-5 max-w-xl text-base leading-relaxed text-[#5F6368] sm:text-lg">
              GraftAI keeps meetings moving without the back-and-forth. It handles routing,
              time zones, and confirmations so the experience stays polished from the first
              click to the final invite.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
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
              {heroSignals.map((item) => (
                <div
                  key={item.title}
                  className="rounded-2xl border border-[#DADCE0] bg-white/85 p-4 shadow-sm backdrop-blur-sm"
                >
                  <div className="flex items-center gap-2 text-[#1A73E8]">
                    <CheckCircle2 size={14} />
                    <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">
                      {item.title}
                    </p>
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-[#5F6368]">
                    {item.text}
                  </p>
                </div>
              ))}
            </div>

            <div className="mt-6 flex flex-wrap gap-2 text-xs font-medium text-[#5F6368]">
              {[
                "Google Calendar",
                "Microsoft 365",
                "Mobile-ready PWA",
                "Clear confirmations",
              ].map((tag) => (
                <span
                  key={tag}
                  className="rounded-full border border-[#DADCE0] bg-white/80 px-3 py-1.5 shadow-sm"
                >
                  {tag}
                </span>
              ))}
            </div>
          </motion.section>

          <motion.section
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.08 }}
            className="lg:col-span-6"
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <BentoCard
                className="sm:col-span-2"
                tone="blue"
                eyebrow="Live preview"
                title="A calmer booking flow"
                description="The product story is shown in a compact rhythm: a clear path, less noise, and stronger hierarchy."
              >
                <div className="space-y-3">
                  {previewSteps.map((step) => (
                    <div
                      key={step.step}
                      className="flex items-start gap-3 rounded-2xl border border-[#DADCE0] bg-[#F8F9FA] p-4"
                    >
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white text-xs font-semibold text-[#1A73E8] shadow-sm">
                        {step.step}
                      </div>
                      <div>
                        <p className="font-medium text-[#202124]">{step.title}</p>
                        <p className="mt-1 text-sm leading-relaxed text-[#5F6368]">{step.text}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </BentoCard>

              <BentoCard
                tone="green"
                eyebrow="Always local"
                title="Time zones stay readable"
                description="Guests get a clear local-time experience instead of offset math or hidden conversions."
                icon={Clock}
                className="min-h-[220px]"
              />

              <BentoCard
                tone="amber"
                eyebrow="Routing"
                title="Teams get the right handoff"
                description="Requests move cleanly to the right person so the visitor never has to chase the next step."
                icon={Users}
                className="min-h-[220px]"
              />
            </div>
          </motion.section>
        </div>
      </main>

      <section id="features" className="border-y border-[#DADCE0]/80 bg-white/90 py-16 sm:py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <SectionHeader
            kicker="What gets better"
            title="A bento layout lets the page explain the product without feeling crowded."
            description="The goal is to close the gaps that a flatter landing page leaves open: product depth, clarity on mobile, and a stronger visual hierarchy."
          />

          <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {featureCards.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                transition={{ duration: 0.4, delay: index * 0.08 }}
                whileHover={{ y: -4 }}
                className={feature.className}
              >
                <BentoCard
                  tone={feature.tone}
                  eyebrow={feature.eyebrow}
                  title={feature.title}
                  description={feature.description}
                  icon={feature.icon}
                >
                  {feature.bullets ? (
                    <div className="grid gap-2 sm:grid-cols-3">
                      {feature.bullets.map((bullet) => (
                        <div
                          key={bullet}
                          className="rounded-2xl border border-[#DADCE0] bg-[#F8F9FA] px-3 py-2 text-xs font-medium text-[#5F6368]"
                        >
                          {bullet}
                        </div>
                      ))}
                    </div>
                  ) : null}
                </BentoCard>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section id="proof" className="py-16 sm:py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <div className="grid gap-4 lg:grid-cols-12">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.45 }}
              className="lg:col-span-7"
            >
              <BentoCard
                tone="violet"
                eyebrow="Why it feels different"
                title="The landing page should mirror the product: structured, calm, and easy to scan."
                description="This section fills the main proof gap by showing why the product feels more polished than a generic scheduling page."
              >
                <div className="grid gap-3 sm:grid-cols-3">
                  {[
                    {
                      title: "Less coordination",
                      text: "A single link replaces repeated message threads.",
                    },
                    {
                      title: "Clear next step",
                      text: "The page makes the action obvious within seconds.",
                    },
                    {
                      title: "Thumb-friendly",
                      text: "Primary actions stay accessible on small screens.",
                    },
                  ].map((item) => (
                    <div
                      key={item.title}
                      className="rounded-2xl border border-[#DADCE0] bg-[#F8F9FA] p-4"
                    >
                      <p className="text-sm font-medium text-[#202124]">{item.title}</p>
                      <p className="mt-1 text-sm leading-relaxed text-[#5F6368]">{item.text}</p>
                    </div>
                  ))}
                </div>
              </BentoCard>
            </motion.div>

            <div className="grid gap-4 lg:col-span-5">
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                transition={{ duration: 0.45, delay: 0.05 }}
              >
                <BentoCard
                  tone="green"
                  eyebrow="Mobile flow"
                  title="Buttons stay thumb-friendly"
                  description="Spacing, hierarchy, and spacing all collapse into a readable vertical path on phones."
                  icon={CheckCircle2}
                />
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                transition={{ duration: 0.45, delay: 0.1 }}
              >
                <BentoCard
                  tone="amber"
                  eyebrow="Installable"
                  title="The PWA opens somewhere useful"
                  description="The install path now starts in the dashboard flow, which makes the app feel more purposeful on first launch."
                  icon={Sparkles}
                />
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      <section id="faq" className="border-t border-[#DADCE0]/80 bg-white/90 py-16 sm:py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <SectionHeader
            kicker="Questions users ask"
            title="An FAQ block fills the last conversion gap without making the page feel heavy."
            description="These answers remove uncertainty around mobile behavior, existing calendars, and what happens after install."
          />

          <div className="mt-10 grid gap-4 md:grid-cols-3">
            {faqItems.map((item, index) => (
              <motion.div
                key={item.question}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                transition={{ duration: 0.4, delay: index * 0.08 }}
              >
                <details className="group rounded-[28px] border border-[#DADCE0] bg-white/85 p-5 shadow-sm transition-shadow hover:shadow-md">
                  <summary className="cursor-pointer list-none text-sm font-medium text-[#202124] outline-none">
                    <span className="flex items-center justify-between gap-4">
                      <span>{item.question}</span>
                      <span className="text-[#1A73E8] transition-transform group-open:rotate-45">+</span>
                    </span>
                  </summary>
                  <p className="mt-4 text-sm leading-relaxed text-[#5F6368]">
                    {item.answer}
                  </p>
                </details>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="px-4 pb-16 sm:px-6 sm:pb-24">
        <div className="mx-auto max-w-7xl">
          <div className="rounded-[32px] border border-[#1A73E8] bg-[#1A73E8] p-6 text-white shadow-[0_24px_80px_-50px_rgba(26,115,232,0.55)] sm:p-8">
            <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-white/80">
                  Ready when you are
                </p>
                <h2 className="mt-4 text-2xl font-normal tracking-tight text-white sm:text-3xl">
                  Make the homepage feel as polished as the product itself.
                </h2>
                <p className="mt-4 max-w-2xl text-sm leading-relaxed text-white/85 sm:text-base">
                  The new layout puts proof, product depth, and mobile clarity in the foreground
                  so the page feels more refined without losing the clean Google-inspired tone.
                </p>
                <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                  <Link
                    href="/signup"
                    className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-medium text-[#1A73E8] transition-colors hover:bg-[#F8F9FA] sm:w-auto"
                  >
                    Start for free
                    <ArrowRight size={18} />
                  </Link>
                  <Link
                    href="/docs"
                    className="inline-flex w-full items-center justify-center rounded-full border border-white/25 bg-white/10 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-white/15 sm:w-auto"
                  >
                    Explore documentation
                  </Link>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
                {[
                  "Clear hierarchy",
                  "Better mobile flow",
                  "Bento-style proof",
                ].map((item) => (
                  <div
                    key={item}
                    className="rounded-2xl border border-white/20 bg-white/10 px-4 py-3 text-sm font-medium text-white/90"
                  >
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-[#DADCE0] bg-[#F8F9FA] py-12">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 text-center md:flex-row md:px-6 md:text-left">
          <div className="flex items-center gap-2 text-[#5F6368]">
            <div className="flex h-5 w-5 items-center justify-center rounded bg-[#DADCE0] text-[10px] font-bold text-white">
              G
            </div>
            <span className="text-xs font-medium">
              © {new Date().getFullYear()} GraftAI. Built for calmer scheduling.
            </span>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs font-medium text-[#5F6368] md:justify-end">
            <Link href="/terms" className="transition-colors hover:text-[#202124]">
              Terms
            </Link>
            <Link href="/privacy" className="transition-colors hover:text-[#202124]">
              Privacy Policy
            </Link>
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
