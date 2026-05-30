"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  BookOpenText,
  CheckCircle2,
  Code2,
  Copy,
  ExternalLink,
  GitBranch,
  Layers3,
  Search,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
  Webhook,
} from "lucide-react";
import {
  MarketingCard,
  MarketingHero,
  MarketingSectionHeading,
  MarketingShell,
} from "@/components/marketing/MarketingShell";

const docSections = [
  {
    id: "surface",
    label: "Platform surface",
    title: "Core scheduling APIs",
    description: "Booking creation, availability intelligence, public links, and calendar state transitions.",
    tags: ["Bookings", "Availability", "Public links"],
  },
  {
    id: "auth",
    label: "Authentication",
    title: "Dual-token architecture",
    description: "Auth.js manages the frontend session while the backend issues and rotates its own JWT pair.",
    tags: ["NextAuth", "backendToken", "refresh rotation"],
  },
  {
    id: "automation",
    label: "Automation",
    title: "AI with safe fallbacks",
    description: "The orchestration path moves from AI agent to rules to manual review instead of relying on one brittle layer.",
    tags: ["Agent controller", "Rule engine", "Audit trail"],
  },
  {
    id: "embed",
    label: "Embeds",
    title: "Public booking embeds",
    description: "Drop booking surfaces into external sites without losing availability, confirmation, or reschedule behavior.",
    tags: ["iframe route", "public booking", "responsive UX"],
  },
  {
    id: "security",
    label: "Security",
    title: "Protected scheduling flows",
    description: "Signed actions, strict validation, rate limits, and operational safeguards protect user-facing scheduling routes.",
    tags: ["Rate limiting", "signed tokens", "forbid extra fields"],
  },
  {
    id: "ops",
    label: "Operations",
    title: "Background tasks and sync",
    description: "Use Celery for reminders, sync, automation, and webhook dispatch so work survives retries and restarts.",
    tags: ["Celery", "Redis", "worker durability"],
  },
];

const capabilityCards = [
  {
    icon: Layers3,
    title: "Architecture clarity",
    text: "Understand the FastAPI, Next.js, Celery, Redis, and calendar-provider layers as one system instead of five separate tools.",
  },
  {
    icon: Webhook,
    title: "Integration thinking",
    text: "Move from booking events to downstream actions with patterns that account for retries, quotas, and auditable outcomes.",
  },
  {
    icon: ShieldCheck,
    title: "Safer defaults",
    text: "Build with the same transaction, auth, and validation conventions the product relies on in production paths.",
  },
];

const codeExamples = {
  javascript: `import { apiClient } from "@/lib/api-client";

const booking = await apiClient.post("/bookings", {
  event_type_id: "team-sync",
  timezone: "America/Los_Angeles",
  attendee_email: "jane@company.com",
  attendee_name: "Jane Smith",
});`,
  python: `async with async_session() as db:
    booking = await booking_service.create_booking(
        db=db,
        event_type_id="team-sync",
        attendee_email="jane@company.com",
        timezone="America/Los_Angeles",
        idempotency_key="calm-flow-001",
    )`,
  curl: `curl -X POST https://api.graftai.com/api/v1/bookings \\
  -H "Authorization: Bearer <backendToken>" \\
  -H "X-Idempotency-Key: calm-flow-001" \\
  -H "Content-Type: application/json" \\
  -d '{
    "event_type_id": "team-sync",
    "timezone": "America/Los_Angeles",
    "attendee_email": "jane@company.com"
  }'`,
} as const;

type ExampleTab = keyof typeof codeExamples;

