import { createAuthClient } from "better-auth/react";
import { magicLinkClient, organizationClient, genericOAuthClient, twoFactorClient } from "better-auth/client/plugins";

function resolveAuthBaseURL(): string {
  // In browsers, always prefer same-origin because Better Auth routes live in this Next app.
  // This avoids accidental calls to backend domains when NEXT_PUBLIC_APP_URL is misconfigured.
  if (typeof window !== "undefined") {
    return window.location.origin.replace(/\/+$/g, "");
  }

  const configured = process.env.NEXT_PUBLIC_APP_URL?.trim();
  if (configured) {
    return configured.replace(/\/+$/g, "");
  }

  return "http://localhost:3000";
}

export const authClient = createAuthClient({
  baseURL: resolveAuthBaseURL(),
  plugins: [
    magicLinkClient(),
    organizationClient(),
    genericOAuthClient(),
    twoFactorClient()
  ]
});

/**
 * Compatibility helpers for existing code using manual fetch logic
 */

export function getToken(): string | null {
  if (typeof document === "undefined") return null;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; graftai_access_token=`);
  if (parts.length === 2) return parts.pop()?.split(";").shift() || null;
  return null;
}

export function getCsrfHeaders(): Record<string, string> {
  if (typeof document === "undefined") return {};
  const value = `; ${document.cookie}`;
  const parts = value.split(`; xsrf-token=`);
  const token = parts.length === 2 ? parts.pop()?.split(";").shift() || null : null;
  return token ? { "X-XSRF-TOKEN": token } : {};
}

export const getSessionSafe = async () => {
  try {
    const session = await authClient.getSession();
    return { data: session.data, error: session.error };
  } catch (err) {
    return { data: null, error: err };
  }
};

export const signOut = async () => {
  return await authClient.signOut();
};

export const signIn = {
  email: async ({ email, password }: { email: string; password: string }) => {
    return await authClient.signIn.email({
      email,
      password,
      callbackURL: "/dashboard",
    });
  },

  social: async ({ provider }: { provider: "google" | "github" | "microsoft" | "apple" | "zoom" }) => {
    if (provider === "zoom") {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return await (authClient.signIn as any).genericOAuth({
        providerId: "zoom",
        callbackURL: "/dashboard",
      });
    }
    return await authClient.signIn.social({
      provider,
      callbackURL: "/dashboard",
    });
  },

  magicLink: async ({ email }: { email: string }) => {
    return await authClient.signIn.magicLink({
      email,
      callbackURL: "/dashboard",
    });
  },

  zoom: async () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return await (authClient.signIn as any).genericOAuth({
      providerId: "zoom",
      callbackURL: "/dashboard",
    });
  },

  sso: async ({ callbackURL }: { callbackURL?: string } = {}) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return await (authClient.signIn as any).genericOAuth({
      providerId: "sso-oidc",
      callbackURL: callbackURL || "/dashboard",
    });
  },

  passkey: async () => {
    return { error: new Error("Passkey sign-in is not available on this login flow yet.") };
  },
};

export const signUp = async (email: string, password: string, name: string) => {
  return await authClient.signUp.email({
    email,
    password,
    name,
    callbackURL: "/dashboard",
  });
};
