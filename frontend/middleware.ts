import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  // We completely bypass middleware-based auth protection because the
  // `graftai_access_token` is an HttpOnly cookie set on the BACKEND domain
  // (e.g. graftai.onrender.com). The Next.js frontend server (vercel.app)
  // physically cannot read this cookie.
  // Auth protection is handled strictly on the client side via the <AuthProvider>
  // and the backend API itself.
  return NextResponse.next();
}

export const config = {
  matcher: [] // Disable middleware execution to speed up navigations
};
