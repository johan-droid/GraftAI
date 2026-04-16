"use client";

import { StaticPageLayout } from "@/components/layout/StaticPageLayout";
import { Box, Typography } from "@mui/material";

export default function TermsAndConditionsPage() {
  return (
    <StaticPageLayout
      title="Terms of Service"
      subtitle="GRAFT_AI :: SYSTEM_USAGE_GOVERNANCE"
      lastUpdated="APRIL 2026"
    >
      <h3>1. Acceptance of Terms</h3>
      <p>
        By creating an account, accessing, or using GraftAI, you agree to be bound by these Terms and all applicable laws. If you do not agree to these parameters, you must discontinue use of the platform and neutralize your connection protocols.
      </p>

      <h3>2. Eligibility and Academic Scope</h3>
      <p>
        GraftAI is built for educational demonstration, academic review, and controlled productivity workflows. Availability, feature set, and integrations may evolve as part of project milestones, evaluations, and supervised deployment exercises.
      </p>

      <h3>3. Authorized Conduct Protocols</h3>
      <p>Operatives agree to utilize GraftAI within the following authorized boundaries:</p>
      <ul>
        <li>Engaging in lawful scheduling, collaboration, and project testing.</li>
        <li>No unauthorized intrusion attempts or API abuse.</li>
        <li>No harvesting of metadata from other platform operatives.</li>
        <li>Maintaining the integrity of provided AI orchestration logic.</li>
      </ul>

      <h3>4. Accounts and Security Integrations</h3>
      <p>
        You are responsible for the integrity of your authentication tokens and all actions taken through your terminal. Connection to third-party services (calendar providers) grants GraftAI "Least Privilege" access required for orchestration.
      </p>

      <h3>5. Intellectual Property Assets</h3>
      <p>
        Unless otherwise specified, the GraftAI kernel, design assets, and project branding remain the proprietary property of the project architects. You are granted a limited, revocable right to use the platform for its intended orchestration purposes.
      </p>

      <h3>6. Liability Buffers</h3>
      <p>
        The service is provided "as is" and "as available" without warranties of uninterrupted operation or total error-free performance. Project authors are not liable for indirect or consequential losses resulting from session downtime.
      </p>

      <h3>7. Protocol Evolution</h3>
      <p>
        These Terms may be updated as project requirements and compliance expectations evolve. Continued engagement after protocol updates constitutes acceptance of revised terms.
      </p>

      <h3>8. Support Uplink</h3>
      <p>
        For legal or governance inquiries, contact our lead architects via the support terminal or at project.graftai@college.example.
      </p>
    </StaticPageLayout>
  );
}
