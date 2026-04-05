import { NextResponse } from "next/server";

export async function GET() {
    const backendUrl =
        process.env.NEXT_PUBLIC_API_BASE_URL ||
        process.env.NEXT_PUBLIC_BACKEND_URL ||
        "http://localhost:8000";
    
    // Check social providers
    const socialProviders: string[] = [];
    if (process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET) socialProviders.push("google");
    if (process.env.MICROSOFT_CLIENT_ID && process.env.MICROSOFT_CLIENT_SECRET) socialProviders.push("microsoft");
    
    const diagnostics = {
        environment: process.env.NODE_ENV || "undefined",
        authMode: "backend-jwt-cookie",
        backendUrl: backendUrl,
        nextPublicAppUrl: process.env.NEXT_PUBLIC_APP_URL || "NOT SET",
        socialProviders: socialProviders,
        sessionCookieCandidates: ["graftai_access_token", "graftai_refresh_token", "xsrf-token"],
        isProduction: process.env.NODE_ENV === "production",
    };

    return NextResponse.json(diagnostics);
}
