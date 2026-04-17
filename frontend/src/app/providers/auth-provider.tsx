"use client";

import { SessionProvider, useSession, signOut } from "next-auth/react";
import type { Session } from "next-auth";
import { ReactNode } from "react";

interface AuthProviderProps {
  children: ReactNode;
}

type AuthUser = {
  id?: string;
  role?: string;
  name?: string;
  username?: string;
  email?: string;
  image?: string;
  avatar?: string;
  full_name?: string;
  bio?: string;
  job_title?: string;
  location?: string;
  tier?: string;
  created_at?: string;
  [key: string]: string | number | boolean | undefined;
};

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
  const rawUser = session?.user;
  const user = rawUser
    ? ({
        ...rawUser,
        name: rawUser.name ?? undefined,
        email: rawUser.email ?? undefined,
        image: rawUser.image ?? undefined,
        avatar: (rawUser as any).avatar ?? undefined,
      } as AuthUser)
    : undefined;

  return {
    session,
    user,
    backendToken: session?.backendToken,
    status,
    isAuthenticated: status === "authenticated",
    loading: status === "loading",
    update,
    refresh: () => update?.(),
    logout: () => signOut({ callbackUrl: "/login" }),
    signOut,
  };
}
