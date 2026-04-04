import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-[#070711] text-slate-200">
      <div className="max-w-3xl mx-auto px-5 py-24">
        <Link href="/" className="inline-flex items-center gap-2 text-sm font-medium text-slate-400 hover:text-white transition-colors mb-8">
          <ArrowLeft className="w-4 h-4" /> Back to Home
        </Link>
        <h1 className="text-4xl font-black text-white mb-4" style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}>
          Privacy Policy
        </h1>
        <p className="text-slate-400 text-sm mb-12">Last Updated: April 2026</p>

        <div className="prose prose-invert prose-slate max-w-none prose-headings:font-bold prose-a:text-indigo-400 hover:prose-a:text-indigo-300">
          <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 mb-8 text-indigo-200 text-sm">
            <strong>Disclaimer:</strong> GraftAI is a 4th-year college student computer science project. This application is constructed for academic and portfolio purposes. <strong>It is not a commercial product.</strong> All rights and trademarks related to underlying third-party API services (such as OpenAI, Anthropic, Google Calendar, Microsoft Graph, Razorpay, Stripe, etc.) are solely reserved to their respective providers.
          </div>

          <h3>1. Information We Collect</h3>
          <p>As this is an academic project, data collection is strictly limited to demonstrating functionality:</p>
          <ul>
            <li><strong>Authentication Data:</strong> User emails, profile names, and profile pictures when you sign in via Google, Microsoft, or Email.</li>
            <li><strong>Application Data:</strong> Generated schedules, mock events, and AI chat histories created during your use of the platform.</li>
          </ul>

          <h3>2. How We Use Information</h3>
          <p>Your data is used entirely within the sandbox environment of this platform to:</p>
          <ul>
            <li>Provide a seamless demonstration of the AI scheduling features.</li>
            <li>Allow you to access a personalized dashboard.</li>
            <li>We do not sell, rent, or monetize your data. </li>
          </ul>

          <h3>3. Third-Party Integrations</h3>
          <p>
            This application proxies requests to third-party Machine Learning providers and Authentication Providers. Please note that data sent to the AI Copilot is processed by these external APIs. We ask that you do not submit highly sensitive, confidential, or PII (Personally Identifiable Information) beyond what is required to test the software.
          </p>

          <h3>4. Data Deletion</h3>
          <p>
            You retain the right to have your data erased. Since this is an academic demonstration, the database may be periodically purged without notice. If you would like your data deleted immediately, please log out or contact the project developer.
          </p>

          <h3>5. Changes to This Policy</h3>
          <p>Changes might be made to this policy as the student project evolves. Continued use of GraftAI constitutes agreement with any revisions.</p>
        </div>
      </div>
    </div>
  );
}
