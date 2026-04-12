"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { Box, Button, Typography, Paper } from "@mui/material";
import { motion } from "framer-motion";
import { AlertTriangle, RefreshCw, Home, Bug } from "lucide-react";
import Link from "next/link";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
    this.setState({ error, errorInfo });
    
    // Log to error tracking service
    // if (process.env.NODE_ENV === 'production') {
    //   logErrorToService(error, errorInfo);
    // }
  }

  private handleReload = () => {
    window.location.reload();
  };

  private handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return <ErrorFallback error={this.state.error} onReload={this.handleReload} onReset={this.handleReset} />;
    }

    return this.props.children;
  }
}

interface ErrorFallbackProps {
  error: Error | null;
  onReload: () => void;
  onReset: () => void;
}

function ErrorFallback({ error, onReload, onReset }: ErrorFallbackProps) {
  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        p: 3,
        background: "hsl(240, 24%, 7%)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background Effects */}
      <Box
        sx={{
          position: "absolute",
          inset: 0,
          background: `
            radial-gradient(ellipse at 30% 30%, hsla(346, 84%, 61%, 0.1) 0%, transparent 50%),
            radial-gradient(ellipse at 70% 70%, hsla(239, 84%, 67%, 0.05) 0%, transparent 50%)
          `,
        }}
      />

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        style={{ width: "100%", maxWidth: 480, position: "relative", zIndex: 1 }}
      >
        <Paper
          elevation={0}
          sx={{
            p: 5,
            background: "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)",
            border: "1px solid hsla(239, 84%, 67%, 0.2)",
            borderRadius: 4,
            textAlign: "center",
          }}
        >
          {/* Error Icon */}
          <Box
            sx={{
              width: 80,
              height: 80,
              borderRadius: "24px",
              background: "hsla(346, 84%, 61%, 0.1)",
              border: "1px solid hsla(346, 84%, 61%, 0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              mx: "auto",
              mb: 3,
            }}
          >
            <AlertTriangle size={40} style={{ color: "hsl(346, 84%, 61%)" }} />
          </Box>

          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              color: "hsl(220, 20%, 98%)",
              mb: 2,
              letterSpacing: "-0.01em",
            }}
          >
            Something went wrong
          </Typography>

          <Typography
            sx={{
              color: "hsl(215, 16%, 55%)",
              mb: 4,
              fontSize: "1rem",
              lineHeight: 1.6,
            }}
          >
            We encountered an unexpected error. Our team has been notified and we&apos;re working to fix it.
          </Typography>

          {/* Error Details (collapsible in production) */}
          {process.env.NODE_ENV === "development" && error && (
            <Box
              sx={{
                mb: 4,
                p: 2,
                background: "hsla(346, 84%, 61%, 0.05)",
                border: "1px solid hsla(346, 84%, 61%, 0.2)",
                borderRadius: 2,
                textAlign: "left",
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                <Bug size={16} style={{ color: "hsl(346, 84%, 61%)" }} />
                <Typography sx={{ fontSize: "0.75rem", color: "hsl(346, 84%, 61%)", fontWeight: 600 }}>
                  DEBUG MODE
                </Typography>
              </Box>
              <Typography
                component="pre"
                sx={{
                  fontSize: "0.75rem",
                  color: "hsl(346, 84%, 61%)",
                  fontFamily: "monospace",
                  overflow: "auto",
                  m: 0,
                  p: 0,
                }}
              >
                {error.message}
                {error.stack && <Box component="div" sx={{ mt: 1, opacity: 0.7 }}>{error.stack}</Box>}
              </Typography>
            </Box>
          )}

          {/* Action Buttons */}
          <Box sx={{ display: "flex", gap: 2, flexDirection: { xs: "column", sm: "row" } }}>
            <Button
              onClick={onReload}
              variant="contained"
              fullWidth
              sx={{
                py: 1.5,
                background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                borderRadius: "12px",
                textTransform: "none",
                fontWeight: 600,
                fontSize: "0.9375rem",
                display: "flex",
                alignItems: "center",
                gap: 1,
                "&:hover": {
                  background: "linear-gradient(135deg, hsl(239, 84%, 57%) 0%, hsl(330, 81%, 50%) 100%)",
                },
              }}
            >
              <RefreshCw size={18} />
              Try Again
            </Button>

            <Button
              component={Link}
              href="/"
              variant="outlined"
              fullWidth
              sx={{
                py: 1.5,
                borderColor: "hsla(239, 84%, 67%, 0.3)",
                color: "hsl(220, 20%, 98%)",
                borderRadius: "12px",
                textTransform: "none",
                fontWeight: 600,
                fontSize: "0.9375rem",
                display: "flex",
                alignItems: "center",
                gap: 1,
                "&:hover": {
                  borderColor: "hsla(239, 84%, 67%, 0.5)",
                  background: "hsla(239, 84%, 67%, 0.05)",
                },
              }}
            >
              <Home size={18} />
              Go Home
            </Button>
          </Box>

          {/* Support Link */}
          <Box sx={{ mt: 4 }}>
            <Typography sx={{ fontSize: "0.875rem", color: "hsl(215, 16%, 40%)" }}>
              Need help?{" "}
              <Link
                href="mailto:support@graftai.com"
                style={{
                  color: "hsl(239, 84%, 67%)",
                  textDecoration: "none",
                  fontWeight: 500,
                }}
              >
                Contact Support
              </Link>
            </Typography>
          </Box>
        </Paper>
      </motion.div>
    </Box>
  );
}

// Hook for functional components to trigger error boundary
export function useErrorBoundary() {
  const [error, setError] = React.useState<Error | null>(null);

  if (error) {
    throw error;
  }

  return setError;
}
