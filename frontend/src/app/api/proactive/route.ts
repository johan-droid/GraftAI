import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { BACKEND_API_URL } from "@/lib/backend";

export async function GET() {
  const session = await auth();
  const backendToken = (session as any)?.backendToken || (session as any)?.session?.backendToken;
  if (!backendToken) {
    return NextResponse.json({ suggestion: null }, { status: 401 });
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  try {
    const res = await fetch(`${BACKEND_API_URL}/proactive/suggest`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${backendToken}`,
      },
      body: JSON.stringify({ context: "dashboard" }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    return res.ok
      ? NextResponse.json(await res.json())
      : NextResponse.json({ suggestion: null });
  } catch (err: any) {
    clearTimeout(timeoutId);
    return NextResponse.json({ suggestion: null });
  }
}
