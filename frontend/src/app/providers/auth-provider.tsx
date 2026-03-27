"use client";

import React, { createContext, useContext } from "react";
import { getSessionSafe, signOut } from "@/lib/auth-client";
import { useRouter } from "next/navigation";

// Define a type for the user matching Neon Auth structure
type User = {
  id: string;
  email: string;
  name: string;
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
  const router = useRouter();
  const [session, setSession] = React.useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let active = true;

    async function loadSession() {
      setLoading(true);
      try {
        const response = await getSessionSafe();
        if (!active) return;
        setSession(response?.data ?? null);
      } catch (err) {
        console.error("Session load failure", err);
        if (active) setSession(null);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadSession();
    const interval = setInterval(loadSession, 60_000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  React.useEffect(() => {
    if (!session?.user && !loading) {
      // Check if we're in the middle of an OAuth flow - don't redirect to login in that case
      const oauthInProgress = typeof window !== "undefined" && sessionStorage.getItem("oauth_in_progress") === "true";
      const isAuthCallback = typeof window !== "undefined" && window.location.pathname.includes("/auth-callback");
      const isLoginPage = typeof window !== "undefined" && window.location.pathname === "/login";
      
      // If we're on the auth-callback page, login page, or in OAuth flow, don't force redirect to login
      // The callback page will handle the session establishment
      if (!isAuthCallback && !isLoginPage && !oauthInProgress) {
        router.replace("/login");
      }
    }
  }, [session, loading, router]);

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

  const loginFn = async (token?: string) => {
    if (token && typeof window !== "undefined") {
      localStorage.setItem("graftai_access_token", token);
      // Clear OAuth in-progress flag after successful login
      sessionStorage.removeItem("oauth_in_progress");
      sessionStorage.removeItem("oauth_redirect_to");
    }
    await refreshFn();
  };

  const logoutFn = async () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("graftai_access_token");
    }
    await signOut();
    setSession(null);
    router.replace("/login");
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