export default function DevelopersPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<ExampleTab>("javascript");
  const [copied, setCopied] = useState(false);

  const normalizedQuery = searchQuery.trim().toLowerCase();
  const filteredSections = !normalizedQuery
    ? docSections
    : docSections.filter((section) => {
        const haystack = [section.label, section.title, section.description, ...section.tags]
          .join(" ")
          .toLowerCase();
        return haystack.includes(normalizedQuery);
      });

  const copyCode = async () => {
    await navigator.clipboard.writeText(codeExamples[activeTab]);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  return (
    <MarketingShell currentPath="/developers">
      <MarketingHero
        eyebrow="Developer hub"
        title="Build on the same calm system the product is selling."
        description="This page now feels like part of the same cinematic marketing journey, but it still gives engineers what they actually need: architecture signals, code examples, integration lanes, and trustworthy platform constraints."
        primaryAction={
          <Link
            href="/docs"
            className="inline-flex items-center justify-center gap-2 rounded-full bg-[#1A73E8] px-6 py-3 text-sm font-semibold text-white shadow-[0_16px_34px_-22px_rgba(26,115,232,0.9)] transition-all hover:bg-[#1557B0]"
          >
            Read platform docs <ArrowRight size={16} />
          </Link>
        }
        secondaryAction={
          <a
            href="https://github.com/graftai"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-2 rounded-full border border-[#DADCE0] bg-white px-6 py-3 text-sm font-semibold text-[#5F6368] transition-colors hover:bg-[#F8F9FA] hover:text-[#202124]"
          >
            View GitHub <ExternalLink size={16} />
          </a>
        }
        stats={[
          { label: "Auth model", value: "Dual token" },
          { label: "Scheduling", value: "Atomic + idempotent" },
          { label: "Workers", value: "Celery-backed" },
        ]}
        aside={
          <MarketingCard className="h-full">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">
                  Build surface
                </p>
                <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[#202124]">
                  Practical entry points for real integrations.
                </h2>
              </div>
              <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-[#E8F0FE] text-[#1967D2]">
                <Code2 size={20} />
              </div>
            </div>

            <div className="mt-6 grid gap-3">
              {capabilityCards.map((card, index) => {
                const Icon = card.icon;
                return (
                  <motion.div
                    key={card.title}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.12 + index * 0.08 }}
                    className="rounded-[28px] border border-[#E5EAF1] bg-[#F8FBFF] px-5 py-4"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-[#1A73E8] shadow-sm">
                        <Icon size={18} />
                      </div>
                      <p className="text-sm font-semibold text-[#202124]">{card.title}</p>
                    </div>
                    <p className="mt-3 text-sm leading-relaxed text-[#5F6368]">{card.text}</p>
                  </motion.div>
                );
              })}
            </div>
          </MarketingCard>
        }
      />

      <section className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-12">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <MarketingSectionHeading
            kicker="Search the platform"
            title="A developer page that helps you orient fast."
            description="Instead of a generic dark docs browser, this hub now leads with the real platform primitives contributors care about."
          />

          <div className="relative w-full max-w-md">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#5F6368]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search auth, booking, embed, security..."
              className="w-full rounded-full border border-white/70 bg-white/82 py-3 pl-11 pr-4 text-sm text-[#202124] shadow-[0_20px_50px_-38px_rgba(32,33,36,0.4)] outline-none backdrop-blur-xl placeholder:text-[#5F6368] focus:border-[#D2E3FC]"
            />
          </div>
        </div>

        <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filteredSections.map((section, index) => (
            <motion.div
              key={section.id}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.45, delay: index * 0.05 }}
            >
              <MarketingCard className="h-full">
                <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">
                  {section.label}
                </p>
                <h3 className="mt-3 text-xl font-semibold tracking-tight text-[#202124]">
                  {section.title}
                </h3>
                <p className="mt-4 text-sm leading-relaxed text-[#5F6368]">{section.description}</p>
                <div className="mt-5 flex flex-wrap gap-2">
                  {section.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full border border-[#DADCE0] bg-[#F8FBFF] px-3 py-1 text-[11px] font-semibold text-[#5F6368]"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </MarketingCard>
            </motion.div>
          ))}
        </div>

        {!filteredSections.length && (
          <MarketingCard className="mt-6">
            <p className="text-lg font-semibold text-[#202124]">No matches yet.</p>
            <p className="mt-2 text-sm leading-relaxed text-[#5F6368]">
              Try searching for booking, tokens, automation, embeds, or security.
            </p>
          </MarketingCard>
        )}
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-12 sm:px-6 sm:pb-16">
        <div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.45 }}
          >
            <MarketingCard className="h-full">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">
                    Quick start
                  </p>
                  <h3 className="mt-3 text-2xl font-semibold tracking-tight text-[#202124]">
                    Code examples with less filler.
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={copyCode}
                  className="inline-flex items-center gap-2 rounded-full border border-[#DADCE0] bg-white px-4 py-2 text-sm font-semibold text-[#5F6368] transition-colors hover:bg-[#F8F9FA] hover:text-[#202124]"
                >
                  {copied ? <CheckCircle2 size={16} className="text-[#34A853]" /> : <Copy size={16} />}
                  {copied ? "Copied" : "Copy"}
                </button>
              </div>

              <div className="mt-5 flex flex-wrap gap-2">
                {(["javascript", "python", "curl"] as ExampleTab[]).map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setActiveTab(tab)}
                    className={`rounded-full px-4 py-2 text-sm font-semibold capitalize transition-all ${
                      activeTab === tab
                        ? "bg-[#202124] text-white shadow-sm"
                        : "border border-[#DADCE0] bg-white text-[#5F6368] hover:bg-[#F8F9FA] hover:text-[#202124]"
                    }`}
                  >
                    {tab === "curl" ? "cURL" : tab}
                  </button>
                ))}
              </div>

              <div className="mt-5 overflow-hidden rounded-[28px] border border-[#DADCE0] bg-[#202124] shadow-[0_30px_70px_-44px_rgba(32,33,36,0.86)]">
                <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
                  <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.28em] text-white/60">
                    <TerminalSquare size={12} />
                    Example
                  </div>
                  <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-white/70">
                    {activeTab}
                  </div>
                </div>
                <pre className="overflow-x-auto px-5 py-5 text-sm leading-relaxed text-[#D2E3FC]">
                  <code>{codeExamples[activeTab]}</code>
                </pre>
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
                Implementation lanes
              </p>
              <h3 className="mt-3 text-2xl font-semibold tracking-tight text-[#202124]">
                The parts most teams ask about first.
              </h3>
              <div className="mt-6 grid gap-3">
                {[
                  {
                    icon: BookOpenText,
                    title: "Public booking",
                    text: "Share a clean route, preserve local time, and keep booking changes self-serve for guests.",
                  },
                  {
                    icon: ShieldCheck,
                    title: "Auth exchange",
                    text: "Convert the frontend session into a backend token through the social exchange flow and protect server-side actions.",
                  },
                  {
                    icon: Sparkles,
                    title: "Automation handoff",
                    text: "Send durable work to Celery and preserve readable audit signals when AI or external integrations act.",
                  },
                ].map((item) => {
                  const Icon = item.icon;
                  return (
                    <div
                      key={item.title}
                      className="rounded-[28px] border border-[#E5EAF1] bg-[#F8FBFF] px-5 py-4"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-[#1A73E8] shadow-sm">
                          <Icon size={18} />
                        </div>
                        <p className="text-sm font-semibold text-[#202124]">{item.title}</p>
                      </div>
                      <p className="mt-3 text-sm leading-relaxed text-[#5F6368]">{item.text}</p>
                    </div>
                  );
                })}
              </div>

              <div className="mt-6 rounded-[28px] border border-[#DADCE0] bg-white px-5 py-5">
                <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">
                  Continue exploring
                </p>
                <div className="mt-4 grid gap-3">
                  <Link
                    href="/docs"
                    className="group flex items-center justify-between rounded-2xl border border-[#E5EAF1] bg-[#F8FBFF] px-4 py-3 text-sm font-medium text-[#202124] transition-all hover:-translate-y-0.5 hover:bg-white"
                  >
                    Documentation overview
                    <ArrowRight size={16} className="text-[#1A73E8] transition-transform group-hover:translate-x-0.5" />
                  </Link>
                  <Link
                    href="/pricing"
                    className="group flex items-center justify-between rounded-2xl border border-[#E5EAF1] bg-[#F8FBFF] px-4 py-3 text-sm font-medium text-[#202124] transition-all hover:-translate-y-0.5 hover:bg-white"
                  >
                    Pricing and quotas
                    <ArrowRight size={16} className="text-[#1A73E8] transition-transform group-hover:translate-x-0.5" />
                  </Link>
                  <a
                    href="https://github.com/graftai"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group flex items-center justify-between rounded-2xl border border-[#E5EAF1] bg-[#F8FBFF] px-4 py-3 text-sm font-medium text-[#202124] transition-all hover:-translate-y-0.5 hover:bg-white"
                  >
                    GitHub organization
                    <GitBranch size={16} className="text-[#1A73E8] transition-transform group-hover:translate-x-0.5" />
                  </a>
                </div>
              </div>
            </MarketingCard>
          </motion.div>
        </div>
      </section>
    </MarketingShell>
  );
}
