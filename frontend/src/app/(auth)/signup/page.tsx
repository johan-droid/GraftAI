"use client";

import { Box, Typography } from "@mui/material";
import Link from "next/link";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { OAuthButtons } from "@/components/auth/OAuthButtons";

export default function SignupPage() {
  return (
    <AuthLayout
      title="Create your account"
      subtitle="Join the future of smart scheduling"
    >
      <Box sx={{ mt: 2 }}>
        <OAuthButtons callbackURL="/dashboard" />
      </Box>

      <Box sx={{ mt: 6, textAlign: "center" }}>
        <Typography
          sx={{
            fontSize: "11px",
            color: "var(--text-faint)",
            maxWidth: "320px",
            mx: "auto",
            lineHeight: 1.6,
            fontFamily: "var(--font-sans)",
          }}
        >
          By creating an account, you agree to our {" "}
          <Link href="/terms" style={{ color: "var(--primary)", textDecoration: "none", fontWeight: 700 }}>Terms of Service</Link>
          {" "}and{" "}
          <Link href="/privacy" style={{ color: "var(--primary)", textDecoration: "none", fontWeight: 700 }}>Privacy Policy</Link>.
        </Typography>
        <Typography sx={{ mt: 4, fontSize: "12px", color: "var(--text-muted)", fontFamily: "var(--font-sans)" }}>
          Already have an account? {" "}
          <Link href="/login" style={{ color: "var(--primary)", textDecoration: "none", fontWeight: 700 }}>Sign in</Link>
        </Typography>
      </Box>
    </AuthLayout>
  );
}
