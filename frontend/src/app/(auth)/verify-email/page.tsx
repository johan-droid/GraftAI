"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Box, Paper, Typography, Button, Chip } from "@mui/material";
import { motion } from "framer-motion";
import { Mail, Check, X, ArrowRight, RefreshCw, Shield } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";
import { toast } from "@/components/ui/Toast";
import { AuthLayout } from "@/components/auth/AuthLayout";

export default function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const { isDark } = useTheme();

  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying");
  const [isResending, setIsResending] = useState(false);

  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setStatus("error");
        return;
      }
      
      try {
        const response = await fetch(`/api/auth/verify?token=${token}`);
        
        if (response.ok) {
          setStatus("success");
        } else {
          setStatus("error");
        }
      } catch {
        setStatus("error");
      }
    };

    verifyEmail();
  }, [token]);

  const handleResend = async () => {
    setIsResending(true);
    try {
      const response = await fetch("/api/auth/resend-verification", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      
      if (response.ok) {
        toast.success("Verification email resent!");
      } else {
        throw new Error("Failed to resend");
      }
    } catch {
      toast.error("Failed to resend email. Please try again.");
    } finally {
      setIsResending(false);
    }
  };

  return (
    <AuthLayout title="Verify Email">
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
              background:
                status === "success"
                  ? "linear-gradient(135deg, hsl(160, 84%, 39%) 0%, hsl(160, 84%, 49%) 100%)"
                  : status === "error"
                  ? "linear-gradient(135deg, hsl(346, 84%, 61%) 0%, hsl(346, 84%, 71%) 100%)"
                  : "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 16px",
              boxShadow:
                status === "success"
                  ? "0 10px 40px -10px hsla(160, 84%, 39%, 0.5)"
                  : status === "error"
                  ? "0 10px 40px -10px hsla(346, 84%, 61%, 0.5)"
                  : "0 10px 40px -10px hsla(239, 84%, 67%, 0.5)",
            }}
          >
            {status === "success" ? (
              <Check size={32} color="white" />
            ) : status === "error" ? (
              <X size={32} color="white" />
            ) : (
              <Mail size={32} color="white" />
            )}
          </Box>

          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
              mb: 1,
            }}
          >
            {status === "success"
              ? "Email verified!"
              : status === "error"
              ? "Verification failed"
              : "Verifying your email"}
          </Typography>

          <Typography sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
            {status === "success"
              ? "Your email has been successfully verified. You can now access all features."
              : status === "error"
              ? "The verification link is invalid or has expired. Please request a new one."
              : "Please wait while we verify your email address..."}
          </Typography>
        </Box>

        {status === "verifying" && (
          <Paper
            elevation={0}
            sx={{
              p: 3,
              textAlign: "center",
              background: isDark
                ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
              border: "1px solid hsla(239, 84%, 67%, 0.15)",
              borderRadius: "16px",
            }}
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              style={{
                width: 40,
                height: 40,
                borderRadius: "50%",
                border: "3px solid hsla(239, 84%, 67%, 0.2)",
                borderTopColor: "hsl(239, 84%, 67%)",
                margin: "0 auto",
              }}
            />
          </Paper>
        )}

        {status === "success" && (
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
            <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 1, mb: 2 }}>
              <Shield size={20} style={{ color: "hsl(160, 84%, 39%)" }} />
              <Typography sx={{ color: "hsl(160, 84%, 39%)", fontWeight: 600 }}>
                Your account is now secure
              </Typography>
            </Box>

            <Button
              onClick={() => router.push("/dashboard")}
              variant="contained"
              endIcon={<ArrowRight size={18} />}
              fullWidth
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
              }}
            >
              Go to Dashboard
            </Button>
          </Paper>
        )}

        {status === "error" && (
          <Paper
            elevation={0}
            sx={{
              p: 3,
              background: isDark
                ? "hsla(346, 84%, 61%, 0.1)"
                : "hsla(346, 84%, 61%, 0.05)",
              border: "1px solid hsla(346, 84%, 61%, 0.3)",
              borderRadius: "16px",
              textAlign: "center",
            }}
          >
            <Typography sx={{ color: "hsl(346, 84%, 61%)", fontWeight: 600, mb: 2 }}>
              Verification failed
            </Typography>
            <Button
              onClick={handleResend}
              disabled={isResending}
              variant="outlined"
              startIcon={<RefreshCw size={16} />}
              fullWidth
              sx={{
                borderColor: "hsla(239, 84%, 67%, 0.5)",
                color: "hsl(239, 84%, 67%)",
                fontWeight: 600,
                borderRadius: "10px",
                textTransform: "none",
                "&:hover": {
                  borderColor: "hsl(239, 84%, 67%)",
                  background: "hsla(239, 84%, 67%, 0.1)",
                },
              }}
            >
              {isResending ? "Resending..." : "Resend Verification Email"}
            </Button>
          </Paper>
        )}

        <Box sx={{ textAlign: "center", mt: 3 }}>
          <Typography sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)", mb: 1 }}>
            Need help?
          </Typography>
          <Link
            href="/login"
            style={{
              color: "hsl(239, 84%, 67%)",
              textDecoration: "none",
              fontWeight: 500,
            }}
          >
            Back to login
          </Link>
        </Box>
      </motion.div>
    </AuthLayout>
  );
}
