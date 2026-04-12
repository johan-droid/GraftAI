"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Box, Paper, Typography, TextField, Button, Chip } from "@mui/material";
import { motion } from "framer-motion";
import { ArrowLeft, Mail, KeyRound, Check, Lock } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";
import { toast } from "@/components/ui/Toast";
import { AuthLayout } from "@/components/auth/AuthLayout";

export default function ForgotPasswordPage() {
  const router = useRouter();
  const { isDark } = useTheme();

  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSent, setIsSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      toast.error("Please enter your email address");
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        throw new Error("Failed to send reset link");
      }

      setIsSent(true);
      toast.success("Password reset link sent to your email!");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to send reset link. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout title="Reset Password">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Box sx={{ textAlign: "center", mb: 4 }}>
          <Box
            sx={{
              width: 64,
              height: 64,
              borderRadius: "16px",
              background: isSent
                ? "linear-gradient(135deg, hsl(160, 84%, 39%) 0%, hsl(160, 84%, 49%) 100%)"
                : "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 16px",
              boxShadow: isSent
                ? "0 10px 40px -10px hsla(160, 84%, 39%, 0.5)"
                : "0 10px 40px -10px hsla(239, 84%, 67%, 0.5)",
            }}
          >
            {isSent ? <Check size={32} color="white" /> : <KeyRound size={32} color="white" />}
          </Box>

          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
              mb: 1,
            }}
          >
            {isSent ? "Check your email" : "Reset password"}
          </Typography>

          <Typography sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
            {isSent
              ? `We sent a password reset link to ${email}`
              : "Enter your email and we'll send you a link to reset your password"}
          </Typography>
        </Box>

        {!isSent ? (
          <Paper
            component="form"
            onSubmit={handleSubmit}
            elevation={0}
            sx={{
              p: 3,
              background: isDark
                ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
              border: "1px solid hsla(239, 84%, 67%, 0.15)",
              borderRadius: "16px",
            }}
          >
            <TextField
              fullWidth
              type="email"
              label="Email Address"
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              InputProps={{
                startAdornment: <Mail size={18} style={{ marginRight: 12, color: "hsl(215, 16%, 55%)" }} />,
              }}
              sx={{
                mb: 3,
                "& .MuiOutlinedInput-root": {
                  background: "transparent",
                  borderRadius: "10px",
                  color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                  "& fieldset": { borderColor: "hsla(239, 84%, 67%, 0.3)" },
                  "&:hover fieldset": { borderColor: "hsla(239, 84%, 67%, 0.5)" },
                  "&.Mui-focused fieldset": { borderColor: "hsl(239, 84%, 67%)" },
                },
                "& .MuiInputLabel-root": { color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" },
              }}
            />

            <Button
              type="submit"
              fullWidth
              disabled={isLoading}
              sx={{
                py: 1.5,
                background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                color: "white",
                fontWeight: 600,
                borderRadius: "10px",
                textTransform: "none",
                fontSize: "1rem",
                "&:hover": {
                  background: "linear-gradient(135deg, hsl(239, 84%, 57%) 0%, hsl(330, 81%, 50%) 100%)",
                },
                "&:disabled": {
                  background: isDark ? "hsl(240, 24%, 22%)" : "hsl(220, 14%, 90%)",
                  color: isDark ? "hsl(215, 16%, 40%)" : "hsl(215, 16%, 60%)",
                },
              }}
            >
              {isLoading ? "Sending..." : "Send Reset Link"}
            </Button>
          </Paper>
        ) : (
          <Paper
            elevation={0}
            sx={{
              p: 3,
              mb: 3,
              background: isDark
                ? "hsla(160, 84%, 39%, 0.1)"
                : "hsla(160, 84%, 39%, 0.05)",
              border: "1px solid hsla(160, 84%, 39%, 0.3)",
              borderRadius: "16px",
              textAlign: "center",
            }}
          >
            <Typography sx={{ color: "hsl(160, 84%, 39%)", fontWeight: 600, mb: 1 }}>
              Email sent successfully!
            </Typography>
            <Typography sx={{ fontSize: "0.875rem", color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
              Didn't receive the email? Check your spam folder or try again.
            </Typography>
          </Paper>
        )}

        <Box sx={{ textAlign: "center", mt: 3 }}>
          <Link
            href="/login"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              color: "hsl(239, 84%, 67%)",
              textDecoration: "none",
              fontWeight: 500,
            }}
          >
            <ArrowLeft size={16} />
            Back to login
          </Link>
        </Box>
      </motion.div>
    </AuthLayout>
  );
}
