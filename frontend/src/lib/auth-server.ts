import { betterAuth } from "better-auth";
import { Pool } from "pg";

export const auth = betterAuth({
    database: new Pool({
        connectionString: process.env.DATABASE_URL,
        ssl: {
            rejectUnauthorized: false
        }
    }),
    emailAndPassword: {
        enabled: true
    },
    socialProviders: {
        google: {
            clientId: process.env.GOOGLE_CLIENT_ID || "",
            clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
            redirectURI: process.env.GOOGLE_REDIRECT_URI || ""
        }
    },
    trustedOrigins: [
        process.env.BETTER_AUTH_URL ||
        process.env.NEXT_PUBLIC_APP_URL ||
        "http://localhost:3000"
    ],
    secret: process.env.BETTER_AUTH_SECRET || process.env.NEXTAUTH_SECRET || "dev-fallback-secret-please-change",
    user: {
        modelName: "users",
    }
});

const isVercel = process.env.VERCEL === "1";
if (!process.env.BETTER_AUTH_SECRET && process.env.NODE_ENV === "production") {
    /* eslint-disable no-console */
    console.warn(
        "BETTER_AUTH_SECRET is not set. In Vercel deploys, set BETTER_AUTH_SECRET in Environment Variables (and/or set NEXTAUTH_SECRET as fallback)."
    );
    if (!isVercel) {
        throw new Error(
            "BETTER_AUTH_SECRET is required in production for Better Auth. Set it in environment variables."
        );
    }
    /* eslint-enable no-console */
}
