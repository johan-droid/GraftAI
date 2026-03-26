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
  login: (token: string) => Promise<void>;
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

  const user = session?.user as User | null;
  const isAuthenticated = !!session;

  const loginFn = async (token: string) => {
    // Session is handled automatically by the auth client provider.
    // If needed, we can refresh via getSession in future.
  };

  const logoutFn = async () => {
    await signOut();
    router.replace("/login");
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      isAuthenticated, 
      loading,
      login: loginFn,
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
