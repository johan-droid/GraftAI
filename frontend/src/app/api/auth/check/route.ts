import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { BACKEND_API_URL } from "@/lib/backend";

export async function GET() {
  const session = await auth();
  const backendToken = (session as any)?.backendToken || (session as any)?.session?.backendToken;
  if (!backendToken) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let backendRes;
  try {
    backendRes = await fetch(`${BACKEND_API_URL}/auth/check`, {
      headers: {
        Authorization: `Bearer ${backendToken}`,
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });
  } catch (error) {
    console.error("Backend unreachable", error);
    return NextResponse.json({ error: "Backend unreachable" }, { status: 502 });
  }

  if (!backendRes.ok) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const data = await backendRes.json();
  return NextResponse.json(data);
}
