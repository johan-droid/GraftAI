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
          <h1 className="mt-4 text-3xl font-black sm:text-4xl">Terms and Conditions</h1>
          <p className="mt-3 text-sm leading-relaxed text-slate-300 sm:text-base">
            Effective date: April 2, 2026. These Terms govern use of the GraftAI platform developed
            as a major college project and software engineering demonstration.
          </p>
        </header>

        <section className="mt-6 space-y-4">
          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-lg font-bold text-white">1. Acceptance of Terms</h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">
              By accessing or using GraftAI, you agree to these Terms and all applicable laws. If you do
              not agree, do not use the application.
            </p>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-lg font-bold text-white">2. Permitted Use</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-300">
              <li>Use the platform for lawful scheduling and productivity workflows.</li>
              <li>Do not attempt unauthorized access, reverse engineering, or service disruption.</li>
              <li>Do not upload harmful, illegal, or abusive content through the system.</li>
            </ul>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="inline-flex items-center gap-2 text-lg font-bold text-white">
              <ShieldAlert className="h-5 w-5 text-amber-300" /> 3. Accounts and Security
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">
              Users are responsible for maintaining account credential confidentiality. Suspicious activity
              should be reported immediately. GraftAI may suspend accounts that violate these Terms.
            </p>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="inline-flex items-center gap-2 text-lg font-bold text-white">
              <Gavel className="h-5 w-5 text-cyan-300" /> 4. Intellectual Property and Liability
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">
              Source code, branding, and content remain property of the project authors unless otherwise
              specified. The service is provided &quot;as is&quot; for educational and demonstration purposes,
              without warranties of uninterrupted or error-free operation.
            </p>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-lg font-bold text-white">5. Modifications and Contact</h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">
              Terms may be revised as project scope evolves. Continued use after updates indicates
              acceptance of revised Terms. For project governance questions, contact
              project.graftai@college.example.
            </p>
          </article>
        </section>
      </div>
    </main>
  );
}
