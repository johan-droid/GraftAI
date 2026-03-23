"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { clearToken, getToken, setToken } from "@/lib/auth";
import { doitAuthCheck, refreshSession } from "@/lib/api";

type User = { sub?: string } & Record<string, unknown> | null;

interface AuthContextValue {
  user: User;
  isAuthenticated: boolean;
  loading: boolean;
  login: (token: string) => void;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initialize = async () => {
      const token = getToken();
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const result = await doitAuthCheck();
        setUser(result.user);
        setIsAuthenticated(true);
      } catch {
        clearToken();
        setUser(null);
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    initialize();

    const interval = setInterval(async () => {
      try {
        await refreshSession();
      } catch {
        clearToken();
        setUser(null);
        setIsAuthenticated(false);
      }
    }, 30 * 1000); // 30 sec

    return () => clearInterval(interval);
  }, []);

  const loginFn = async (token: string) => {
    setToken(token);
    try {
      const result = await doitAuthCheck();
      setUser(result.user);
      setIsAuthenticated(true);
    } catch {
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  const logoutFn = () => {
    clearToken();
    setUser(null);
    setIsAuthenticated(false);
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  };

  const refreshFn = async () => {
    try {
      const result = await refreshSession();
      setUser(result.user);
      setIsAuthenticated(true);
    } catch {
      clearToken();
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, loading, login: loginFn, logout: logoutFn, refresh: refreshFn }}>
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
