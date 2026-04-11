import { headers } from "next/headers";
import { NextResponse } from "next/server";
import { auth } from "@/lib/auth-server";

const BACKEND =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "http://localhost:8000";

export async function GET() {
  const reqHeaders = await headers();
  const session = await auth.api.getSession({ headers: reqHeaders });
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let backendRes;
  try {
    backendRes = await fetch(`${BACKEND_API_URL}/auth/check`, {
      headers: {
        Authorization: `Bearer ${session.session.token}`,
        "Content-Type": "application/json",
      },
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
