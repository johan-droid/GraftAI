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
      title="INIT_AUTH_SEQUENCE"
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
          AUTH_CONSENT: By proceeding, you accept the{" "}
          <Link href="/terms" style={{ color: "var(--primary)", textDecoration: "none" }}>ENFORCE_TERMS</Link>
          {" "}AND{" "}
          <Link href="/privacy" style={{ color: "var(--primary)", textDecoration: "none" }}>PRIVACY_PROTOCOL</Link>.
        </Typography>
      </Box>
    </AuthLayout>
  );
}
