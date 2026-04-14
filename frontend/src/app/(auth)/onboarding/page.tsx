"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Box, CircularProgress, Stack, Typography } from "@mui/material";
import { AuthLayout } from "@/components/auth/AuthLayout";

export default function OnboardingPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/profile/setup");
  }, [router]);

  return (
    <AuthLayout title="Redirecting to setup">
      <Box sx={{ py: 6 }}>
        <Stack spacing={2.5} alignItems="center" textAlign="center">
          <CircularProgress size={28} sx={{ color: "var(--primary)" }} />
          <Typography sx={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>
            Redirecting you to profile setup.
          </Typography>
          <Typography sx={{ fontSize: 13, color: "var(--text-secondary)", maxWidth: 420 }}>
            The new onboarding flow lives in one place so the setup steps stay consistent.
          </Typography>
        </Stack>
      </Box>
    </AuthLayout>
  );
}
