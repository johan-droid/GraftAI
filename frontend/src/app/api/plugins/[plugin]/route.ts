import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { BACKEND_API_URL } from "@/lib/backend";

export async function POST(
  request: Request,
  { params }: { params: { plugin: string } }
) {
  const pluginId = params.plugin;
  const session = await auth();
  const backendToken = (session as any)?.backendToken || (session as any)?.session?.backendToken;
  if (!backendToken) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const backendRes = await fetch(`${BACKEND_API_URL}/plugins/${encodeURIComponent(pluginId)}/enable`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${backendToken}`,
      "Content-Type": "application/json",
    },
    cache: "no-store",
  });

  const data = await backendRes.json().catch(() => ({}));
  return NextResponse.json(data, { status: backendRes.status });
}
