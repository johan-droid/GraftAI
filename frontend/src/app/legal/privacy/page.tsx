export default function PrivacyPolicy() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-24 text-slate-300">
      <h1 className="text-4xl font-bold text-white mb-8">Privacy Policy</h1>
      <div className="space-y-6 text-sm leading-relaxed">
        <p>Last updated: April 2026</p>
        <section>
          <h2 className="text-xl font-semibold text-white mb-4">1. Data Collection</h2>
          <p>We collect essential calendar metadata solely for scheduling purposes. We adhere to strict zero-retention policies where possible.</p>
        </section>
        <section>
          <h2 className="text-xl font-semibold text-white mb-4">2. Integration Permissions</h2>
          <p>Google and Microsoft OAuth tokens are encrypted at rest. We only request permissions necessary for core functionality.</p>
        </section>
      </div>
    </div>
  );
}