"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Box, Typography } from "@mui/material";
import { motion } from "framer-motion";
import { Mail, Lock, ArrowRight, Loader2, AlertCircle } from "lucide-react";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { OAuthButtons } from "@/components/auth/OAuthButtons";
import { FloatingInput } from "@/components/ui/FloatingInput";
import { GradientButton } from "@/components/ui/GradientButton";
import { signIn } from "next-auth/react";
import { toast } from "@/components/ui/Toast";

export default function LoginPage() {
  return (
    <AuthLayout
      title="Sign in to GraftAI"
      subtitle="The most powerful AI-first calendar and scheduling platform."
    >
      <Box sx={{ mt: 2 }}>
        <OAuthButtons callbackURL="/dashboard" />
      </Box>

      <Box sx={{ mt: 6, textAlign: "center" }}>
        <Typography
          sx={{
            fontSize: "0.875rem",
            color: "hsl(215, 16%, 50%)",
            maxWidth: "280px",
            mx: "auto",
            lineHeight: 1.6,
          }}
        >
          By signing in, you agree to our{" "}
          <Link href="/terms" style={{ color: "hsl(239, 84%, 67%)", textDecoration: "none" }}>Terms of Service</Link>
          {" "}and{" "}
          <Link href="/privacy" style={{ color: "hsl(239, 84%, 67%)", textDecoration: "none" }}>Privacy Policy</Link>.
        </Typography>
      </Box>
    </AuthLayout>
  );
}
