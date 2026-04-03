import { NextResponse } from "next/server";

export async function GET() {
    const providers = [];

    if (process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET) providers.push("google");
    if (process.env.GITHUB_CLIENT_ID && process.env.GITHUB_CLIENT_SECRET) providers.push("github");
    if (process.env.MICROSOFT_CLIENT_ID && process.env.MICROSOFT_CLIENT_SECRET) providers.push("microsoft");
    if (process.env.APPLE_CLIENT_ID && process.env.APPLE_CLIENT_SECRET) providers.push("apple");
    if (process.env.ZOOM_CLIENT_ID && process.env.ZOOM_CLIENT_SECRET) providers.push("zoom");
    if (process.env.SSO_OIDC_DISCOVERY_URL && process.env.SSO_OIDC_CLIENT_ID) providers.push("sso-oidc");

    return NextResponse.json({
        providers,
        env: process.env.NODE_ENV
    });
}
