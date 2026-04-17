"use client";

import { Box, Typography, Stack } from "@mui/material";
import Link from "next/link";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { OAuthButtons } from "@/components/auth/OAuthButtons";

export default function LoginPage() {
  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to pick up your schedule, messages, and automations where you left off."
    >
      <Stack spacing={4}>
        <OAuthButtons callbackURL="/dashboard" actionText="Sign in" />

        <Box sx={{ mt: 2, textAlign: "center" }}>
          <Typography
            sx={{
              fontSize: "13px",
              color: "var(--text-secondary, #444746)",
              lineHeight: 1.5,
              fontFamily: "var(--font-sans, Roboto, sans-serif)",
            }}
          >
            On a shared device? A private window or quick sign-out keeps things tidy.
          </Typography>
          
          <Box sx={{ mt: 5, pt: 4, display: "flex", justifyContent: "center" }}>
            <Typography 
              sx={{ 
                fontSize: "14px", 
                color: "var(--text-secondary, #444746)", 
                fontFamily: "var(--font-sans, Roboto, sans-serif)", 
              }}
            >
              Don&apos;t have an account?{" "}
              <Link 
                href="/signup" 
                style={{ 
                  color: "var(--primary, #1a73e8)", 
                  textDecoration: "none", 
                  fontWeight: 500 
                }}
              >
                Create account
              </Link>
            </Typography>
          </Box>
        </Box>
      </Stack>
    </AuthLayout>
  );
}
