"use client";

import { StaticPageLayout } from "@/components/layout/StaticPageLayout";
import { Box, Typography } from "@mui/material";

export default function TermsPage() {
  return (
    <StaticPageLayout
      title="Terms of Service"
      subtitle="The simple rules for using GraftAI"
      lastUpdated="December 2024"
    >
      <h3>1. Acceptance of Terms</h3>
      <p>
        By using GraftAI, you agree to these terms. If you don't agree, please don't use the app. GraftAI provides AI-powered scheduling and calendar management services.
      </p>

      <h3>2. Our Services</h3>
      <p>
        GraftAI helps you manage your time, sync calendars, and coordinate meetings using smart AI. We're always working to improve the app, so features may change over time.
      </p>

      <h3>3. Your Account</h3>
      <p>
        To use GraftAI, you'll need to create an account. You're responsible for keeping your login information safe and for everything that happens under your account. If you think someone else has access to your account, let us know right away.
      </p>

      <h3>4. Acceptable Use</h3>
      <p>We want everyone to have a great experience. You agree not to:</p>
      <ul>
        <li>Use the app for anything illegal or harmful.</li>
        <li>Try to break or hack into our systems.</li>
        <li>Collect information about other users.</li>
        <li>Use the app to send spam or unsolicited messages.</li>
      </ul>

      <h3>5. Payments and Subscriptions</h3>
      <p>
        Some of our advanced features require a paid subscription. By signing up for a plan, you agree to the pricing and billing terms. Fees are generally non-refundable, but we'll work with you if there's a technical error.
      </p>

      <h3>6. Privacy</h3>
      <p>
        Your privacy is our priority. Check out our <a href="/privacy" style={{ color: "var(--primary)" }}>Privacy Policy</a> to see how we handle your data.
      </p>

      <h3>7. Intellectual Property</h3>
      <p>
        GraftAI and all its features are owned by us and are protected by law. Please don't copy or reuse our code or designs without permission.
      </p>

      <h3>8. Limitation of Liability</h3>
      <p>
        We work hard to make GraftAI perfect, but we can't guarantee it will always be error-free. We're not liable for any indirect or consequential damages if something goes wrong.
      </p>

      <h3>9. Changes to These Terms</h3>
      <p>
        We might update these terms from time to time. We'll post the new version here, and if you keep using the app, it means you're okay with the changes.
      </p>

      <h3>10. Contact Us</h3>
      <p>
        Got questions? We're here to help at <strong>hi@graftai.com</strong>
      </p>
    </StaticPageLayout>
  );
}
