import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function TermsOfServicePage() {
  return (
    <div className="min-h-screen bg-[#070711] text-slate-200">
      <div className="max-w-3xl mx-auto px-5 py-24">
        <Link href="/" className="inline-flex items-center gap-2 text-sm font-medium text-slate-400 hover:text-white transition-colors mb-8">
          <ArrowLeft className="w-4 h-4" /> Back to Home
        </Link>
        <h1 className="text-4xl font-black text-white mb-4" style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}>
          Terms of Service
        </h1>
        <p className="text-slate-400 text-sm mb-12">Last Updated: April 2026</p>

        <div className="prose prose-invert prose-slate max-w-none prose-headings:font-bold prose-a:text-indigo-400 hover:prose-a:text-indigo-300">
          <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 mb-8 text-indigo-200 text-sm">
            <strong>Disclaimer:</strong> GraftAI is a 4th-year college student computer science project. This application is constructed for academic and portfolio purposes. <strong>It is not a commercial product.</strong> All rights and trademarks related to underlying third-party API services (such as OpenAI, Anthropic, Google Calendar, Microsoft Graph, Razorpay, Stripe, etc.) are solely reserved to their respective providers.
          </div>

          <h3>1. Acceptance of Terms</h3>
          <p>By accessing and using the GraftAI platform, you acknowledge that you are interacting with an academic, non-commercial software project. You agree to use the service strictly for evaluation and demonstration purposes.</p>

          <h3>2. Description of Service</h3>
          <p>
            GraftAI is a web application designed to showcase integrating AI language models with calendar orchestration. The service is provided "as-is" and "as-available" without warranties of any kind. There are no guarantees regarding uptime, data persistence, or algorithmic accuracy.
          </p>

          <h3>3. Intellectual Property Rights</h3>
          <p>
            All third-party services, APIs, logos, and trademarks accessed through this platform (including but not limited to generative AI platforms, calendar providers, and payment gateways) remain the exclusive property of their respective owners. The source code created for the orchestration logic is part of an academic portfolio.
          </p>

          <h3>4. User Conduct</h3>
          <p>
            Users agree not to:
          </p>
          <ul>
            <li>Abuse the system resources or attempt to bypass rate limits.</li>
            <li>Submit malicious prompts or payloads to the system.</li>
            <li>Use the demonstration payment flows (if any) with real payment details unless specifically instructed that it is a live sandbox testing mode.</li>
          </ul>

          <h3>5. Limitation of Liability</h3>
          <p>
            Under no circumstances shall the developer or the affiliated university be liable for any direct, indirect, incidental, or consequential damages resulting from the use or inability to use the GraftAI platform.
          </p>

          <h3>6. Contact</h3>
          <p>
            If you have any questions or feedback regarding this student project, please reach out via GitHub or the portfolio contact system of the developer.
          </p>
        </div>
      </div>
    </div>
  );
}
