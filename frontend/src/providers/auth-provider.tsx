"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { apiClient } from "@/lib/api-client";

interface User {
  id: string;
  email: string;
  full_name: string;
  bio?: string;
  job_title?: string;
  location?: string;
  created_at?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  logout: () => {},
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

  return (
    <AuthContext.Provider value={{ user, loading, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
