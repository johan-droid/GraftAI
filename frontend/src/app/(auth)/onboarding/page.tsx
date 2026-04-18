"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Box, CircularProgress, Stack, Typography } from "@mui/material";
import { AuthLayout } from "@/components/auth/AuthLayout";
// Profile setup check removed - redirecting directly to dashboard
// import { getProfileSetupStatus } from "@/lib/api";

export default function OnboardingPage() {
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;

    const resolveDestination = async () => {
      try {
        // Skip profile setup check and always redirect to dashboard
        // Profile setup can be completed later from settings
        if (!cancelled) {
          router.replace("/dashboard");
        }
      } catch (error) {
        console.error("Failed to resolve onboarding destination:", error);
        if (!cancelled) {
          router.replace("/dashboard");
        }
      }
    };

    void resolveDestination();

    return () => {
      cancelled = true;
    };
  }, [router]);

  return (
    <AuthLayout title="Resolving your account">
      <Box sx={{ py: 6 }}>
        <Stack spacing={2.5} alignItems="center" textAlign="center">
          <CircularProgress size={28} sx={{ color: "var(--primary)" }} />
          <Typography sx={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>
            Checking your account state.
          </Typography>
          <Typography sx={{ fontSize: 13, color: "var(--text-secondary)", maxWidth: 420 }}>
            You will be sent to the right place based on your saved profile status.
          </Typography>
        </Stack>
      </Box>
    </AuthLayout>
  );
}
