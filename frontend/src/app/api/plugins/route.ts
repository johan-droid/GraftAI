import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { BACKEND_API_URL } from "@/lib/backend";

export async function GET() {
  const session = await auth();
  const backendToken = (session as any)?.backendToken || (session as any)?.session?.backendToken;
  if (!backendToken) {
    return NextResponse.json({ plugins: [] }, { status: 401 });
  }

  const res = await fetch(`${BACKEND_API_URL}/plugins/list`, {
    headers: { "Authorization": `Bearer ${backendToken}` },
    cache: "no-store",
  });

  if (!res.ok) {
    return NextResponse.json({ plugins: [] }, { status: res.status });
  }

  return NextResponse.json(await res.json());
}
