import { NextResponse } from "next/server";
import { auth } from "@/lib/auth-server";
import { headers } from "next/headers";
import { BACKEND_API_URL } from "@/lib/backend";

export async function GET() {
  const reqHeaders = await headers();
  const session = await auth.api.getSession({ headers: reqHeaders });
  if (!session) return NextResponse.json({ suggestion: null }, { status: 401 });

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  try {
    const res = await fetch(`${BACKEND_API_URL}/proactive/suggest`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${session.session.token}`,
      },
      body: JSON.stringify({ context: "dashboard" }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!res.ok) return NextResponse.json({ suggestion: null });
    return NextResponse.json(await res.json());
  } catch (err: any) {
    clearTimeout(timeoutId);
    return NextResponse.json({ suggestion: null });
  }
}
