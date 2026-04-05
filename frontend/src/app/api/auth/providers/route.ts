import { NextResponse } from "next/server";

export async function GET() {
    const providers = [];

    if (process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET) providers.push("google");
    if (process.env.MICROSOFT_CLIENT_ID && process.env.MICROSOFT_CLIENT_SECRET) providers.push("microsoft");

    return NextResponse.json({
        providers,
        env: process.env.NODE_ENV
    });
}
