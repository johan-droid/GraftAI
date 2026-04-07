"use client";

import * as React from "react";
import { createContext, useContext } from "react";
import { useRouter } from "next/navigation";
import { getSessionSafe, signOut, syncWithBackend } from "@/lib/auth-client";
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
  const router = useRouter();
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
    router.replace("/login");
  }, [router]);

  React.useEffect(() => {
    let active = true;

    async function loadSession(isSilent = false) {
      if (!isSilent) setLoading(true);
      try {
        const response = await getSessionSafe();
        if (!active) return;

        if (response?.data) {
          transientAuthFailuresRef.current = 0;
          setSession(response.data);
          
          // CRITICAL SYNC: Ensure backend user record exists/is fresh.
          if (response.data.user) {
            void syncWithBackend().then(res => {
              if (res.error) console.error("[AUTH]: Initial sync error:", res.error);
            });
          }
        } else if (response?.error) {
          if (isLikelyNetworkError(response.error)) {
            console.debug("Session check encountered a network glitch; retrying without kicking user out.");
          } else {
            transientAuthFailuresRef.current += 1;
            // Only set session to null if we've failed twice OR if it's a blocking load
            if (transientAuthFailuresRef.current >= 2 || !isSilent) {
              setSession(null);
            } else {
              console.debug("Transient auth failure detected in background; retaining session and retrying shortly.");
              if (typeof window !== "undefined") {
                if (retryTimerRef.current) {
                  window.clearTimeout(retryTimerRef.current);
                }
                retryTimerRef.current = window.setTimeout(() => {
                  void loadSession(isSilent);
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
        if (active && !isSilent) setLoading(false);
      }
    }

    loadSession(false); // Initial load is NOT silent
    const interval = setInterval(() => loadSession(true), 60_000); // Background refreshes ARE silent

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

  // Global Realtime SSE Listener (Replaces Manual Interval Polling)
  React.useEffect(() => {
    if (!session?.user) return;
    const { getToken } = require("@/lib/auth-client");
    const token = getToken();
    if (!token) return;

    const baseUrl = typeof window === "undefined" 
      ? (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000") 
      : window.location.origin;

    const url = new URL("/api/v1/calendar/sync/stream", baseUrl);
    url.searchParams.set("token", token);

    const eventSource = new EventSource(url.toString());
    eventSource.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.event === "QUOTA_UPDATE") {
          refreshFn(); // Seamless UI update!
        }
      } catch (err) {}
    };

    return () => eventSource.close();
  }, [(session?.user as User | null)?.id]);

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
      setSession(null);
      router.replace("/");
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
