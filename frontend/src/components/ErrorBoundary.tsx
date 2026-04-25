"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
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
    <div
      className="min-h-screen flex items-center justify-center p-6 relative overflow-hidden"
      style={{ background: "hsl(240, 24%, 7%)" }}
    >
      {/* Background Effects */}
      <div
        className="absolute inset-0"
        style={{
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
        className="w-full max-w-md relative z-10"
      >
        <div
          className="p-8 rounded-2xl text-center"
          style={{
            background: "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)",
            border: "1px solid hsla(239, 84%, 67%, 0.2)",
          }}
        >
          {/* Error Icon */}
          <div
            className="w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-6"
            style={{
              background: "hsla(346, 84%, 61%, 0.1)",
              border: "1px solid hsla(346, 84%, 61%, 0.3)",
            }}
          >
            <AlertTriangle size={40} style={{ color: "hsl(346, 84%, 61%)" }} />
          </div>

          <h1
            className="text-2xl font-bold mb-4"
            style={{
              color: "hsl(220, 20%, 98%)",
              letterSpacing: "-0.01em",
            }}
          >
            Something went wrong
          </h1>

          <p
            className="mb-6"
            style={{
              color: "hsl(215, 16%, 55%)",
              fontSize: "1rem",
              lineHeight: 1.6,
            }}
          >
            We encountered an unexpected error. Our team has been notified and we&apos;re working to fix it.
          </p>

          {/* Error Details (collapsible in production) */}
          {process.env.NODE_ENV === "development" && error && (
            <div
              className="mb-6 p-4 rounded-lg text-left"
              style={{
                background: "hsla(346, 84%, 61%, 0.05)",
                border: "1px solid hsla(346, 84%, 61%, 0.2)",
              }}
            >
              <div className="flex items-center gap-2 mb-2">
                <Bug size={16} style={{ color: "hsl(346, 84%, 61%)" }} />
                <span className="text-xs font-semibold" style={{ color: "hsl(346, 84%, 61%)" }}>
                  DEBUG MODE
                </span>
              </div>
              <pre
                className="text-xs font-mono overflow-auto"
                style={{ color: "hsl(346, 84%, 61%)", margin: 0 }}
              >
                {error.message}
                {error.stack && (
                  <div className="mt-2 opacity-70">{error.stack}</div>
                )}
              </pre>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={onReload}
              className="flex-1 py-3 px-6 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-colors"
              style={{
                background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                color: "white",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "linear-gradient(135deg, hsl(239, 84%, 57%) 0%, hsl(330, 81%, 50%) 100%)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)";
              }}
            >
              <RefreshCw size={18} />
              Try Again
            </button>

            <Link
              href="/"
              className="flex-1 py-3 px-6 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-colors"
              style={{
                border: "1px solid hsla(239, 84%, 67%, 0.3)",
                color: "hsl(220, 20%, 98%)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "hsla(239, 84%, 67%, 0.5)";
                e.currentTarget.style.background = "hsla(239, 84%, 67%, 0.05)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "hsla(239, 84%, 67%, 0.3)";
                e.currentTarget.style.background = "transparent";
              }}
            >
              <Home size={18} />
              Go Home
            </Link>
          </div>

          {/* Support Link */}
          <div className="mt-6">
            <p className="text-sm" style={{ color: "hsl(215, 16%, 40%)" }}>
              Need help?{" "}
              <a
                href="mailto:support@graftai.com"
                className="font-medium hover:underline"
                style={{ color: "hsl(239, 84%, 67%)" }}
              >
                Contact Support
              </a>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
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
