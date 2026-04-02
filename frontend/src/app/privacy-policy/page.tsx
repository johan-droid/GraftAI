import Link from "next/link";
import { FileText, ShieldCheck, Database, Lock, ArrowLeft } from "lucide-react";

export default function PrivacyPolicyPage() {
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
            <FileText className="h-4 w-4" /> Legal Document
          </p>
          <h1 className="mt-4 text-3xl font-black sm:text-4xl">Privacy Policy</h1>
          <p className="mt-3 text-sm leading-relaxed text-slate-300 sm:text-base">
            Effective date: April 2, 2026. This Privacy Policy explains how GraftAI collects, uses,
            secures, and manages information for this major college project and demonstration platform.
          </p>
        </header>

        <section className="mt-6 space-y-4">
          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-lg font-bold text-white">1. Information We Collect</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-300">
              <li>Account data such as name, email, and authentication identifiers.</li>
              <li>Calendar metadata required to provide scheduling and sync functionality.</li>
              <li>Operational logs (errors, request timing, status checks) for reliability monitoring.</li>
              <li>Consent choices submitted by users for analytics and communication preferences.</li>
            </ul>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="inline-flex items-center gap-2 text-lg font-bold text-white">
              <ShieldCheck className="h-5 w-5 text-emerald-300" /> 2. How We Use Data
            </h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-300">
              <li>Provide core scheduling, authentication, and integration features.</li>
              <li>Improve system stability, performance, and user experience.</li>
              <li>Maintain security controls and prevent misuse.</li>
              <li>Generate academic performance reports and project evaluation metrics.</li>
            </ul>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="inline-flex items-center gap-2 text-lg font-bold text-white">
              <Database className="h-5 w-5 text-cyan-300" /> 3. Data Retention and Sharing
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">
              Data is retained only as long as required for project operation, debugging, and assessment.
              GraftAI does not sell personal information. Limited data sharing may occur with service
              providers (for example hosting and email services) strictly to deliver platform features.
            </p>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="inline-flex items-center gap-2 text-lg font-bold text-white">
              <Lock className="h-5 w-5 text-amber-300" /> 4. User Rights
            </h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-300">
              <li>Request access to account data used by the application.</li>
              <li>Request correction or deletion of inaccurate personal information.</li>
              <li>Withdraw optional consents where legally and technically feasible.</li>
            </ul>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-lg font-bold text-white">5. Contact for Privacy Queries</h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">
              For academic review or privacy concerns, contact: project.graftai@college.example
            </p>
          </article>
        </section>
      </div>
    </main>
  );
}
