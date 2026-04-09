import Link from "next/link";
import { ArrowLeft, BookOpenText, CalendarClock, Code2, ShieldCheck, Workflow } from "lucide-react";

const sections = [
  {
    icon: <Workflow className="h-5 w-5 text-indigo-300" />,
    title: "Architecture",
    body: "GraftAI runs as a high-performance monolith: FastAPI backend, Next.js frontend, async SQLAlchemy models, and worker-driven async jobs for non-blocking workflows.",
    bullets: [
      "FastAPI + SQLAlchemy async models",
      "Public booking routes with signed action tokens",
      "Worker cron for calendar and booking reminders",
    ],
  },
  {
    icon: <CalendarClock className="h-5 w-5 text-emerald-300" />,
    title: "Booking Flow",
    body: "Public booking supports availability calculation, conflict prevention, confirmations, reschedule, and cancellation with email lifecycle updates.",
    bullets: [
      "Timezone-aware slot generation",
      "Tokenized attendee management links",
      "Calendar event synchronization on booking updates",
    ],
  },
  {
    icon: <ShieldCheck className="h-5 w-5 text-sky-300" />,
    title: "Security Baseline",
    body: "Security headers, trusted host checks, auth token validation, and per-route rate limiting protect critical API workflows.",
    bullets: [
      "HSTS and strict content-type/frame policies",
      "Public action token verification (HMAC)",
      "Rate limits for booking and availability endpoints",
    ],
  },
  {
    icon: <Code2 className="h-5 w-5 text-amber-300" />,
    title: "Embed Widget",
    body: "Embed booking directly into external websites through the GraftAI embed loader and dedicated iframe route.",
    bullets: [
      "Drop-in script: /graftai-embed.js",
      "Autoload with data-graftai-embed container",
      "Direct route support: /embed/{username}/{eventType}",
    ],
  },
];

export default function DocsPage() {
  return (
    <main className="min-h-screen bg-[#070711] text-slate-200">
      <div className="mx-auto w-full max-w-5xl px-5 py-20 sm:px-8 sm:py-24">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm font-medium text-slate-400 transition-colors hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Home
        </Link>

        <div className="mt-8 rounded-3xl border border-white/10 bg-white/[0.02] p-6 sm:p-8">
          <div className="flex items-start gap-3">
            <span className="mt-1 rounded-xl border border-white/10 bg-white/5 p-2">
              <BookOpenText className="h-5 w-5 text-violet-300" />
            </span>
            <div>
              <h1 className="text-3xl font-black tracking-tight text-white sm:text-4xl">GraftAI Documentation</h1>
              <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-400 sm:text-base">
                Technical documentation for the current implementation track. This page summarizes architecture,
                booking lifecycle behavior, operational safety, and rollout conventions.
              </p>
            </div>
          </div>
        </div>

        <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {sections.map((section) => (
            <article
              key={section.title}
              className="rounded-3xl border border-white/10 bg-white/[0.02] p-5 sm:p-6"
            >
              <div className="mb-3 flex items-center gap-2">
                {section.icon}
                <h2 className="text-lg font-bold text-white">{section.title}</h2>
              </div>
              <p className="text-sm leading-relaxed text-slate-400">{section.body}</p>
              <ul className="mt-4 space-y-2 text-sm text-slate-300">
                {section.bullets.map((bullet) => (
                  <li key={bullet} className="flex items-start gap-2">
                    <span className="mt-1 h-1.5 w-1.5 rounded-full bg-indigo-400" />
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </section>

        <section className="mt-8 rounded-3xl border border-indigo-500/20 bg-indigo-500/10 p-6 sm:p-8">
          <h2 className="text-xl font-bold text-white">Operational Notes</h2>
          <p className="mt-3 text-sm leading-relaxed text-indigo-100/80">
            For production readiness, keep reminders enabled in workers, monitor email delivery logs,
            and verify public booking token flow after any auth or route refactor.
          </p>
          <div className="mt-5 flex flex-wrap gap-3 text-sm">
            <Link href="/pricing" className="rounded-xl bg-white px-4 py-2 font-semibold text-black hover:bg-slate-200">
              View Plans
            </Link>
            <Link href="/privacy-policy" className="rounded-xl border border-white/20 bg-white/5 px-4 py-2 font-semibold text-white hover:bg-white/10">
              Privacy Policy
            </Link>
            <Link href="/terms-of-service" className="rounded-xl border border-white/20 bg-white/5 px-4 py-2 font-semibold text-white hover:bg-white/10">
              Terms of Service
            </Link>
          </div>

          <div className="mt-6 rounded-2xl border border-white/20 bg-black/20 p-4 sm:p-5">
            <p className="text-xs uppercase tracking-[0.2em] text-indigo-200">Embed Snippet</p>
            <pre className="mt-3 overflow-x-auto rounded-xl bg-black/40 p-3 text-xs text-indigo-100 sm:text-sm">
{`<div data-graftai-embed data-username="jane" data-event-type="intro-call"></div>
<script src="https://www.graftai.tech/graftai-embed.js" defer></script>`}
            </pre>
          </div>
        </section>
      </div>
    </main>
  );
}
