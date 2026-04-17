"use client";

import { StaticPageLayout } from "@/components/layout/StaticPageLayout";

export default function PrivacyPage() {
  return (
    <StaticPageLayout
      title="Privacy Policy"
      subtitle="How we protect your data and your time"
      lastUpdated="December 2024"
    >
      <h3>1. Introduction</h3>
      <p>
        At GraftAI, we take your privacy seriously. This policy explains how we collect, use, and protect your information when you use our AI-powered scheduling assistant.
      </p>

      <h3>2. What information we collect</h3>
      <p>We only collect what we need to make your scheduling experience amazing:</p>
      <ul>
        <li><strong>Account Info:</strong> Your name, email, and basic profile details.</li>
        <li><strong>Calendar Data:</strong> Your schedule and event preferences so we can find the best meeting times.</li>
        <li><strong>Usage Data:</strong> How you interact with the app so we can keep improving.</li>
        <li><strong>Device Info:</strong> Basic technical details to keep your account secure.</li>
      </ul>

      <h3>3. How we use your data</h3>
      <p>We use your information to help you get more done:</p>
      <ul>
        <li>Providing and maintaining your scheduling services.</li>
        <li>Learning your preferences to suggest better meeting times.</li>
        <li>Syncing your calendar across all your devices.</li>
        <li>Keeping the platform safe and secure.</li>
      </ul>

      <h3>4. Your Calendar Data</h3>
      <p>GraftAI needs access to your calendar to work its magic. We use this access strictly to:</p>
      <ul>
        <li>Find available times for your meetings.</li>
        <li>Protect your &quot;Deep Work&quot; focus time.</li>
        <li>Keep your schedule in sync everywhere.</li>
      </ul>
      <p><strong>Important:</strong> We never sell your calendar data to advertisers or third parties.</p>

      <h3>5. Security</h3>
      <p>We use industry-standard security to keep your data safe:</p>
      <ul>
        <li><strong>Encryption:</strong> Your data is encrypted whether it&apos;s sitting on our servers or traveling to your device.</li>
        <li><strong>Safe Access:</strong> We use secure login methods like Google and Outlook.</li>
        <li><strong>Regular Audits:</strong> We constantly check our systems for any security risks.</li>
      </ul>

      <h3>6. Data Retention</h3>
      <p>
        We keep your data as long as your account is active. If you decide to leave us, you can delete your account and all your data at any time.
      </p>

      <h3>7. Your Rights</h3>
      <p>You&apos;re in control of your data. You have the right to:</p>
      <ul>
        <li>See what data we have about you.</li>
        <li>Fix any mistakes in your information.</li>
        <li>Ask us to delete your data.</li>
        <li>Take your data with you if you decide to leave.</li>
      </ul>

      <h3>8. Third-Party Services</h3>
      <p>
        If you connect with services like Google or Microsoft, their own privacy policies apply. We only ask for the minimum access we need to help manage your schedule.
      </p>

      <h3>9. Children&apos;s Privacy</h3>
      <p>GraftAI is for professionals and teams. We don&apos;t knowingly collect information from anyone under the age of 13.</p>

      <h3>10. Changes to This Policy</h3>
      <p>We might update this policy from time to time. If we make big changes, we&apos;ll let you know inside the app or via email.</p>

      <h3>11. Contact Us</h3>
      <p>If you have any questions about your privacy, we&apos;re here to help:</p>
      <p>
        <strong>Email:</strong> hi@graftai.com<br />
        <strong>Address:</strong> 123 Tech Street, San Francisco, CA 94105
      </p>
    </StaticPageLayout>
  );
}
