"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";
import Link from "next/link";
import {
  Calendar,
  MessageSquare,
  Sparkles,
  ShieldCheck,
  Clock,
  Zap,
} from "lucide-react";

interface AuthLayoutProps {
  children: ReactNode;
  title: string;
  subtitle?: string;
}

const highlights = [
  {
    icon: Calendar,
    title: "Calendar-aware",
    text: "Keep your scheduling context in sync across devices.",
    tone: "blue" as const,
  },
  {
    icon: MessageSquare,
    title: "Copilot ready",
    text: "Move from chat to action without losing the thread.",
    tone: "green" as const,
  },
  {
    icon: ShieldCheck,
    title: "Private by default",
    text: "Secure sign-in and simple, low-friction access.",
    tone: "amber" as const,
  },
];

const toneMap = {
  blue: {
    iconBg: "bg-[#E8F0FE]",
    iconColor: "text-[#1A73E8]",
    border: "border-[#D2E3FC]",
  },
  green: {
    iconBg: "bg-[#E6F4EA]",
    iconColor: "text-[#137333]",
    border: "border-[#CDE7D6]",
  },
  amber: {
    iconBg: "bg-[#FEF7E0]",
    iconColor: "text-[#E37400]",
    border: "border-[#F9E0B5]",
  },
};

const stats = [
  { value: "99.9%", label: "Uptime" },
  { value: "<80ms", label: "Avg latency" },
  { value: "256-bit", label: "Encryption" },
];

