import { NextResponse } from "next/server";
import { headers } from "next/headers";
import { BACKEND_API_URL } from "@/lib/backend";
import { applyServerAuthCookies, resolveServerAccessToken } from "@/lib/server-auth";

export async function GET() {
  const reqHeaders = await headers();
  const tokenResolution = await resolveServerAccessToken(reqHeaders);
  if (!tokenResolution.accessToken) return NextResponse.json({ suggestion: null }, { status: 401 });

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  try {
    const res = await fetch(`${BACKEND_API_URL}/proactive/suggest`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${tokenResolution.accessToken}`,
      },
      body: JSON.stringify({ context: "dashboard" }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    const response = res.ok
      ? NextResponse.json(await res.json())
      : NextResponse.json({ suggestion: null });

    if (tokenResolution.refreshed) {
      applyServerAuthCookies(response, tokenResolution.accessToken, tokenResolution.refreshToken);
    }

    return response;
  } catch (err: any) {
    clearTimeout(timeoutId);
    return NextResponse.json({ suggestion: null });
  }
}
