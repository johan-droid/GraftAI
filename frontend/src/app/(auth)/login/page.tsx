"use client";

import { Box, Typography, Stack } from "@mui/material";
import { motion } from "framer-motion";
import Link from "next/link";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { OAuthButtons } from "@/components/auth/OAuthButtons";
import { Lock, Shield, Cpu } from "lucide-react";

export default function LoginPage() {
  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to your GraftAI workspace"
    >
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
      >
        <Stack spacing={4}>
          <Box sx={{ textAlign: "center", mb: 2 }}>
            <Typography
              sx={{
                fontSize: "12px",
                color: "var(--text-secondary)",
                fontFamily: "var(--font-sans)",
                fontWeight: 600,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 1.5
              }}
            >
              Let's get you signed in
            </Typography>
          </Box>

          <OAuthButtons callbackURL="/dashboard" />

          <Box sx={{ mt: 2, textAlign: "center" }}>
            <Typography
              sx={{
                fontSize: "11px",
                color: "var(--text-faint)",
                lineHeight: 1.8,
                fontFamily: "var(--font-sans)",
              }}
            >
              By proceeding, you agree to our{" "}
              <Link href="/terms" style={{ color: "var(--primary)", textDecoration: "none", fontWeight: 700 }}>Terms of Service</Link>
              {" "}and{" "}
              <Link href="/privacy" style={{ color: "var(--primary)", textDecoration: "none", fontWeight: 700 }}>Privacy Policy</Link>.
            </Typography>
            
            <Box sx={{ mt: 4, pt: 4, borderTop: "1px solid var(--border-subtle)" }}>
              <Typography sx={{ fontSize: "12px", color: "var(--text-muted)", fontFamily: "var(--font-sans)", display: "flex", alignItems: "center", justifyContent: "center", gap: 1 }}>
                New here?{" "}
                <Link href="/signup" style={{ color: "var(--primary)", textDecoration: "none", fontWeight: 700 }}>Create an account</Link>
              </Typography>
            </Box>
          </Box>
        </Stack>
      </motion.div>
    </AuthLayout>
  );
}
