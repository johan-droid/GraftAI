import { betterAuth } from "better-auth";
import { magicLink } from "better-auth/plugins";
import { Pool } from "pg";

export const auth = betterAuth({
    baseURL: process.env.BETTER_AUTH_URL || process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
    database: new Pool({
        connectionString: process.env.DATABASE_URL,
        ssl: {
            rejectUnauthorized: false
        }
    }),
    secret: process.env.BETTER_AUTH_SECRET || process.env.NEXTAUTH_SECRET || "dev-fallback-secret-please-change",
    emailAndPassword: {
        enabled: true
    },
    socialProviders: {
        google: {
            clientId: process.env.GOOGLE_CLIENT_ID || "",
            clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
        }
    },
    plugins: [
        magicLink({
            sendMagicLink: async ({ email, url, token }) => {
                // In a real app, send an email here. For now, log it.
                console.log(`Magic link for ${email}: ${url} (token: ${token})`);
            }
        })
    ],
    trustedOrigins: [
        process.env.BETTER_AUTH_URL ||
        process.env.NEXT_PUBLIC_APP_URL ||
        "http://localhost:3000"
    ],
    user: {
        modelName: "users",
        fields: {
            emailVerified: "emailVerified",
            createdAt: "createdAt",
            updatedAt: "updatedAt"
        }
    },
    session: {
        modelName: "session",
        fields: {
            userId: "userId",
            expiresAt: "expiresAt",
            createdAt: "createdAt",
            updatedAt: "updatedAt",
            userAgent: "userAgent",
            ipAddress: "ipAddress"
        }
    },
    account: {
        modelName: "account",
        fields: {
            userId: "userId",
            accountId: "accountId",
            providerId: "providerId",
            accessToken: "accessToken",
            refreshToken: "refreshToken",
            idToken: "idToken",
            accessTokenExpiresAt: "accessTokenExpiresAt",
            refreshTokenExpiresAt: "refreshTokenExpiresAt",
            createdAt: "createdAt",
            updatedAt: "updatedAt"
        }
    }
});

const isVercel = process.env.VERCEL === "1";
if (!process.env.BETTER_AUTH_SECRET && process.env.NODE_ENV === "production") {
    console.warn(
        "BETTER_AUTH_SECRET is not set. In Vercel deploys, set BETTER_AUTH_SECRET in Environment Variables (and/or set NEXTAUTH_SECRET as fallback)."
    );
    if (!isVercel) {
        throw new Error(
            "BETTER_AUTH_SECRET is required in production for Better Auth. Set it in environment variables."
        );
    }
}
