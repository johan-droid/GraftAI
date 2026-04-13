"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { apiClient } from "@/lib/api-client";

interface User {
  id: string;
  email: string;
  full_name: string;
  name?: string; // Alias for UI compatibility
  bio?: string;
  job_title?: string;
  location?: string;
  created_at?: string;
  tier?: string;
  daily_ai_count?: number;
  daily_sync_count?: number;
  daily_ai_limit?: number;
  daily_sync_limit?: number;
  quota_reset_at?: string;
  ai_remaining?: number;
  sync_remaining?: number;
  trial_days_left?: number;
  trial_expires_at?: string;
  trial_active?: boolean;
  subscription_status?: string;
  razorpay_subscription_id?: string;
  timezone?: string;
}

interface AuthResult {
  error?: { message: string } | null;
  data?: User | null;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<AuthResult>;
  register: (name: string, email: string, password: string) => Promise<AuthResult>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: async () => ({ error: { message: 'Auth not initialized' } }),
  register: async () => ({ error: { message: 'Auth not initialized' } }),
  logout: () => {},
  refresh: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem("token")
        || localStorage.getItem("graftai_access_token")
        || sessionStorage.getItem("token")
        || sessionStorage.getItem("graftai_access_token");
      
      // If there's no token and they are trying to access the dashboard, kick them out
      if (!token && pathname.startsWith("/dashboard")) {
        router.push("/login");
        setLoading(false);
        return;
      }

      if (token) {
        try {
          // We fetch the current user's details using the token
          const userData = await apiClient.fetch("/users/me");
          setUser(userData);
        } catch (error) {
          console.error("Auth token invalid", error);
          localStorage.removeItem("token");
          if (pathname.startsWith("/dashboard")) router.push("/login");
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, [pathname, router]);

  const login = async (email: string, password: string): Promise<AuthResult> => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        return { error: { message: error.detail || 'Login failed' } };
      }
      
      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      setUser(data.user);
      return { data: data.user };
    } catch (error) {
      return { error: { message: 'Network error. Please try again.' } };
    }
  };

  const register = async (name: string, email: string, password: string): Promise<AuthResult> => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        return { error: { message: error.detail || 'Registration failed' } };
      }
      
      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      setUser(data.user);
      return { data: data.user };
    } catch (error) {
      return { error: { message: 'Network error. Please try again.' } };
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    router.push("/login");
  };

  if (loading) {
    return (
      <div className="flex flex-col h-screen items-center justify-center bg-[#070711] text-white">
        <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mb-4"></div>
        <p className="font-bold tracking-widest uppercase text-xs opacity-50">Initializing GraftAI...</p>
      </div>
    );
  }

  const refresh = async () => {
    const token = localStorage.getItem("token")
      || localStorage.getItem("graftai_access_token")
      || sessionStorage.getItem("token")
      || sessionStorage.getItem("graftai_access_token");
    
    if (token) {
      try {
        const userData = await apiClient.fetch("/users/me");
        setUser(userData);
      } catch (error) {
        console.error("Refresh failed", error);
      }
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
export const useAuthContext = useAuth;
