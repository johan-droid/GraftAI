"use client";
import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props { children: ReactNode; fallback?: ReactNode; }
interface State { hasError: boolean; message: string; }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: "" };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[ErrorBoundary]", error, info);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="card flex flex-col items-center justify-center gap-4 py-12 px-6 text-center">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center"
            style={{ background: "rgba(248,113,113,0.1)" }}>
            <AlertTriangle className="w-6 h-6" style={{ color: "var(--error)" }} />
          </div>
          <div>
            <p className="font-semibold" style={{ color: "var(--text)" }}>Something went wrong</p>
            <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
              {this.state.message || "An unexpected error occurred."}
            </p>
          </div>
          <button
            className="btn btn-ghost text-sm"
            onClick={() => this.setState({ hasError: false, message: "" })}
          >
            <RefreshCw className="w-4 h-4" /> Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
