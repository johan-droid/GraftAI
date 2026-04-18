import type { NextAuthConfig } from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import MicrosoftEntraId from "next-auth/providers/microsoft-entra-id";
import { getGoogleOAuthCredentials, getMicrosoftOAuthCredentials } from "@/lib/oauth-env";

// ─── Environment Bridging ──────────────────────────────────────────────────
// Resolve legacy and Auth.js v5 env names so either deployment convention works.
const googleOAuth = getGoogleOAuthCredentials();
const microsoftOAuth = getMicrosoftOAuthCredentials();

if (!googleOAuth.clientId || !googleOAuth.clientSecret) {
  console.warn(
    "[NextAuth] Google OAuth credentials are missing. Set GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET or AUTH_GOOGLE_ID/AUTH_GOOGLE_SECRET."
  );
}

if (googleOAuth.clientId && !process.env.AUTH_GOOGLE_ID) {
  process.env.AUTH_GOOGLE_ID = googleOAuth.clientId;
}
if (googleOAuth.clientSecret && !process.env.AUTH_GOOGLE_SECRET) {
  process.env.AUTH_GOOGLE_SECRET = googleOAuth.clientSecret;
}
if (microsoftOAuth.clientId && !process.env.AUTH_MICROSOFT_ENTRA_ID_ID) {
  process.env.AUTH_MICROSOFT_ENTRA_ID_ID = microsoftOAuth.clientId;
}
if (microsoftOAuth.clientSecret && !process.env.AUTH_MICROSOFT_ENTRA_ID_SECRET) {
  process.env.AUTH_MICROSOFT_ENTRA_ID_SECRET = microsoftOAuth.clientSecret;
}

// ─── NextAuth Configuration (Edge Compatible) ────────────────────────────────
// This file contains providers and settings that must be available in the 
// Edge runtime (Middleware). Avoid Node-only dependencies here.
const providers = [] as any[];

if (googleOAuth.clientId && googleOAuth.clientSecret) {
  providers.push(
    GoogleProvider({
      clientId: googleOAuth.clientId,
      clientSecret: googleOAuth.clientSecret,
      authorization: {
        params: {
          scope: [
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events",
          ].join(" "),
          access_type: "offline",
          prompt: "consent",
        },
      },
    })
  );
} else {
  console.warn("[NextAuth] Google provider not registered due to missing credentials.");
}

if (microsoftOAuth.clientId && microsoftOAuth.clientSecret) {
  providers.push(
    MicrosoftEntraId({
      clientId: microsoftOAuth.clientId,
      clientSecret: microsoftOAuth.clientSecret,
      issuer: `https://login.microsoftonline.com/${process.env.MICROSOFT_TENANT_ID || "common"}/v2.0`,
      authorization: {
        params: {
          scope: [
            "openid",
            "email",
            "profile",
            "offline_access",
            "Calendars.ReadWrite",
            "User.Read",
          ].join(" "),
        },
      },
    })
  );
} else {
  console.warn("[NextAuth] Microsoft Entra provider not registered due to missing credentials.");
}

export const authConfig = {
  providers,
  trustHost: true,
  pages: {
    signIn: "/login",
    error: "/login",
  },
  callbacks: {
    authorized({ auth, request: { nextUrl } }: { auth: any; request: { nextUrl: any } }) {
      const isLoggedIn = !!auth?.user;
      const isDashboard = nextUrl.pathname.startsWith("/dashboard");
      const isOnboarding = nextUrl.pathname.startsWith("/onboarding") || nextUrl.pathname.startsWith("/profile/setup");
      
      // Allow dashboard access if logged in (skip profile setup check)
      if (isDashboard) {
        if (isLoggedIn) return true;
        return false; // Redirect unauthenticated users to login page
      }
      
      // If user is logged in and tries to access onboarding/setup, redirect to dashboard
      if (isOnboarding && isLoggedIn) {
        return Response.redirect(new URL("/dashboard", nextUrl));
      }
      
      return true;
    },
  },
} satisfies NextAuthConfig;
