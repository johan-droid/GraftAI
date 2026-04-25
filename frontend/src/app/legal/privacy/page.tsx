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
        <section className="mb-8">
          <h2 className="text-xl font-bold text-white mb-4">Google Workspace APIs and Limited Use Policy</h2>
          <p className="text-slate-300 mb-4">
            GraftAI allows users to connect their Google Calendar to facilitate automated scheduling. When you authenticate with Google, we request access to your calendar data. 
          </p>
          <ul className="list-disc pl-6 mb-4 text-slate-300 space-y-2">
            <li><strong>What we collect:</strong> We access your calendar event start and end times, and availability status.</li>
            <li><strong>How we use it:</strong> We use this data strictly to identify scheduling conflicts, prevent double-bookings, and automatically create new calendar events when an attendee books a time with you.</li>
            <li><strong>What we do not do:</strong> We do not sell your Google data to third-party advertisers. <strong>We do not use your personal Google Calendar data to train our underlying Artificial Intelligence or Large Language Models.</strong></li>
          </ul>
          
          {/* THIS IS THE MANDATORY GOOGLE CLAUSE. DO NOT ALTER THIS SENTENCE. */}
          <div className="p-4 bg-gray-800 border-l-4 border-blue-600 rounded-r-md mt-6 text-sm text-slate-300">
            <p>
              GraftAI&apos;s use and transfer to any other app of information received from Google APIs will adhere to the{' '}
              <a 
                href="https://developers.google.com/terms/api-services-user-data-policy" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-400 hover:underline font-medium"
              >
                Google API Services User Data Policy
              </a>
              , including the Limited Use requirements.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}