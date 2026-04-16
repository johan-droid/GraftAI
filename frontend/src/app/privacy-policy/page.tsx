"use client";

import { StaticPageLayout } from "@/components/layout/StaticPageLayout";
import { Box, Typography } from "@mui/material";

export default function PrivacyPolicyPage() {
  return (
    <StaticPageLayout
      title="Privacy Policy"
      subtitle="GRAFT_AI :: DATA_HANDLING_PROTOCOL"
      lastUpdated="APRIL 16, 2026"
    >
      <Box sx={{ 
        p: 3, 
        bgcolor: "rgba(0, 255, 156, 0.05)", 
        border: "1px solid rgba(0, 255, 156, 0.1)", 
        borderRadius: 1, 
        mb: 6,
        fontSize: "13px"
      }}>
        <strong>Academic Disclaimer:</strong> GraftAI is a 4th-year computer science project built for academic purposes. It is not a commercial product. All rights and trademarks for underlying services (OpenAI, Google, Microsoft, Stripe) are reserved to their respective providers.
      </Box>

      <h3>1. Information Acquisition</h3>
      <p>As an academic demonstration, data collection is strictly optimized for terminal functionality walkthroughs:</p>
      <ul>
        <li><strong>Identity Markers:</strong> Email addresses, profile names, and verified tokens retrieved during secure handshake protocols (Google/Microsoft OAuth).</li>
        <li><strong>Neural Logs:</strong> AI interaction histories, generated schedules, and mock event data created during session activity.</li>
      </ul>

      <h3>2. Utilization of Data</h3>
      <p>Your data flows through a secured sandbox environment exclusively to:</p>
      <ul>
        <li>Demonstrate advanced AI-Calendar orchestration cycles.</li>
        <li>Authorize secure access to personal orchestration dashboards.</li>
        <li>Validate system performance and algorithmic precision.</li>
      </ul>
      <p>We operate on a zero-monetization policy. Your internal data is never traded, leased, or transmitted to commercial marketing entities.</p>

      <h3>3. Third-Party Neural Networks</h3>
      <p>
        This platform acts as an orchestration proxy for third-party LLM providers. Please be advised that data transmitted during "Copilot" sessions is processed by external neural nodes. Do not submit sensitive military-grade or highly confidential intel to the AI beyond standard testing parameters.
      </p>

      <h3>4. Hibernation & Erasure</h3>
      <p>
        Operatives retain the right to complete session erasure. As this is a terminal-based academic project, the central database undergoes periodic purge cycles. For immediate data neutralization, please trigger the 'Full Account Wipe' in your profile settings or reach out to the project architects.
      </p>

      <h3>5. Protocol Evolutions</h3>
      <p>The architects reserve the right to evolve this protocol as the project enters new development phases. Continued platform uplink constitutes agreement with current and future protocol revisions.</p>
    </StaticPageLayout>
  );
}
