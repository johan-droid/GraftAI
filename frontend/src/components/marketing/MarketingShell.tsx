"use client";

import type { ReactNode } from "react";
import { useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ArrowRight, Menu, ShieldCheck, Sparkles, X } from "lucide-react";

const navLinks = [
  { href: "/docs", label: "Documentation" },
  { href: "/developers", label: "Developers" },
  { href: "/pricing", label: "Pricing" },
];

function isActive(currentPath: string | undefined, href: string) {
  if (!currentPath) return false;
  return currentPath === href || currentPath.startsWith(`${href}/`);
}

export function MarketingShell({
  children,
  currentPath,
}: {
  children: ReactNode;
  currentPath?: string;
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const shouldReduceMotion = useReducedMotion();

  return (
    <div className="relative min-h-dvh overflow-hidden bg-[radial-gradient(circle_at_top,rgba(26,115,232,0.16),transparent_28%),radial-gradient(circle_at_86%_14%,rgba(52,168,83,0.12),transparent_18%),radial-gradient(circle_at_20%_82%,rgba(217,48,37,0.08),transparent_20%),linear-gradient(180deg,#EDF4FF_0%,#F7FAFF_38%,#FFFFFF_100%)] text-[#202124] selection:bg-[#D2E3FC]">
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.08)_1px,transparent_1px)] bg-[size:120px_120px] opacity-40" />
        <motion.div
          animate={
            shouldReduceMotion
              ? undefined
              : { x: [0, 28, 0], y: [0, 18, 0], opacity: [0.2, 0.28, 0.2] }
          }
          transition={
            shouldReduceMotion
              ? undefined
              : { duration: 18, repeat: Infinity, ease: "easeInOut" }
          }
          className="absolute -left-24 top-12 h-80 w-80 rounded-full bg-[#1A73E8]/18 blur-3xl"
        />
        <motion.div
          animate={
            shouldReduceMotion
              ? undefined
              : { x: [0, -18, 0], y: [0, 26, 0], opacity: [0.16, 0.24, 0.16] }
          }
          transition={
            shouldReduceMotion
              ? undefined
              : { duration: 20, repeat: Infinity, ease: "easeInOut" }
          }
          className="absolute right-[-5rem] top-28 h-72 w-72 rounded-full bg-[#34A853]/16 blur-3xl"
        />
      </div>

      <div className="sticky top-0 z-50 px-4 pt-3 sm:px-6 sm:pt-4">
        <nav className="mx-auto max-w-7xl rounded-full border border-white/60 bg-white/78 px-4 py-2.5 shadow-[0_18px_60px_-36px_rgba(32,33,36,0.32)] backdrop-blur-2xl">
          <div className="flex items-center justify-between gap-3">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#1A73E8] text-sm font-bold text-white shadow-[0_10px_24px_-12px_rgba(26,115,232,0.7)]">
                G
              </div>
              <div>
                <p className="text-base font-semibold tracking-tight text-[#202124]">GraftAI</p>
                <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">
                  Cinematic scheduling
                </p>
              </div>
            </Link>

            <div className="hidden items-center gap-1 rounded-full border border-white/70 bg-white/70 p-1 md:flex">
              <Link
                href="/"
                className={`rounded-full px-4 py-2 text-sm font-medium transition-all ${
                  currentPath === "/"
                    ? "bg-[#202124] text-white shadow-sm"
                    : "text-[#5F6368] hover:bg-white hover:text-[#202124]"
                }`}
              >
                Home
              </Link>
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`rounded-full px-4 py-2 text-sm font-medium transition-all ${
                    isActive(currentPath, link.href)
                      ? "bg-[#202124] text-white shadow-sm"
                      : "text-[#5F6368] hover:bg-white hover:text-[#202124]"
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="hidden rounded-full border border-[#DADCE0] bg-white px-4 py-2 text-sm font-medium text-[#1A73E8] shadow-sm transition-colors hover:bg-[#F8F9FA] sm:inline-flex"
              >
                Sign in
              </Link>
              <Link
                href="/signup"
                className="hidden items-center gap-2 rounded-full bg-[#1A73E8] px-4 py-2 text-sm font-medium text-white shadow-[0_14px_30px_-18px_rgba(26,115,232,0.9)] transition-all hover:bg-[#1557B0] sm:inline-flex"
              >
                Get started <ArrowRight size={16} />
              </Link>
              <button
                type="button"
                onClick={() => setMobileMenuOpen((open) => !open)}
                className="rounded-full p-2 text-[#5F6368] transition-colors hover:bg-[#F1F3F4] md:hidden"
                aria-label="Toggle menu"
              >
                {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            </div>
          </div>

          <AnimatePresence>
            {mobileMenuOpen && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden md:hidden"
              >
                <div className="flex flex-col gap-1 px-1 pb-2 pt-3">
                  {[{ href: "/", label: "Home" }, ...navLinks, { href: "/login", label: "Sign in" }].map((link) => (
                    <Link
                      key={link.href}
                      href={link.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`rounded-2xl px-4 py-3 text-sm font-medium transition-colors ${
                        link.href === "/" ? currentPath === "/" : isActive(currentPath, link.href)
                          ? "bg-[#202124] text-white"
                          : "text-[#5F6368] hover:bg-white hover:text-[#202124]"
                      }`}
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

      {children}

      <footer className="border-t border-white/70 bg-white/70 py-10 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 text-center sm:px-6 md:flex-row md:items-center md:justify-between md:text-left">
          <div className="flex items-center justify-center gap-3 md:justify-start">
            <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-[#202124] text-sm font-bold text-white">
              G
            </div>
            <div>
              <p className="text-sm font-semibold text-[#202124]">GraftAI</p>
              <p className="text-xs text-[#5F6368]">Built for calmer scheduling systems.</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-5 text-sm font-medium text-[#5F6368] md:justify-end">
            <Link href="/docs" className="transition-colors hover:text-[#202124]">
              Documentation
            </Link>
            <Link href="/developers" className="transition-colors hover:text-[#202124]">
              Developers
            </Link>
            <Link href="/pricing" className="transition-colors hover:text-[#202124]">
              Pricing
            </Link>
            <Link href="/privacy" className="transition-colors hover:text-[#202124]">
              Privacy
            </Link>
            <div className="inline-flex items-center gap-1.5 rounded-full border border-[#DADCE0] bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-[#5F6368]">
              <Sparkles size={12} className="text-[#1A73E8]" />
              Public beta
            </div>
            <div className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.2em] text-[#5F6368]">
              <ShieldCheck size={13} />
              Secure booking
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export function MarketingHero({
  eyebrow,
  title,
  description,
  primaryAction,
  secondaryAction,
  stats,
  aside,
}: {
  eyebrow: string;
  title: string;
  description: string;
  primaryAction?: ReactNode;
  secondaryAction?: ReactNode;
  stats?: { label: string; value: string }[];
  aside?: ReactNode;
}) {
  return (
    <section className="mx-auto max-w-7xl px-4 pb-10 pt-10 sm:px-6 sm:pb-14 sm:pt-14">
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)] lg:items-end">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="relative overflow-hidden rounded-[40px] border border-white/70 bg-white/78 p-7 shadow-[0_30px_90px_-56px_rgba(32,33,36,0.38)] backdrop-blur-2xl sm:p-10"
        >
          <div className="absolute inset-x-0 top-0 h-px bg-[linear-gradient(90deg,transparent,rgba(26,115,232,0.7),transparent)]" />
          <p className="inline-flex items-center rounded-full border border-[#D2E3FC] bg-[#EDF4FF] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.28em] text-[#1967D2]">
            {eyebrow}
          </p>
          <h1 className="mt-5 max-w-3xl text-[2.4rem] font-semibold leading-[0.98] tracking-[-0.05em] text-[#202124] sm:text-5xl lg:text-[4.3rem]">
            {title}
          </h1>
          <p className="mt-5 max-w-2xl text-sm leading-relaxed text-[#5F6368] sm:text-base">
            {description}
          </p>
          {(primaryAction || secondaryAction) && (
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              {primaryAction}
              {secondaryAction}
            </div>
          )}
          {stats?.length ? (
            <div className="mt-8 grid gap-3 sm:grid-cols-3">
              {stats.map((stat) => (
                <div
                  key={stat.label}
                  className="rounded-3xl border border-[#E5EAF1] bg-[#F8FBFF] px-4 py-4 shadow-[0_12px_30px_-28px_rgba(26,115,232,0.5)]"
                >
                  <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">
                    {stat.label}
                  </p>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-[#202124]">{stat.value}</p>
                </div>
              ))}
            </div>
          ) : null}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.08 }}
          className="h-full"
        >
          {aside}
        </motion.div>
      </div>
    </section>
  );
}

export function MarketingSectionHeading({
  kicker,
  title,
  description,
}: {
  kicker: string;
  title: string;
  description: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.45 }}
      className="max-w-2xl"
    >
      <p className="inline-flex items-center rounded-full border border-[#D2E3FC] bg-white px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.28em] text-[#1967D2] shadow-sm">
        {kicker}
      </p>
      <h2 className="mt-4 text-2xl font-semibold tracking-tight text-[#202124] sm:text-3xl lg:text-[2.1rem]">
        {title}
      </h2>
      <p className="mt-4 text-sm leading-relaxed text-[#5F6368] sm:text-base">
        {description}
      </p>
    </motion.div>
  );
}

export function MarketingCard({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`relative overflow-hidden rounded-[32px] border border-white/70 bg-white/82 p-6 shadow-[0_28px_80px_-56px_rgba(32,33,36,0.42)] backdrop-blur-2xl ${className}`}
    >
      <div className="absolute inset-x-0 top-0 h-px bg-[linear-gradient(90deg,transparent,rgba(26,115,232,0.5),transparent)]" />
      <div className="relative z-10">{children}</div>
    </div>
  );
}

