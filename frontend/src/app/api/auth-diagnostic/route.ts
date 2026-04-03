import { NextResponse } from "next/server";

export async function GET() {
    const rawDatabaseUrl =
        process.env.FRONTEND_DATABASE_URL ||
        process.env.DATABASE_URL ||
        process.env.NEXT_PUBLIC_DATABASE_URL;
    
    const authSecret = process.env.BETTER_AUTH_SECRET || process.env.NEXTAUTH_SECRET;
    const betterAuthUrl = process.env.BETTER_AUTH_URL || process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";
    
    // Check social providers
    const socialProviders: string[] = [];
    if (process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET) socialProviders.push("google");
    if (process.env.GITHUB_CLIENT_ID && process.env.GITHUB_CLIENT_SECRET) socialProviders.push("github");
    if (process.env.MICROSOFT_CLIENT_ID && process.env.MICROSOFT_CLIENT_SECRET) socialProviders.push("microsoft");
    if (process.env.APPLE_CLIENT_ID && process.env.APPLE_CLIENT_SECRET) socialProviders.push("apple");
    if (process.env.ZOOM_CLIENT_ID && process.env.ZOOM_CLIENT_SECRET) socialProviders.push("zoom");
    if (process.env.SSO_OIDC_DISCOVERY_URL && process.env.SSO_OIDC_CLIENT_ID && process.env.SSO_OIDC_CLIENT_SECRET) socialProviders.push("sso-oidc");
    
    const diagnostics = {
        environment: process.env.NODE_ENV || "undefined",
        hasDatabase: !!rawDatabaseUrl,
        hasBetterAuthSecret: !!authSecret,
        betterAuthUrl: betterAuthUrl,
        nextPublicAppUrl: process.env.NEXT_PUBLIC_APP_URL || "NOT SET",
        databaseType: rawDatabaseUrl?.includes("postgresql")
            ? "PostgreSQL"
            : rawDatabaseUrl
                ? "Unknown/Invalid"
                : "Not Configured",
        dbConnectionStatus: rawDatabaseUrl ? "configured" : "not_configured",
        socialProviders: socialProviders,
        sessionCookieCandidates: ["better-auth.session_token", "graftai_access_token"],
        isProduction: process.env.NODE_ENV === "production",
    };

    return NextResponse.json(diagnostics);
}
