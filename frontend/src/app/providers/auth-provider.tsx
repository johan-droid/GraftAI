"use client";

import React, { createContext, useContext } from "react";
import { getSessionSafe, signOut } from "@/lib/auth-client";

type User = {
  id: string;
  email: string;
  name: string;
  tier?: string;
  subscription_status?: string;
  razorpay_subscription_id?: string;
  daily_ai_count?: number;
  daily_sync_count?: number;
};

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (token?: string) => Promise<void>;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = React.useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = React.useState(true);

  const isLikelyNetworkError = React.useCallback((error: unknown) => {
    if (!error || typeof error !== "object") return false;
    const maybeMessage = "message" in error ? String((error as { message?: unknown }).message ?? "") : "";
    const msg = maybeMessage.toLowerCase();
    return msg.includes("network") || msg.includes("failed to fetch") || msg.includes("fetch") || msg.includes("timeout");
  }, []);

  const isProtectedPath = React.useCallback((pathname: string) => {
    return pathname.startsWith("/dashboard");
  }, []);

  const redirectToLogin = React.useCallback(() => {
    if (typeof window !== "undefined" && window.location.pathname !== "/login") {
      window.location.replace("/login");
    }
  }, []);

  React.useEffect(() => {
    let active = true;

    async function loadSession() {
      // Keep loading until we get a definitive non-network answer.
      setLoading(true);
      try {
        const response = await getSessionSafe();
        if (!active) return;

        if (response?.data) {
          setSession(response.data);
          setLoading(false);
        } else if (response?.error) {
          if (isLikelyNetworkError(response.error)) {
            console.debug("Session check encountered a network glitch; retrying without kicking user out.");
            // Keep prior session state (do not set null) and keep loading until next heartbeat.
            return;
          }
          setSession(null);
          setLoading(false);
        }
      } catch (err) {
        console.error("Session load failure", err);
        // Full fallback: do not log out on transient backend startup failures
        return;
      }
    }

    loadSession();
    const interval = setInterval(loadSession, 60_000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [isLikelyNetworkError]);

  React.useEffect(() => {
    // If not loading and no session user, check for redirection
    if (!loading && !session?.user) {
      const oauthInProgress = typeof window !== "undefined" && sessionStorage.getItem("oauth_in_progress") === "true";
      const currentPath = typeof window !== "undefined" ? window.location.pathname : "";
      
      // If we're on a protected route and not in an auth flow/login page
      if (isProtectedPath(currentPath) && !oauthInProgress && currentPath !== "/login" && !currentPath.includes("/auth-callback")) {
        console.debug("[AUTH]: Unauthenticated access to protected route, redirecting...");
        redirectToLogin();
      }
    }
  }, [session, loading, redirectToLogin, isProtectedPath]);

  React.useEffect(() => {
    if (typeof window === "undefined" || !("serviceWorker" in navigator)) return;

    window.addEventListener("load", async () => {
      try {
        const registration = await navigator.serviceWorker.register("/sw.js");
        console.log("Service Worker registration successful with scope:", registration.scope);
      } catch (error) {
        console.warn("Service Worker registration failed:", error);
      }
    });

    return () => {
      window.removeEventListener("load", () => {});
    };
  }, []);

  const user = session?.user as User | null;
  const isAuthenticated = !!session;

  const refreshFn = async () => {
    const sessionResult = await getSessionSafe();
    if (sessionResult?.data) {
      setSession(sessionResult.data);
    } else {
      setSession(null);
    }
    return;
  };

  const loginFn = async () => {
    if (typeof window !== "undefined") {
      // Clear OAuth in-progress flag after successful login
      sessionStorage.removeItem("oauth_in_progress");
      sessionStorage.removeItem("oauth_redirect_to");
    }
    await refreshFn();
  };

  const logoutFn = async () => {
    await signOut();
    setSession(null);
    redirectToLogin();
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      isAuthenticated, 
      loading,
      login: loginFn,
      refresh: refreshFn,
      logout: logoutFn 
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext must be used within AuthProvider");
  }
  return context;
}
