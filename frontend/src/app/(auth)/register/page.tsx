"use client";

import { useState } from "react";
import Link from "next/link";
import { Box, Typography, Checkbox, FormControlLabel } from "@mui/material";
import { motion } from "framer-motion";
import { Mail, Lock, User, ArrowRight, Loader2, AlertCircle } from "lucide-react";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { OAuthButtons } from "@/components/auth/OAuthButtons";
import { FloatingInput } from "@/components/ui/FloatingInput";
import { GradientButton } from "@/components/ui/GradientButton";
import { PasswordStrength } from "@/components/ui/PasswordStrength";
import { toast } from "@/components/ui/Toast";

export default function RegisterPage() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!fullName.trim()) {
      setError("Please enter your full name");
      return;
    }
    if (!email.trim()) {
      setError("Please enter your email");
      return;
    }
    if (!password) {
      setError("Please enter a password");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (!agreeTerms) {
      setError("Please agree to the terms and conditions");
      return;
    }

    setIsLoading(true);

    try {
      setError("Local registration is currently disabled. Use Google or Microsoft to sign up.");
      toast.warning("Local registration is not supported at this time.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Join thousands of professionals who save hours every week with AI scheduling."
    >
      {/* Show OAuth first since that's the primary method */}
      <Box sx={{ mb: 4 }}>
        <OAuthButtons callbackURL="/dashboard" />
        <Typography sx={{ mt: 3, color: "hsl(215, 16%, 55%)", fontSize: "0.9rem" }}>
          Email registration is currently disabled. Please continue with Google or Microsoft sign-up.
        </Typography>
      </Box>

      {/* Divider */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 4 }}>
        <Box sx={{ flex: 1, height: 1, background: "hsla(239, 84%, 67%, 0.1)" }} />
        <Typography sx={{ fontSize: "0.875rem", color: "hsl(215, 16%, 40%)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
          Or with email
        </Typography>
        <Box sx={{ flex: 1, height: 1, background: "hsla(239, 84%, 67%, 0.1)" }} />
      </Box>

      <form onSubmit={handleSubmit}>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
          {/* Error Alert */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              <Box
                sx={{
                  p: 3,
                  background: "hsla(346, 84%, 61%, 0.1)",
                  border: "1px solid hsla(346, 84%, 61%, 0.3)",
                  borderRadius: "12px",
                  display: "flex",
                  alignItems: "center",
                  gap: 2,
                  color: "hsl(346, 84%, 61%)",
                }}
              >
                <AlertCircle size={20} />
                <Typography sx={{ fontSize: "0.9375rem" }}>{error}</Typography>
              </Box>
            </motion.div>
          )}

          {/* Full Name Field */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.3 }}
          >
            <FloatingInput
              label="Full Name"
              type="text"
              placeholder="John Doe"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              icon={User}
              disabled={isLoading}
              required
            />
          </motion.div>

          {/* Email Field */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.3 }}
          >
            <FloatingInput
              label="Email"
              type="email"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              icon={Mail}
              disabled={isLoading}
              required
            />
          </motion.div>

          {/* Password Field */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.3 }}
          >
            <FloatingInput
              label="Password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={Lock}
              isPassword
              disabled={isLoading}
              required
            />
            <PasswordStrength password={password} />
          </motion.div>

          {/* Terms Checkbox */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.3 }}
          >
            <FormControlLabel
              control={
                <Checkbox
                  checked={agreeTerms}
                  onChange={(e) => setAgreeTerms(e.target.checked)}
                  sx={{
                    color: "hsla(239, 84%, 67%, 0.3)",
                    "&.Mui-checked": {
                      color: "hsl(239, 84%, 67%)",
                    },
                  }}
                />
              }
              label={
                <Typography sx={{ fontSize: "0.875rem", color: "hsl(215, 16%, 55%)" }}>
                  I agree to the{" "}
                  <Link href="/terms" style={{ color: "hsl(239, 84%, 67%)", textDecoration: "none" }}>
                    Terms of Service
                  </Link>{" "}
                  and{" "}
                  <Link href="/privacy" style={{ color: "hsl(239, 84%, 67%)", textDecoration: "none" }}>
                    Privacy Policy
                  </Link>
                </Typography>
              }
            />
          </motion.div>

          {/* Submit Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.3 }}
          >
            <GradientButton
              type="submit"
              gradientVariant="primary"
              fullWidth
              size="large"
              disabled
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <ArrowRight size={18} />
                Local sign-up disabled
              </Box>
            </GradientButton>
          </motion.div>
        </Box>
      </form>

      {/* Sign In Link */}
      <Box sx={{ mt: 4, textAlign: "center" }}>
        <Typography sx={{ fontSize: "0.9375rem", color: "hsl(215, 16%, 55%)" }}>
          Already have an account?{" "}
          <Link
            href="/login"
            style={{
              color: "hsl(239, 84%, 67%)",
              textDecoration: "none",
              fontWeight: 600,
            }}
          >
            Sign in
          </Link>
        </Typography>
      </Box>
    </AuthLayout>
  );
}
