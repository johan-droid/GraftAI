import { NextResponse } from "next/server";
import { auth } from "@/lib/auth-server";
import { headers } from "next/headers";
import { BACKEND_API_URL } from "@/lib/backend";

export async function GET() {
  const reqHeaders = await headers();
  const session = await auth.api.getSession({ headers: reqHeaders });
  if (!session) return NextResponse.json({ plugins: [] }, { status: 401 });

  const res = await fetch(`${BACKEND_API_URL}/plugins/list`, {
    headers: { "Authorization": `Bearer ${session.session.token}` },
    next: { revalidate: 300 },
  });

  if (!res.ok) return NextResponse.json({ plugins: [] });
  return NextResponse.json(await res.json());
}
