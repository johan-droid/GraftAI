"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  ReactNode,
} from "react";
import { useRouter, usePathname } from "next/navigation";
import { useSession, signOut } from "next-auth/react";
import { apiClient } from "@/lib/api-client";

// ─── Types ────────────────────────────────────────────────────────────────────

export type User = {
  id: string;
  email: string;
  full_name?: string;
  name?: string; // Add name alias
  avatar?: string; // Add avatar alias
  image?: string;
  username?: string;
  bio?: string;
  job_title?: string;
  location?: string;
  created_at?: string;
  tier?: string;
  subscription_status?: string;
};

type AuthContextType = {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  /** Alias for isLoading — kept for backward compat */
  loading: boolean;
  logout: () => void;
  refresh: () => Promise<void>;
  /** The raw backend JWT, for use in non-apiClient contexts */
  backendToken: string | null;
};

// ─── Context ──────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  loading: true,
  logout: () => {},
  refresh: async () => {},
  backendToken: null,
});

// ─── Protected routes: redirect to login if unauthenticated ──────────────────

const PROTECTED_PREFIXES = [
  "/dashboard",
  "/calendar",
  "/copilot",
  "/integrations",
  "/book",
  "/profile",
];

function isProtectedRoute(pathname: string) {
  return PROTECTED_PREFIXES.some((p) => pathname.startsWith(p));
}

// ─── Provider ─────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const { data: session, status } = useSession();
  const [user, setUser] = useState<User | null>(null);
  const [isFetchingProfile, setIsFetchingProfile] = useState(false);
  const [fetchFailCount, setFetchFailCount] = useState(0);
  const router = useRouter();
  const pathname = usePathname();

  const isLoading = status === "loading" || isFetchingProfile;
  const backendToken = (session as any)?.backendToken ?? null;

  // ── fetch / refresh the backend profile ─────────────────────────────────────
  const fetchProfile = useCallback(async () => {
    if (status !== "authenticated" || !backendToken) return;

    // If the session has a RefreshTokenError the backend token is gone —
    // Only force re-login if we also have no user data (give benefit of doubt)
    if ((session as any)?.error === "RefreshTokenError" && !user) {
      console.warn("[AuthProvider] RefreshTokenError with no user — signing out.");
      signOut({ callbackUrl: "/login" });
      return;
    }

    setIsFetchingProfile(true);
    try {
      const userData = await apiClient.get<User>("/users/me");
      setUser(userData);
      setFetchFailCount(0); // Reset failure counter on success
    } catch (err: any) {
      const msg: string = err?.message ?? "";
      const isAuthError =
        msg.includes("sign in again") ||
        (msg.toLowerCase().includes("credential") && msg.toLowerCase().includes("validate"));

      if (isAuthError) {
        const newCount = fetchFailCount + 1;
        setFetchFailCount(newCount);
        // Only sign out after 2 consecutive auth failures, not the first one
        // (avoids race conditions on first page load)
        if (newCount >= 2) {
          console.error("[AuthProvider] Persistent 401 — forcing sign-out");
          setUser(null);
          signOut({ callbackUrl: "/login" });
        } else {
          console.warn("[AuthProvider] Auth error on /users/me (attempt", newCount, ") — will retry.");
        }
      } else {
        console.error("[AuthProvider] Failed to fetch user profile:", err);
      }
    } finally {
      setIsFetchingProfile(false);
    }
  }, [status, backendToken, session, user, fetchFailCount]);

  // ── fetch / refresh the backend profile ─────────────────────────────────────
  useEffect(() => {
    if (status === "authenticated" && backendToken) {
      fetchProfile();
    } else if (status === "unauthenticated") {
      setUser(null);
    }
  }, [status, backendToken]); 


  // ── Protected route guard ────────────────────────────────────────────────────
  useEffect(() => {
    // Only redirect if NextAuth says we are definitively NOT authenticated
    if (status === "unauthenticated" && isProtectedRoute(pathname)) {
      console.log("[AuthProvider] Redirecting to login: unauthenticated status on protected route", pathname);
      router.push("/login?callbackUrl=" + encodeURIComponent(pathname));
    }
  }, [status, pathname, router]);


  // ── Actions ──────────────────────────────────────────────────────────────────
  const logout = useCallback(() => {
    setUser(null);
    signOut({ callbackUrl: "/login" });
  }, []);

  const refresh = useCallback(async () => {
    await fetchProfile();
  }, [fetchProfile]);

  // ── Loading state ─────────────────────────────────────────────────────────────
  if (status === "loading" && !user) {
    return (
      <div className="flex flex-col h-screen items-center justify-center bg-[#050505] text-white relative overflow-hidden">
        {/* Terminal Grid Background */}
        <div 
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `
              linear-gradient(var(--border-subtle) 1px, transparent 1px),
              linear-gradient(90deg, var(--border-subtle) 1px, transparent 1px)
            `,
            backgroundSize: "40px 40px",
          }}
        />
        
        <div className="relative z-10 flex flex-col items-center">
          <div className="w-12 h-12 border-2 border-[var(--border-subtle)] border-t-[var(--primary)] rounded-none animate-spin mb-8" />
          
          <div className="flex flex-col items-center gap-2">
            <p className="font-mono text-[10px] uppercase tracking-[0.4em] text-[var(--primary)] font-black">
              INITIALIZING_GRAFT_ENGINE
            </p>
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <div 
                  key={i}
                  className="w-1.5 h-1.5 bg-[var(--primary)] animate-pulse"
                  style={{ animationDelay: `${i * 0.2}s` }}
                />
              ))}
            </div>
          </div>

          <div className="mt-12 px-4 py-2 border border-dashed border-[var(--border-subtle)] bg-black/40">
             <p className="font-mono text-[8px] text-[var(--text-faint)] uppercase tracking-widest">
                [ AUTH_NODE_STABLE // KERNEL_CONNECT_PENDING ]
             </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: status === "authenticated", // Rely on NextAuth session status for auth state
        isLoading,
        loading: isLoading,

        logout,
        refresh,
        backendToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

/** @deprecated Use `useAuth` instead */
export const useAuthContext = useAuth;
