import type { NextAuthConfig } from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import MicrosoftEntraId from "next-auth/providers/microsoft-entra-id";

// ─── Environment Bridging ──────────────────────────────────────────────────
// Auth.js v5 prefers AUTH_* prefixes. We bridge established names for 
// compatibility without requiring dashboard changes.
if (process.env.GOOGLE_CLIENT_ID && !process.env.AUTH_GOOGLE_ID) {
  process.env.AUTH_GOOGLE_ID = process.env.GOOGLE_CLIENT_ID;
}
if (process.env.GOOGLE_CLIENT_SECRET && !process.env.AUTH_GOOGLE_SECRET) {
  process.env.AUTH_GOOGLE_SECRET = process.env.GOOGLE_CLIENT_SECRET;
}
if (process.env.MICROSOFT_CLIENT_ID && !process.env.AUTH_MICROSOFT_ENTRA_ID_ID) {
  process.env.AUTH_MICROSOFT_ENTRA_ID_ID = process.env.MICROSOFT_CLIENT_ID;
}
if (process.env.MICROSOFT_CLIENT_SECRET && !process.env.AUTH_MICROSOFT_ENTRA_ID_SECRET) {
  process.env.AUTH_MICROSOFT_ENTRA_ID_SECRET = process.env.MICROSOFT_CLIENT_SECRET;
}

// ─── NextAuth Configuration (Edge Compatible) ────────────────────────────────
// This file contains providers and settings that must be available in the 
// Edge runtime (Middleware). Avoid Node-only dependencies here.
export const authConfig = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
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
    }),
    MicrosoftEntraId({
      clientId: process.env.MICROSOFT_CLIENT_ID,
      clientSecret: process.env.MICROSOFT_CLIENT_SECRET,
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
    }),
  ],
  trustHost: true,
  pages: {
    signIn: "/login",
    error: "/login",
  },
  callbacks: {
    authorized({ auth, request: { nextUrl } }: { auth: any; request: { nextUrl: any } }) {
      const isLoggedIn = !!auth?.user;
      const isDashboard = nextUrl.pathname.startsWith("/dashboard");
      if (isDashboard) {
        if (isLoggedIn) return true;
        return false; // Redirect unauthenticated users to login page
      }
      return true;
    },
  },
} satisfies NextAuthConfig;