export function AuthLayout({ children, title, subtitle }: AuthLayoutProps) {
  return (
    <div className="min-h-dvh flex flex-col bg-[#F8F9FA] selection:bg-[#D2E3FC] relative overflow-hidden">
      {/* Ambient background glows */}
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <div className="absolute -top-32 -left-24 w-72 h-72 rounded-full bg-[#1A73E8]/8 blur-[100px]" />
        <div className="absolute -bottom-32 -right-20 w-72 h-72 rounded-full bg-[#34A853]/6 blur-[100px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-white/40 blur-[120px]" />
      </div>

      {/* Mobile-first: single column stacks, lg: side-by-side bento */}
      <div className="relative z-10 flex flex-1 items-center justify-center px-4 py-8 sm:px-6 sm:py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: "easeOut" }}
          className="w-full max-w-[1080px]"
        >
          {/* ─── Bento Grid ─── */}
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.1fr] gap-4 lg:gap-5">

            {/* ─── LEFT: Brand Panel ─── */}
            <div className="flex flex-col gap-4 order-2 lg:order-1">

              {/* Brand Hero Card */}
              <div className="rounded-3xl border border-[#DADCE0] bg-white p-6 sm:p-8 shadow-[0_1px_3px_rgba(60,64,67,0.08)]">
                {/* Badge */}
                <div className="flex items-center gap-2 mb-5">
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-[#E8F0FE] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-[#1967D2]">
                    <Sparkles size={11} />
                    GraftAI Workspace
                  </span>
                </div>

                <h2 className="text-[1.65rem] sm:text-[1.85rem] leading-[1.1] font-medium tracking-[-0.03em] text-[#202124]">
                  One account for scheduling, chat, and follow-up.
                </h2>

                <p className="mt-3 text-[15px] leading-relaxed text-[#5F6368] max-w-sm">
                  Sign in once and keep your calendar, AI copilot, and
                  automation context in one place. Less switching, more momentum.
                </p>
              </div>

              {/* ─── Feature Highlights Bento ─── */}
              <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-1 gap-3">
                {highlights.map((item) => {
                  const Icon = item.icon;
                  const tone = toneMap[item.tone];
                  return (
                    <div
                      key={item.title}
                      className={`flex gap-3.5 items-start rounded-2xl border ${tone.border} bg-white p-4 shadow-[0_1px_2px_rgba(60,64,67,0.06)] transition-all hover:shadow-[0_2px_8px_rgba(60,64,67,0.1)]`}
                    >
                      <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${tone.iconBg} ${tone.iconColor}`}>
                        <Icon size={16} />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-[#202124]">
                          {item.title}
                        </p>
                        <p className="mt-0.5 text-[13px] leading-snug text-[#5F6368]">
                          {item.text}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* ─── Stats Bar ─── */}
              <div className="hidden lg:grid grid-cols-3 gap-3">
                {stats.map((stat) => (
                  <div
                    key={stat.label}
                    className="rounded-2xl border border-[#DADCE0] bg-[#F8F9FA] px-4 py-3 text-center"
                  >
                    <p className="text-lg font-semibold text-[#202124]">{stat.value}</p>
                    <p className="text-[11px] font-medium text-[#5F6368] uppercase tracking-wider mt-0.5">{stat.label}</p>
                  </div>
                ))}
              </div>

              {/* ─── Pill Tags ─── */}
              <div className="hidden lg:flex flex-wrap gap-2">
                {["Calendar sync", "Mobile-first", "Private access", "AI copilot"].map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full border border-[#DADCE0] bg-white px-3 py-1.5 text-[11px] font-medium text-[#5F6368]"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            {/* ─── RIGHT: Auth Form Card ─── */}
            <div className="flex flex-col gap-4 order-1 lg:order-2">
              <div className="rounded-3xl border border-[#DADCE0] bg-white p-6 sm:p-8 shadow-[0_1px_3px_rgba(60,64,67,0.08)] flex flex-col items-center">
                {/* Logo + security badge row */}
                <div className="flex w-full items-center justify-between mb-6">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#1A73E8] text-white text-xl font-bold shadow-sm">
                    G
                  </div>
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-[#E6F4EA] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-[#137333]">
                    <ShieldCheck size={11} />
                    Secure session
                  </span>
                </div>

                {/* Title */}
                <h1 className="text-2xl sm:text-[1.75rem] font-medium text-[#202124] text-center tracking-[-0.02em]">
                  {title}
                </h1>

                {subtitle && (
                  <p className="mt-2 text-[15px] text-[#5F6368] text-center max-w-xs leading-relaxed">
                    {subtitle}
                  </p>
                )}

                {/* Auth form content */}
                <div className="w-full mt-7">
                  {children}
                </div>
              </div>

              {/* ─── Trust Signals Card (mobile: below form, desktop: below form) ─── */}
              <div className="rounded-2xl border border-[#DADCE0] bg-white/80 p-4 flex items-center gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#E8F0FE] text-[#1A73E8]">
                  <Zap size={18} />
                </div>
                <div>
                  <p className="text-sm font-medium text-[#202124]">Lightning-fast setup</p>
                  <p className="text-[12px] text-[#5F6368] mt-0.5">
                    Connect your calendar and start scheduling in under 60 seconds.
                  </p>
                </div>
              </div>

              {/* ─── Quick Stats (mobile-only) ─── */}
              <div className="grid grid-cols-3 gap-3 lg:hidden">
                {stats.map((stat) => (
                  <div
                    key={stat.label}
                    className="rounded-2xl border border-[#DADCE0] bg-white px-3 py-2.5 text-center"
                  >
                    <p className="text-base font-semibold text-[#202124]">{stat.value}</p>
                    <p className="text-[10px] font-medium text-[#5F6368] uppercase tracking-wider mt-0.5">{stat.label}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ─── Footer ─── */}
          <div className="mt-5 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 px-2">
            <Link
              href="/terms"
              className="text-[12px] font-medium text-[#5F6368] hover:text-[#202124] transition-colors"
            >
              Terms
            </Link>
            <Link
              href="/privacy"
              className="text-[12px] font-medium text-[#5F6368] hover:text-[#202124] transition-colors"
            >
              Privacy
            </Link>
            <span className="flex items-center gap-1.5 text-[12px] font-medium text-[#5F6368]">
              <Clock size={12} />
              24/7 Support
            </span>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
