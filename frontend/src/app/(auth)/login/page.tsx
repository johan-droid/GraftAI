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
import { authClient } from "@/lib/auth-client";
import { toast } from "@/components/ui/Toast";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password) {
      setError("Please enter both email and password");
      return;
    }

    setIsLoading(true);

    try {
      const { error: authError } = await authClient.signIn.email({
        email: email.trim(),
        password,
      });

      if (authError) {
        throw new Error(authError.message ?? "Invalid credentials");
      }

      toast.success("Welcome back!");
      router.replace("/dashboard");
    } catch (err) {
      const message = (err as Error).message || "Sign-in failed. Please try again.";
      setError(message);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Sign in to your account"
      subtitle="Welcome back! Please enter your credentials to continue."
    >
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

          {/* Email Field */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.3 }}
          >
            <FloatingInput
              label="Email"
              type="email"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              icon={Mail}
              errorMessage={error && !email ? "Email is required" : undefined}
              disabled={isLoading}
              required
            />
          </motion.div>

          {/* Password Field */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.3 }}
          >
            <FloatingInput
              label="Password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={Lock}
              isPassword
              errorMessage={error && !password ? "Password is required" : undefined}
              disabled={isLoading}
              required
            />
          </motion.div>

          {/* Forgot Password Link */}
          <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
            <Link
              href="/forgot-password"
              style={{
                fontSize: "0.875rem",
                color: "hsl(239, 84%, 67%)",
                textDecoration: "none",
                fontWeight: 500,
                transition: "color 0.2s",
              }}
            >
              Forgot password?
            </Link>
          </Box>

          {/* Submit Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.3 }}
          >
            <GradientButton
              type="submit"
              gradientVariant="primary"
              fullWidth
              size="large"
              disabled={isLoading}
            >
              {isLoading ? (
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Loader2 size={20} className="animate-spin" />
                  Signing in...
                </Box>
              ) : (
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  Sign in
                  <ArrowRight size={18} />
                </Box>
              )}
            </GradientButton>
          </motion.div>
        </Box>
      </form>

      {/* OAuth Section */}
      <Box sx={{ mt: 4 }}>
        <OAuthButtons callbackURL="/dashboard" />
      </Box>

      {/* Sign Up Link */}
      <Box sx={{ mt: 4, textAlign: "center" }}>
        <Box
          component="p"
          sx={{
            fontSize: "0.9375rem",
            color: "hsl(215, 16%, 55%)",
          }}
        >
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            style={{
              color: "hsl(239, 84%, 67%)",
              textDecoration: "none",
              fontWeight: 600,
              transition: "color 0.2s",
            }}
          >
            Sign up for free
          </Link>
        </Box>
      </Box>
    </AuthLayout>
  );
}
