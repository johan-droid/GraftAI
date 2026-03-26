import { getConfiguredSocialProviders } from "@/lib/auth-server";
import { NextResponse } from "next/server";

export async function GET() {
  const providers = getConfiguredSocialProviders();
  return NextResponse.json({ providers });
}
