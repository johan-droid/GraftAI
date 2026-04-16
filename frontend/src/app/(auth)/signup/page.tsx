"use client";

import { Box, Typography } from "@mui/material";
import Link from "next/link";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { OAuthButtons } from "@/components/auth/OAuthButtons";

export default function SignupPage() {
  return (
    <AuthLayout
      title="CREATE_ACCOUNT"
      subtitle="GRAFT_AI :: SECURE_KERNEL_ACCESS_GATEWAY"
    >
      <Box sx={{ mt: 2 }}>
        <OAuthButtons callbackURL="/dashboard" />
      </Box>

      <Box sx={{ mt: 6, textAlign: "center" }}>
        <Typography
          sx={{
            fontSize: "10px",
            color: "var(--text-faint)",
            maxWidth: "320px",
            mx: "auto",
            lineHeight: 1.6,
            fontFamily: "var(--font-mono)",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          By creating an account, you accept the {" "}
          <Link href="/terms" style={{ color: "var(--primary)", textDecoration: "none" }}>ENFORCE_TERMS</Link>
          {" "}AND{" "}
          <Link href="/privacy" style={{ color: "var(--primary)", textDecoration: "none" }}>PRIVACY_PROTOCOL</Link>.
        </Typography>
        <Typography sx={{ mt: 4, fontSize: "10px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
          Already have an account? {" "}
          <Link href="/login" style={{ color: "var(--primary)", textDecoration: "none" }}>Sign in</Link>
        </Typography>
      </Box>
    </AuthLayout>
  );
}
