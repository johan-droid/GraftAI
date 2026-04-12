"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { apiClient } from "@/lib/api-client";

type User = {
  id: string;
  email: string;
  full_name?: string;
  bio?: string;
  job_title?: string;
  location?: string;
  created_at?: string;
};

type AuthContextType = {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  loading: boolean; // Alias for isLoading used in some components
  login: (email: string, password: string) => Promise<{ error?: { message: string } | null; data?: User | null }>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  loading: true,
  login: async () => ({ error: { message: "Auth not initialized" } }),
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const controller = new AbortController();
    const checkAuth = async () => {
      try {
        const response = await fetch("/api/auth/session", {
          method: "GET",
          credentials: "include",
          headers: {
            Accept: "application/json",
          },
          signal: controller.signal,
        });

        if (controller.signal.aborted) return;

        if (response.ok) {
          const data = await response.json();
          if (controller.signal.aborted) return;
          setUser(data.user);
          setIsLoading(false);
          return;
        }
      } catch (error) {
        if (controller.signal.aborted) return;
        console.error("Session check failed", error);
      }

      const token =
        localStorage.getItem("token") ||
        localStorage.getItem("graftai_access_token") ||
        sessionStorage.getItem("token") ||
        sessionStorage.getItem("graftai_access_token");

      if (!token) {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
        return;
      }

      try {
        const userData = await apiClient.fetch("/users/me", { signal: controller.signal });
        if (controller.signal.aborted) return;
        setUser(userData);
      } catch (error) {
        if (controller.signal.aborted) return;
        console.error("Auth token invalid", error);
        localStorage.removeItem("token");
        localStorage.removeItem("graftai_access_token");
        sessionStorage.removeItem("token");
        sessionStorage.removeItem("graftai_access_token");
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    };

    checkAuth();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!isLoading && !user && pathname.startsWith("/dashboard")) {
      localStorage.removeItem("token");
      localStorage.removeItem("graftai_access_token");
      sessionStorage.removeItem("token");
      sessionStorage.removeItem("graftai_access_token");
      router.push("/login");
    }
  }, [pathname, user, isLoading, router]);

  const login = async (email: string, password: string) => {
    try {
      const response = await fetch("/api/auth/signin", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: "Login failed" }));
        return { error: { message: error.error || "Login failed" } };
      }

      const data = await response.json();
      if (data.access_token) {
        localStorage.setItem("token", data.access_token);
      }
      setUser(data.user || null);
      return { data: data.user };
    } catch (error) {
      return { error: { message: "Network error. Please try again." } };
    }
  };

  const logout = async () => {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } catch (error) {
      console.error("Logout failed", error);
    }

    localStorage.removeItem("token");
    localStorage.removeItem("graftai_access_token");
    sessionStorage.removeItem("token");
    sessionStorage.removeItem("graftai_access_token");
    setUser(null);
    router.push("/login");
  };

  if (isLoading) {
    return (
      <div className="flex flex-col h-screen items-center justify-center bg-[#070711] text-white">
        <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mb-4"></div>
        <p className="font-bold tracking-widest uppercase text-xs opacity-50">Initializing GraftAI...</p>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ 
      user, 
      isAuthenticated: !!user, 
      isLoading, 
      loading: isLoading, 
      login, 
      logout 
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuthContext must be used within an AuthProvider");
  }
  return context;
}
