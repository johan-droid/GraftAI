import { headers } from "next/headers";
import { NextResponse } from "next/server";
import { auth } from "@/lib/auth-server";
import { BACKEND_API_URL } from "@/lib/backend";

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
