import { NextResponse } from "next/server";

export async function GET(req: Request) {
    // SEC-04: Block unauthenticated configuration disclosure
    if ((process.env.NODE_ENV as string) === "production") {
        return NextResponse.json({ error: "Not Found" }, { status: 404 });
    }

    // Optional: require a specific header even in dev to prevent accidental leakage via open dev ports
    const authHeader = req.headers.get("x-graftai-debug");
    if (process.env.DEBUG_TOKEN && authHeader !== process.env.DEBUG_TOKEN) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

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
        isProduction: (process.env.NODE_ENV as string) === "production",
    };

    return NextResponse.json(diagnostics);
}
