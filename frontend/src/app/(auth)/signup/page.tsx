"use client";

import { Box, Typography } from "@mui/material";
import Link from "next/link";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { OAuthButtons } from "@/components/auth/OAuthButtons";

export default function SignupPage() {
  return (
    <AuthLayout
      title="Create your account"
      subtitle="Join GraftAI to get started"
    >
      <Box sx={{ mt: 1 }}>
        <OAuthButtons callbackURL="/dashboard" actionText="Sign up" />
      </Box>

      <Box sx={{ mt: 4, textAlign: "center" }}>
        <Typography
          sx={{
            fontSize: "12px",
            color: "var(--text-secondary, #444746)",
            maxWidth: "320px",
            mx: "auto",
            lineHeight: 1.5,
            fontFamily: "var(--font-sans, Roboto, sans-serif)",
          }}
        >
          By creating an account, you agree to the {" "}
          <Link href="/terms" style={{ color: "var(--primary, #1a73e8)", textDecoration: "none" }}>Terms of Service</Link>
          {" "}and{" "}
          <Link href="/privacy" style={{ color: "var(--primary, #1a73e8)", textDecoration: "none" }}>Privacy Policy</Link>.
        </Typography>
        
        <Box sx={{ mt: 5, pt: 4, display: "flex", justifyContent: "center" }}>
          <Typography 
            sx={{ 
              fontSize: "14px", 
              color: "var(--text-secondary, #444746)", 
              fontFamily: "var(--font-sans, Roboto, sans-serif)", 
            }}
          >
            Already have an account? {" "}
            <Link 
              href="/login" 
              style={{ 
                color: "var(--primary, #1a73e8)", 
                textDecoration: "none", 
                fontWeight: 500 
              }}
            >
              Sign in
            </Link>
          </Typography>
        </Box>
      </Box>
    </AuthLayout>
  );
}
