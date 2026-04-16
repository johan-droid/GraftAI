import NextAuth, { NextAuthOptions, Session } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { nextAuthSecret } from "@/auth";

interface AuthProviderUser {
  id: string;
  email: string;
  name: string;
  role: string;
  accessToken: string;
}

interface TokenWithAuth {
  accessToken?: string;
  id?: string;
  role?: string;
  name?: string;
  [key: string]: unknown;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error("Missing credentials");
        }

        try {
          const formData = new URLSearchParams();
          formData.append("username", credentials.email);
          formData.append("password", credentials.password);

          const res = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData.toString(),
          });

          const data = await res.json() as { detail?: string; access_token?: string };

          if (!res.ok) {
            throw new Error(data.detail || "Authentication failed");
          }

          const userRes = await fetch(`${API_URL}/users/me`, {
            headers: { Authorization: `Bearer ${data.access_token}` },
          });

          if (!userRes.ok) {
            const body = await userRes.text().catch(() => "");
            throw new Error(`Failed fetching user profile: ${userRes.status} ${body}`);
          }

          const userData = await userRes.json();

          return {
            id: userData.id,
            email: userData.email,
            name: userData.name,
            role: userData.role,
            accessToken: data.access_token,
          } as AuthProviderUser;
        } catch (error) {
          const err = error as { message?: string } | undefined;
          console.error("NextAuth Authorize Error:", err?.message ?? error);
          return null;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user, trigger, session }) {
      const authToken = token as TokenWithAuth;
      const authUser = user as AuthProviderUser | undefined;

      if (authUser) {
        authToken.accessToken = authUser.accessToken;
        authToken.id = authUser.id;
        authToken.role = authUser.role;
      }

      if (trigger === "update" && session?.name) {
        authToken.name = session.name;
      }

      return authToken;
    },
    async session({ session, token }) {
      const authToken = token as TokenWithAuth;
      const nextSession = session as Session & { accessToken?: string };

      if (authToken) {
        nextSession.user.id = authToken.id as string;
        nextSession.user.role = authToken.role as string;
        nextSession.accessToken = authToken.accessToken;
      }
      return nextSession;
    },
  },
  pages: {
    signIn: "/login",
    signOut: "/login",
    error: "/login",
  },
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60,
  },
  secret: nextAuthSecret,
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
