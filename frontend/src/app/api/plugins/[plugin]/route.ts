import { headers } from "next/headers";
import { NextResponse } from "next/server";
import { BACKEND_API_URL } from "@/lib/backend";
import { applyServerAuthCookies, resolveServerAccessToken } from "@/lib/server-auth";

export async function POST(
  request: Request,
  { params }: { params: { plugin: string } }
) {
  const pluginId = params.plugin;
  const reqHeaders = await headers();
  const tokenResolution = await resolveServerAccessToken(reqHeaders);
  if (!tokenResolution.accessToken) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const backendRes = await fetch(`${BACKEND_API_URL}/plugins/${encodeURIComponent(pluginId)}/enable`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${tokenResolution.accessToken}`,
      "Content-Type": "application/json",
    },
    cache: "no-store",
  });

  const data = await backendRes.json().catch(() => ({}));
  const response = NextResponse.json(data, { status: backendRes.status });

  if (tokenResolution.refreshed) {
    applyServerAuthCookies(response, tokenResolution.accessToken, tokenResolution.refreshToken);
  }

  return response;
}
