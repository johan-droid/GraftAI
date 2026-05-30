"use client";

import { SessionProvider, useSession, signOut } from "next-auth/react";
import type { Session } from "next-auth";
import { ReactNode } from "react";

interface AuthProviderProps {
  children: ReactNode;
  initialSession?: Session | null;
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

export function AuthProvider({ children, initialSession }: AuthProviderProps) {
  return (
    <SessionProvider
      session={initialSession ?? undefined}
      // Seeded from the server layout to avoid an extra session round-trip.
      // We keep refetching disabled for speed; token refresh is handled by
      // the NextAuth JWT callback/server-side backend token rotation.
      refetchInterval={0}
      refetchOnWindowFocus={false}
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
