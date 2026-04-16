"use client";

import { SessionProvider, useSession, signOut } from "next-auth/react";
import { ReactNode } from "react";

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  return (
    <SessionProvider
      // Re-fetch session every 5 minutes to keep it fresh
      refetchInterval={5 * 60}
      // Refetch when the user switches tabs back to the app
      refetchOnWindowFocus={true}
    >
      {children}
    </SessionProvider>
  );
}

// Backward-compatible hook used across the codebase
export function useAuth() {
  const { data: session, status, update } = useSession();
  return {
    session,
    user: session?.user,
    status,
    update,
    signOut,
  };
}
