import { betterAuth } from "better-auth";
import { magicLink, organization, genericOAuth, twoFactor } from "better-auth/plugins";
import { Pool } from "pg";

// Helper to resolve the auth server URL
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

// Database URL resolution with sanitization
const rawDatabaseUrl =
    process.env.FRONTEND_DATABASE_URL ||
    process.env.DATABASE_URL ||
    process.env.NEXT_PUBLIC_DATABASE_URL;

function sanitizeDatabaseUrl(url?: string): string | undefined {
    if (!url) return undefined;
    // Standardize protocol: Node.js 'pg' driver doesn't support '+asyncpg' or '+pg'
    return url.replace(/^postgresql\+[^:]+:/, "postgresql:").replace(/^postgres\+[^:]+:/, "postgres:");
}

const sanitizedDbUrl = sanitizeDatabaseUrl(rawDatabaseUrl);

// Validate required configuration in production
if (!sanitizedDbUrl && process.env.NODE_ENV === "production") {
    throw new Error(
        "FRONTEND_DATABASE_URL or DATABASE_URL is required in production for Better Auth."
    );
}

// Create database pool
let dbPool: Pool | undefined;
let dbConnectionError: Error | null = null;

if (sanitizedDbUrl) {
    try {
        dbPool = new Pool({
            connectionString: sanitizedDbUrl,
            ssl:
                process.env.NODE_ENV === "production"
                    ? { rejectUnauthorized: false }
                    : false,
            max: 5,
            idleTimeoutMillis: 30000,
            connectionTimeoutMillis: 10000,
        });

        // Test database connection synchronously where possible
        // The actual test happens async but we track errors
        dbPool
            .query("SELECT 1")
            .then(() => {
                console.log("[DB_TEST_SUCCESS]: Connected to database for Better Auth");
            })
            .catch((err) => {
                console.error("[DB_TEST_ERROR]: Better Auth DB connection failed", err);
                dbConnectionError = err;
            });
    } catch (err) {
        console.error("[DB_POOL_ERROR]: Failed to create database pool", err);
        dbConnectionError = err as Error;
        dbPool = undefined;
    }
} else {
    console.warn(
        "[DB_WARNING]: No database URL configured for Better Auth. This will use in-memory adapter and is not suitable for production."
    );
}

// Validate secret key
const authSecret = process.env.BETTER_AUTH_SECRET || process.env.NEXTAUTH_SECRET;
const isVercel = process.env.VERCEL === "1";

if (!authSecret && process.env.NODE_ENV === "production" && !isVercel) {
    throw new Error(
        "BETTER_AUTH_SECRET is required in production for Better Auth. Set it in environment variables."
    );
}

if (!authSecret) {
    console.warn("[AUTH_BOOT]: Using default secret - NOT SECURE for production!");
}

// Build social providers config
function buildSocialProviders() {
    const providerConfig: Record<string, unknown> = {};

    if (process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET) {
        providerConfig.google = {
            clientId: process.env.GOOGLE_CLIENT_ID,
            clientSecret: process.env.GOOGLE_CLIENT_SECRET,
        };
    }

    if (process.env.GITHUB_CLIENT_ID && process.env.GITHUB_CLIENT_SECRET) {
        providerConfig.github = {
            clientId: process.env.GITHUB_CLIENT_ID,
            clientSecret: process.env.GITHUB_CLIENT_SECRET,
        };
    }

    if (process.env.MICROSOFT_CLIENT_ID && process.env.MICROSOFT_CLIENT_SECRET) {
        providerConfig.microsoft = {
            clientId: process.env.MICROSOFT_CLIENT_ID,
            clientSecret: process.env.MICROSOFT_CLIENT_SECRET,
        };
    }

    if (process.env.APPLE_CLIENT_ID && process.env.APPLE_CLIENT_SECRET) {
        providerConfig.apple = {
            clientId: process.env.APPLE_CLIENT_ID,
            clientSecret: process.env.APPLE_CLIENT_SECRET,
        };
    }

    // Zoom OAuth configuration
    if (process.env.ZOOM_CLIENT_ID && process.env.ZOOM_CLIENT_SECRET) {
        providerConfig.zoom = {
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
                    id: user.id || user.p_id,
                    email: user.email,
                    name: `${user.first_name} ${user.last_name}`,
                    emailVerified: true,
                };
            },
        };
    }

    // Generic OIDC for enterprise SSO
    if (process.env.SSO_OIDC_DISCOVERY_URL && process.env.SSO_OIDC_CLIENT_ID && process.env.SSO_OIDC_CLIENT_SECRET) {
        providerConfig["sso-oidc"] = {
            providerId: "sso-oidc",
            discoveryUrl: process.env.SSO_OIDC_DISCOVERY_URL,
            clientId: process.env.SSO_OIDC_CLIENT_ID,
            clientSecret: process.env.SSO_OIDC_CLIENT_SECRET,
        };
    }

    const names = Object.keys(providerConfig);
    if (names.length === 0) {
        console.warn("[AUTH_BOOT]: No social providers configured. Email/password authentication is still available.");
    } else {
        console.log(`[AUTH_BOOT]: Social providers configured: ${names.join(", ")}`);
    }

    return providerConfig;
}

const socialProviders = buildSocialProviders();

// Initialize Better Auth
export const auth = betterAuth({
    baseURL: resolvedAuthUrl,
    database: dbPool,
    secret: authSecret || "dev-fallback-secret-please-change-in-production-min-32-chars",
    emailAndPassword: {
        enabled: true,
        requireEmailVerification: false, // Can be enabled in production
    },
    socialProviders: socialProviders,
    plugins: [
        magicLink({
            sendMagicLink: async ({ email, url, token }) => {
                console.log(`[MAGIC_LINK] Magic link for ${email}: ${url}`);
                // TODO: Implement actual email sending
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
                            id: user.id || user.p_id,
                            email: user.email,
                            name: `${user.first_name} ${user.last_name}`,
                            emailVerified: true,
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
        resolvedAuthUrl,
        ...(process.env.TRUSTED_ORIGINS ? process.env.TRUSTED_ORIGINS.split(",") : [])
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
    },
    // Advanced security settings
    advanced: {
        // Cookie settings
        cookiePrefix: "better-auth",
        cookieOptions: {
            sameSite: process.env.NODE_ENV === "production" ? "none" : "lax",
            secure: process.env.NODE_ENV === "production",
            path: "/",
        },
        // CSRF protection
        useSecureCookies: process.env.NODE_ENV === "production",
    }
});

// Export connection status for diagnostics
export const getAuthStatus = () => ({
    hasDatabase: !!sanitizedDbUrl,
    hasPool: !!dbPool,
    hasConnection: !dbConnectionError,
    connectionError: dbConnectionError?.message,
    hasSecret: !!authSecret,
    authUrl: resolvedAuthUrl,
    socialProviders: Object.keys(socialProviders),
    isProduction: process.env.NODE_ENV === "production",
});
