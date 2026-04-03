import { betterAuth } from "better-auth";
import { magicLink, organization, genericOAuth, twoFactor } from "better-auth/plugins";
import { Pool } from "pg";

function resolveServerAuthUrl(): string {
    const explicit =
        process.env.BETTER_AUTH_URL ||
        process.env.NEXT_PUBLIC_AUTH_URL ||
        process.env.NEXT_PUBLIC_APP_URL ||
        process.env.APP_URL;

    if (explicit) {
        return explicit.replace(/\/+$/g, "");
    }

    if (process.env.VERCEL_URL) {
        return `https://${process.env.VERCEL_URL}`.replace(/\/+$/g, "");
    }

    console.warn(
        "[AUTH_BOOT] No BETTER_AUTH_URL/NEXT_PUBLIC_AUTH_URL/NEXT_PUBLIC_APP_URL set. Falling back to http://localhost:3000"
    );

    return "http://localhost:3000";
}

const resolvedAuthUrl = resolveServerAuthUrl();

const rawDatabaseUrl =
    process.env.FRONTEND_DATABASE_URL ||
    process.env.DATABASE_URL ||
    process.env.NEXT_PUBLIC_DATABASE_URL;

if (!rawDatabaseUrl && process.env.NODE_ENV === "production") {
    throw new Error(
        "FRONTEND_DATABASE_URL or DATABASE_URL is required in production for Better Auth."
    );
}

function sanitizeDatabaseUrl(url?: string): string | undefined {
    if (!url) return undefined;
    // Standardize protocol: Node.js 'pg' driver doesn't support '+asyncpg' or '+pg'
    return url.replace(/^postgresql\+[^:]+:/, "postgresql:").replace(/^postgres\+[^:]+:/, "postgres:");
}

const sanitizedDbUrl = sanitizeDatabaseUrl(rawDatabaseUrl);

let dbPool: Pool | undefined;

if (sanitizedDbUrl) {
    try {
        dbPool = new Pool({
            connectionString: sanitizedDbUrl,
            ssl:
                process.env.NODE_ENV === "production"
                    ? { rejectUnauthorized: false }
                    : false,
            max: 5, // Reduce for serverless and connection caps
            idleTimeoutMillis: 30000,
            connectionTimeoutMillis: 10000,
        });

        // Sanity check the connection without blocking startup too long.
        dbPool
            .query("SELECT 1")
            .then(() => {
                console.log("[DB_TEST_SUCCESS]: Connected to database for Better Auth");
            })
            .catch((err) => {
                console.error("[DB_TEST_ERROR]: Better Auth DB connection failed", err);
            });
    } catch (err) {
        console.error("[DB_POOL_ERROR]: Failed to create database pool", err);
        dbPool = undefined;
    }
} else {
    console.warn(
        "[DB_WARNING]: No database URL configured for Better Auth. This will use in-memory adapter and is not suitable for production."
    );
}

export const auth = betterAuth({
    baseURL: resolvedAuthUrl,
    database: dbPool,
    secret: process.env.BETTER_AUTH_SECRET || process.env.NEXTAUTH_SECRET || "dev-fallback-secret-please-change",
    emailAndPassword: {
        enabled: true
    },
    socialProviders: {
        ...(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET ? {
            google: {
                clientId: process.env.GOOGLE_CLIENT_ID,
                clientSecret: process.env.GOOGLE_CLIENT_SECRET,
            },
        } : {}),
        ...(process.env.GITHUB_CLIENT_ID && process.env.GITHUB_CLIENT_SECRET ? {
            github: {
                clientId: process.env.GITHUB_CLIENT_ID,
                clientSecret: process.env.GITHUB_CLIENT_SECRET,
            },
        } : {}),
        ...(process.env.MICROSOFT_CLIENT_ID && process.env.MICROSOFT_CLIENT_SECRET ? {
            microsoft: {
                clientId: process.env.MICROSOFT_CLIENT_ID,
                clientSecret: process.env.MICROSOFT_CLIENT_SECRET,
            },
        } : {}),
        ...(process.env.APPLE_CLIENT_ID && process.env.APPLE_CLIENT_SECRET ? {
            apple: {
                clientId: process.env.APPLE_CLIENT_ID,
                clientSecret: process.env.APPLE_CLIENT_SECRET,
            },
        } : {}),
    },
    plugins: [
        magicLink({
            sendMagicLink: async ({ email, url, token }) => {
                console.log(`Magic link for ${email}: ${url} (token: ${token})`);
            }
        }),
        organization({}),
        twoFactor({
            issuer: "GraftAI"
        }),
        genericOAuth({
            config: [
                ...(process.env.ZOOM_CLIENT_ID && process.env.ZOOM_CLIENT_SECRET ? [{
                    providerId: "zoom",
                    clientId: process.env.ZOOM_CLIENT_ID,
                    clientSecret: process.env.ZOOM_CLIENT_SECRET,
                    authorizationUrl: "https://zoom.us/oauth/authorize",
                    tokenUrl: "https://zoom.us/oauth/token",
                    getUserInfo: async (tokens: { accessToken?: string }) => {
                        const response = await fetch("https://api.zoom.us/v2/users/me", {
                            headers: {
                                Authorization: `Bearer ${tokens.accessToken ?? ""}`,
                            },
                        });
                        const user = await response.json();
                        return {
                            id: user.id || user.p_id, // Zoom standard ID field
                            email: user.email,
                            name: `${user.first_name} ${user.last_name}`,
                            emailVerified: true // Assume email is verified by Zoom
                        };
                    },
                }] : []),
                ...(process.env.SSO_OIDC_DISCOVERY_URL && process.env.SSO_OIDC_CLIENT_ID && process.env.SSO_OIDC_CLIENT_SECRET ? [{
                    providerId: "sso-oidc",
                    discoveryUrl: process.env.SSO_OIDC_DISCOVERY_URL,
                    clientId: process.env.SSO_OIDC_CLIENT_ID,
                    clientSecret: process.env.SSO_OIDC_CLIENT_SECRET,
                }] : [])
            ]
        })
    ],
    trustedOrigins: [
        resolvedAuthUrl
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

// Startup Diagnostics
if (process.env.NODE_ENV === "production") {
    console.log(`[AUTH_BOOT]: Better Auth URL: ${resolvedAuthUrl}`);
    if (sanitizedDbUrl) {
        const masked = sanitizedDbUrl.replace(/:([^@]+)@/, ":****@");
        console.log(`[AUTH_BOOT]: Database Configured: ${masked}`);
    } else {
        console.warn("[AUTH_BOOT]: DATABASE_URL is MISSING");
    }
}
