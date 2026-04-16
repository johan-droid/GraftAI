"use client";

import { StaticPageLayout } from "@/components/layout/StaticPageLayout";
import { Box, Typography } from "@mui/material";

export default function TermsOfServicePage() {
  return (
    <StaticPageLayout
      title="Terms of Service"
      subtitle="GRAFT_AI :: SYSTEM_USAGE_PROTOCOL"
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
        <strong>Academic Disclaimer:</strong> GraftAI is a 4th-year computer science project. This application is constructed for academic and portfolio purposes. <strong>It is not a commercial product.</strong> All rights and trademarks related to underlying third-party services are reserved to their respective providers.
      </Box>

      <h3>1. Protocol Acceptance</h3>
      <p>By establishing an uplink with the GraftAI platform, you acknowledge that you are interacting with an academic, non-commercial software orchestration project. You agree to use the service strictly for evaluation and demonstration purposes within the prescribed security boundaries.</p>

      <h3>2. Description of Orchestration</h3>
      <p>
        GraftAI is a web application designed to demonstrate the integration of Large Language Models with calendar orchestration systems. The service is provided "as-is" and "as-available" without warranties of any kind. There are no guarantees regarding system uptime, data persistence, or algorithmic accuracy.
      </p>

      <h3>3. Intellectual Property Handshake</h3>
      <p>
        All third-party services, APIs, logos, and trademarks accessed through this platform (including but not limited to OpenAI, Anthropic, Google Calendar, and Microsoft Graph) remain the exclusive property of their respective owners. The orchestration logic and interface designs created for this project are part of an academic portfolio.
      </p>

      <h3>4. Operative Conduct</h3>
      <p>
        Operatives agree not to:
      </p>
      <ul>
        <li>Overload system nodes or attempt to bypass prescribed rate limits.</li>
        <li>Inject malicious payloads or corrupted prompts into the AI core.</li>
        <li>Utilize demonstration payment flows with real financial credentials.</li>
      </ul>

      <h3>5. Limitation of Liability</h3>
      <p>
        Under no circumstances shall the architects or the affiliated academic institution be liable for any direct, indirect, incidental, or consequential damages resulting from the usage or downtime of the GraftAI platform.
      </p>

      <h3>6. Command Communications</h3>
      <p>
        For inquiries or feedback regarding this student project, please establish communication via the GitHub repository or the lead architect's portfolio contact system.
      </p>
    </StaticPageLayout>
  );
}
