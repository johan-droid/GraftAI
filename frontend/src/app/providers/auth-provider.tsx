"use client";

import * as React from "react";
import { createContext, useContext } from "react";
import { getSessionSafe, signOut } from "@/lib/auth-client";
import { invalidateSessionCache } from "@/lib/api";

type User = {
  id: string;
  email: string;
  name: string;
  /** Legacy alias — Better Auth uses `name`, app code may read `full_name` */
  full_name?: string;
  tier?: string;
  subscription_status?: string;
  razorpay_subscription_id?: string;
  daily_ai_count?: number;
  daily_sync_count?: number;
  daily_ai_limit?: number;
  daily_sync_limit?: number;
  ai_remaining?: number;
  sync_remaining?: number;
  quota_reset_at?: string;
  trial_days_left?: number;
  trial_expires_at?: string;
  trial_active?: boolean;
};

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  /** Store a newly-acquired token and refresh the session context */
  login: (token: string) => Promise<void>;
  logout: () => Promise<void>;
  /** Re-fetch the session (used by dashboard for periodic refresh) */
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = React.useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = React.useState(true);
  const transientAuthFailuresRef = React.useRef(0);
  const retryTimerRef = React.useRef<number | null>(null);

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
    if (typeof window !== "undefined") {
      // For maximal security and to clear browser history of dashboard pages, use replace to the login screen
      window.location.replace("/login");
    }
  }, []);

  React.useEffect(() => {
    let active = true;

    async function loadSession() {
      setLoading(true);
      try {
        const response = await getSessionSafe();
        if (!active) return;

        if (response?.data) {
          transientAuthFailuresRef.current = 0;
          setSession(response.data);
        } else if (response?.error) {
          if (isLikelyNetworkError(response.error)) {
            console.debug("Session check encountered a network glitch; retrying without kicking user out.");
          } else {
            transientAuthFailuresRef.current += 1;
            if (transientAuthFailuresRef.current >= 2) {
              setSession(null);
            } else {
              console.debug("Transient auth failure detected; retaining session and retrying shortly.");
              if (typeof window !== "undefined") {
                if (retryTimerRef.current) {
                  window.clearTimeout(retryTimerRef.current);
                }
                retryTimerRef.current = window.setTimeout(() => {
                  void loadSession();
                }, 1200);
              }
            }
          }
        } else {
          setSession(null);
        }
      } catch (err) {
        console.error("Session load failure", err);
        setSession(null);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadSession();
    const interval = setInterval(loadSession, 60_000);

    return () => {
      active = false;
      clearInterval(interval);
      if (typeof window !== "undefined" && retryTimerRef.current) {
        window.clearTimeout(retryTimerRef.current);
      }
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
      transientAuthFailuresRef.current = 0;
      setSession(sessionResult.data);
    } else {
      transientAuthFailuresRef.current += 1;
      if (transientAuthFailuresRef.current >= 2) {
        setSession(null);
      }
    }
    return;
  };

  /**
   * FIX BUG-021: loginFn now invalidates the apiFetch session token cache
   * so the next API call immediately uses the newly-acquired token, and
   * refreshes the React session state from Better Auth.
   */
  const loginFn = async (_token: string) => {
    invalidateSessionCache();
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("oauth_in_progress");
      sessionStorage.removeItem("oauth_redirect_to");
      sessionStorage.setItem("graftai_access_token", _token);
      try {
        window.localStorage.setItem("graftai_access_token", _token);
      } catch (error) {
        console.debug("Failed to persist access token in localStorage", error);
      }
    }
    await refreshFn();
  };

  const logoutFn = async () => {
    try {
      await signOut();
    } catch (err) {
      console.debug("SignOut error during cleanup", err);
    }
    
    // Nuke all browser-side storage
    if (typeof window !== "undefined") {
      localStorage.clear();
      sessionStorage.clear();
      // Ensure all cookies are invalidated by refreshing the page to the landing route
      setSession(null);
      window.location.replace("/");
    }
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
