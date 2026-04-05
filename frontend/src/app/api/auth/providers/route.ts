import { NextResponse } from "next/server";

export async function GET() {
    const providers: string[] = [];

    const googleConfigured = Boolean(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET);
    const microsoftConfigured = Boolean(process.env.MICROSOFT_CLIENT_ID && process.env.MICROSOFT_CLIENT_SECRET);

    if (googleConfigured) providers.push("google");
    if (microsoftConfigured) providers.push("microsoft");

    const details = {
        google: { configured: googleConfigured },
        microsoft: { configured: microsoftConfigured },
    };

    return NextResponse.json({
        providers,
        details,
        env: process.env.NODE_ENV,
    });
}
