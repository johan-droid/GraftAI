"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  BookOpenText,
  Code2,
  Layers3,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
  Workflow,
} from "lucide-react";
import {
  MarketingCard,
  MarketingHero,
  MarketingSectionHeading,
  MarketingShell,
} from "@/components/marketing/MarketingShell";

const docTracks = [
  {
    icon: Workflow,
    label: "Product flow",
    title: "Booking lifecycle",
    description:
      "Understand how public links, availability, confirmation, reminders, and rescheduling fit together as one journey.",
    bullets: ["Time-zone aware slots", "Clear guest handoffs", "Reliable follow-up states"],
  },
  {
    icon: Layers3,
    label: "System shape",
    title: "Platform architecture",
    description:
      "See how the FastAPI backend, worker queue, frontend shell, and calendar sync layers stay coordinated under load.",
    bullets: ["Async API routes", "Celery background work", "Shared design and auth patterns"],
  },
  {
    icon: ShieldCheck,
    label: "Trust layer",
    title: "Security and policy",
    description:
      "Review the operational defaults that keep scheduling flows protected, rate-limited, and auditable.",
    bullets: ["JWT and session boundaries", "Protected action tokens", "Operational guardrails"],
  },
  {
    icon: Code2,
    label: "Build surface",
    title: "Developer handoff",
    description:
      "Jump from product docs into implementation guidance, code examples, and API-oriented thinking without losing context.",
    bullets: ["Starter snippets", "Integration patterns", "Delivery-oriented references"],
  },
];

const implementationCards = [
  {
    title: "Frontend conventions",
    text: "Use the singleton API client, prefer server components by default, and keep public routes visually calm and fast to scan.",
  },
  {
    title: "Backend conventions",
    text: "Use async sessions, explicit HTTP exceptions, idempotency on booking creation, and Celery for durable background work.",
  },
  {
    title: "Automation model",
    text: "Treat AI as one layer in a fallback chain, not the only decision-maker. Every automated action should remain explainable later.",
  },
];

const quickLinks = [
  { href: "/developers", label: "Open developer hub" },
  { href: "/pricing", label: "See plans and quotas" },
  { href: "/privacy", label: "Review privacy policy" },
];

