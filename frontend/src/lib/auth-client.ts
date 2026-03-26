import { createAuthClient } from "better-auth/react";

export const authClient = createAuthClient({
    baseURL: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"
});

/**
 * Compatibility helper for existing code that uses getSessionSafe.
 * Returns the current session in a format expected by the application.
 */
export const getSessionSafe = async () => {
    try {
        const session = await authClient.getSession();
        return session;
    } catch (err) {
        console.error("Failed to get session safely", err);
        return { data: null, error: err };
    }
};

/**
 * Compatibility helper for existing code that uses signOut.
 */
export const signOut = async () => {
    return await authClient.signOut();
};

/**
 * Compatibility helper for Social Sign In.
 */
export const signInSocial = async (provider: "google" | "github") => {
    return await authClient.signIn.social({
        provider,
        callbackURL: "/auth-callback"
    });
};

/**
 * Compatibility helper for Email Sign Up.
 */
export const signUp = async (email: string, password: string, name: string) => {
    return await authClient.signUp.email({
        email,
        password,
        name,
        callbackURL: "/dashboard"
    });
};
