import Link from "next/link";
import { Scale, ShieldAlert, Gavel, ArrowLeft } from "lucide-react";

export default function TermsAndConditionsPage() {
  return (
    <main className="page-with-floating-nav min-h-screen bg-slate-950 px-5 pb-16 text-slate-100 sm:px-6 md:px-8">
      <div className="mx-auto w-full max-w-4xl">
        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-200 transition hover:bg-slate-800"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Home
        </Link>

        <header className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/80 p-6 sm:p-8">
          <p className="inline-flex items-center gap-2 rounded-lg bg-indigo-500/15 px-3 py-1 text-xs font-bold uppercase tracking-wide text-indigo-200">
            <Scale className="h-4 w-4" /> Legal Document
          </p>
          <h1 className="mt-4 text-3xl font-black sm:text-4xl">Terms of Service</h1>
          <p className="mt-3 text-sm leading-relaxed text-slate-300 sm:text-base">
            Effective date: April 4, 2026. These Terms govern your access to and use of GraftAI,
            a fourth-year major project and software engineering demonstration platform.
          </p>
        </header>

        <section className="mt-6 space-y-4">
          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-lg font-bold text-white">1. Acceptance of Terms</h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">
              By creating an account, accessing, or using GraftAI, you agree to these Terms and
              applicable laws. If you do not agree, you must discontinue use of the platform.
            </p>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-lg font-bold text-white">2. Eligibility and Academic Scope</h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">
              GraftAI is built for educational demonstration, academic review, and controlled
              productivity workflows. Availability, feature set, and integrations may evolve as part
              of project milestones, evaluations, and supervised deployment exercises.
            </p>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-lg font-bold text-white">3. Permitted and Prohibited Use</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-300">
              <li>You may use the platform for lawful scheduling, collaboration, and project testing.</li>
              <li>You must not attempt unauthorized access, abuse APIs, or disrupt service operation.</li>
              <li>You must not upload unlawful, harmful, or malicious content.</li>
              <li>You must not perform reverse engineering except where law expressly permits it.</li>
            </ul>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="inline-flex items-center gap-2 text-lg font-bold text-white">
              <ShieldAlert className="h-5 w-5 text-amber-300" /> 4. Accounts, Security, and Integrations
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">
              You are responsible for account credentials and any actions taken through your account.
              If you connect third-party services (such as calendar providers), you grant permission
              for required scoped access. Suspicious activity must be reported promptly.
            </p>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="inline-flex items-center gap-2 text-lg font-bold text-white">
              <Gavel className="h-5 w-5 text-cyan-300" /> 5. Intellectual Property and License
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">
              Unless otherwise specified, source code, design assets, and project branding remain the
              property of the project authors and contributors. You receive a limited, revocable,
              non-exclusive right to use the platform for its intended purposes.
            </p>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-lg font-bold text-white">6. Disclaimers and Limitation of Liability</h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">
              The service is provided &quot;as is&quot; and &quot;as available&quot; without warranties of uninterrupted
              operation, fitness for a specific purpose, or error-free performance. To the extent
              permitted by law, project authors are not liable for indirect or consequential losses.
            </p>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-lg font-bold text-white">7. Changes to Terms and Contact</h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">
              These Terms may be updated as project requirements and compliance expectations evolve.
              Continued use after updates constitutes acceptance of revised Terms. For legal or
              governance queries, contact project.graftai@college.example.
            </p>
          </article>
        </section>
      </div>
    </main>
  );
}