export default function DocsPage() {
  return (
    <MarketingShell currentPath="/docs">
      <MarketingHero
        eyebrow="Documentation hub"
        title="Explore the system without losing the product feel."
        description="The docs experience now mirrors the same calm, premium atmosphere as the landing page while giving visitors a clearer path into architecture, workflows, and implementation details."
        primaryAction={
          <Link
            href="/developers"
            className="inline-flex items-center justify-center gap-2 rounded-full bg-[#1A73E8] px-6 py-3 text-sm font-semibold text-white shadow-[0_16px_34px_-22px_rgba(26,115,232,0.9)] transition-all hover:bg-[#1557B0]"
          >
            Explore developer hub <ArrowRight size={16} />
          </Link>
        }
        secondaryAction={
          <Link
            href="/pricing"
            className="inline-flex items-center justify-center rounded-full border border-[#DADCE0] bg-white px-6 py-3 text-sm font-semibold text-[#5F6368] transition-colors hover:bg-[#F8F9FA] hover:text-[#202124]"
          >
            Compare plans
          </Link>
        }
        stats={[
          { label: "System", value: "FastAPI + Next.js" },
          { label: "Scheduling", value: "Atomic booking flow" },
          { label: "Automation", value: "AI with fallbacks" },
        ]}
        aside={
          <MarketingCard className="h-full">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">
                  Reader mode
                </p>
                <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[#202124]">
                  Start at the right altitude.
                </h2>
              </div>
              <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-[#E8F0FE] text-[#1967D2]">
                <BookOpenText size={20} />
              </div>
            </div>

            <div className="mt-6 space-y-3">
              {quickLinks.map((link, index) => (
                <motion.div
                  key={link.href}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.12 + index * 0.08 }}
                >
                  <Link
                    href={link.href}
                    className="group flex items-center justify-between rounded-3xl border border-[#E5EAF1] bg-[#F8FBFF] px-4 py-4 transition-all hover:-translate-y-0.5 hover:border-[#D2E3FC] hover:bg-white"
                  >
                    <span className="text-sm font-medium text-[#202124]">{link.label}</span>
                    <ArrowRight
                      size={16}
                      className="text-[#1A73E8] transition-transform group-hover:translate-x-0.5"
                    />
                  </Link>
                </motion.div>
              ))}
            </div>

            <div className="mt-6 rounded-[28px] border border-[#DADCE0] bg-[#202124] p-5 text-white shadow-[0_26px_50px_-36px_rgba(32,33,36,0.9)]">
              <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.28em] text-white/60">
                <Sparkles size={12} />
                Live excerpt
              </div>
              <pre className="mt-4 overflow-x-auto text-sm leading-relaxed text-[#D2E3FC]">
{`POST /api/v1/bookings
X-Idempotency-Key: calm-flow-001

{
  "event_type_id": "strategy-intro",
  "timezone": "America/Los_Angeles",
  "attendee_email": "guest@example.com"
}`}
              </pre>
            </div>
          </MarketingCard>
        }
      />

      <section className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-12">
        <MarketingSectionHeading
          kicker="Documentation tracks"
          title="A clearer way to move from product story to implementation detail."
          description="Instead of splitting the experience into disconnected dark microsites, the documentation now behaves like a guided surface with crisp hierarchy, motion, and stronger wayfinding."
        />

        <div className="mt-10 grid gap-4 md:grid-cols-2">
          {docTracks.map((track, index) => {
            const Icon = track.icon;
            return (
              <motion.div
                key={track.title}
                initial={{ opacity: 0, y: 18 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.45, delay: index * 0.06 }}
              >
                <MarketingCard className="h-full">
                  <div className="flex items-start gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#E8F0FE] text-[#1967D2]">
                      <Icon size={20} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">
                        {track.label}
                      </p>
                      <h3 className="mt-2 text-xl font-semibold tracking-tight text-[#202124]">
                        {track.title}
                      </h3>
                    </div>
                  </div>
                  <p className="mt-4 text-sm leading-relaxed text-[#5F6368]">{track.description}</p>
                  <div className="mt-5 grid gap-2">
                    {track.bullets.map((bullet) => (
                      <div
                        key={bullet}
                        className="rounded-2xl border border-[#E5EAF1] bg-[#F8FBFF] px-4 py-3 text-sm font-medium text-[#202124]"
                      >
                        {bullet}
                      </div>
                    ))}
                  </div>
                </MarketingCard>
              </motion.div>
            );
          })}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-12 sm:px-6 sm:pb-16">
        <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.45 }}
          >
            <MarketingCard className="h-full">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#FDE7E9] text-[#D93025]">
                  <TerminalSquare size={20} />
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">
                    Implementation note
                  </p>
                  <h3 className="mt-2 text-xl font-semibold tracking-tight text-[#202124]">
                    Operational guidance stays close to the product.
                  </h3>
                </div>
              </div>
              <p className="mt-4 max-w-2xl text-sm leading-relaxed text-[#5F6368]">
                GraftAI’s strongest documentation isn’t just a reference list. It ties UI choices, API behavior,
                background task expectations, and security rules into one readable system so contributors can make
                changes confidently.
              </p>
              <div className="mt-6 grid gap-3">
                {implementationCards.map((card) => (
                  <div
                    key={card.title}
                    className="rounded-[28px] border border-[#E5EAF1] bg-white/90 px-5 py-4 shadow-[0_14px_34px_-28px_rgba(32,33,36,0.32)]"
                  >
                    <p className="text-sm font-semibold text-[#202124]">{card.title}</p>
                    <p className="mt-2 text-sm leading-relaxed text-[#5F6368]">{card.text}</p>
                  </div>
                ))}
              </div>
            </MarketingCard>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.45, delay: 0.08 }}
          >
            <MarketingCard className="h-full">
              <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">
                Next stop
              </p>
              <h3 className="mt-3 text-2xl font-semibold tracking-tight text-[#202124]">
                Ready for code, SDKs, and integration patterns?
              </h3>
              <p className="mt-4 text-sm leading-relaxed text-[#5F6368]">
                The developer hub now inherits the same public theme, but it goes deeper into examples, architecture
                surfaces, and implementation-ready entry points.
              </p>

              <div className="mt-6 rounded-[28px] border border-[#DADCE0] bg-[#202124] p-5 text-white">
                <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.28em] text-white/60">
                  <Code2 size={12} />
                  Focus areas
                </div>
                <div className="mt-4 grid gap-3">
                  {["Quick-start snippets", "Architecture maps", "API capability overview", "Support and handoff paths"].map((item) => (
                    <div
                      key={item}
                      className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-medium text-white/90"
                    >
                      {item}
                    </div>
                  ))}
                </div>
              </div>

              <Link
                href="/developers"
                className="mt-6 inline-flex items-center gap-2 rounded-full bg-[#1A73E8] px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#1557B0]"
              >
                Continue to developers <ArrowRight size={16} />
              </Link>
            </MarketingCard>
          </motion.div>
        </div>
      </section>
    </MarketingShell>
  );
}

