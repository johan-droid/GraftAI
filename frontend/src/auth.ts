import NextAuth, { NextAuthConfig } from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import MicrosoftEntraId from "next-auth/providers/microsoft-entra-id";

const nextAuthSecret = process.env.NEXTAUTH_SECRET || process.env.AUTH_SECRET || "your-development-fallback-secret-here";
if (process.env.NODE_ENV === "production" && !process.env.NEXTAUTH_SECRET && !process.env.AUTH_SECRET) {
  console.warn(
    "NEXTAUTH_SECRET/AUTH_SECRET is missing in production. The app will build, but authentication may be insecure until the value is provided."
  );
} else if (!process.env.NEXTAUTH_SECRET && !process.env.AUTH_SECRET) {
  console.warn("NEXTAUTH_SECRET/AUTH_SECRET is missing. This is required for secure sessions.");
}

const authOptions: NextAuthConfig = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
    }),
    MicrosoftEntraId({
      clientId: process.env.MICROSOFT_CLIENT_ID || "",
      clientSecret: process.env.MICROSOFT_CLIENT_SECRET || "",
      tenantId: process.env.MICROSOFT_TENANT_ID || "common",
    }),
  ],
  pages: {
    signIn: "/login", // The page where you show the Google sign-in button
  },
  callbacks: {
    async signIn({ user, account, profile }) {
      try {
        // Send the Google access token or id token to your backend to sync users
        // This simulates reconstructing the auth system where the backend creates the user
        const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1/auth/social/exchange`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            provider: account?.provider,
            provider_account_id: account?.providerAccountId,
            email: user?.email,
            name: user?.name,
            image: user?.image,
            access_token: account?.access_token,
            id_token: account?.id_token,
          }),
        });

        if (res.ok) {
          const data = await res.json();
          // Store backend tokens to pass along
          user.backendToken = data.access_token;
          user.refreshToken = data.refresh_token;
          return true;
        }
      } catch (error) {
        console.error("Failed to sync with backend", error);
      }
      return false; // Deny sign-in if backend sync fails (or handle fallback)
    },
    async jwt({ token, user, account }) {
      if (user && "backendToken" in user) {
        token.backendToken = user.backendToken;
        token.refreshToken = user.refreshToken;
      }
      return token;
    },
    async session({ session, token }) {
      // Expose the backend token so the frontend can make authenticated requests to FastAPI
      if (token.backendToken) {
        (session as any).backendToken = token.backendToken;
      }
      return session;
    },
  },
  secret: process.env.NEXTAUTH_SECRET || "your-development-fallback-secret-here",
};

export const { handlers, signIn, signOut, auth } = NextAuth(authOptions);
