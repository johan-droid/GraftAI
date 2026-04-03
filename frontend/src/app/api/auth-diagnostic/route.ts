import { NextResponse } from "next/server";

export async function GET() {
    const diagnostics = {
        environment: process.env.NODE_ENV || "undefined",
        hasDatabase: Boolean(process.env.DATABASE_URL || process.env.FRONTEND_DATABASE_URL),
        hasBetterAuthSecret: Boolean(process.env.BETTER_AUTH_SECRET),
        betterAuthUrl: process.env.BETTER_AUTH_URL || "NOT SET",
        nextPublicAppUrl: process.env.NEXT_PUBLIC_APP_URL || "NOT SET",
        databaseType: (process.env.DATABASE_URL || process.env.FRONTEND_DATABASE_URL)?.includes("postgresql")
            ? "PostgreSQL"
            : "Unknown",
        sessionCookieCandidates: ["better-auth.session_token", "graftai_access_token"],
    };

    return NextResponse.json(diagnostics);
}
