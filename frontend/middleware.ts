import { auth } from "@/auth";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export default auth(async function middleware(request: NextRequest & { auth: any }) {
  // 1. Generate Nonce
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");

  // 2. Define CSP Policy
  const cspHeader = `
    default-src 'self';
    script-src 'self' 'nonce-${nonce}' 'strict-dynamic' 'unsafe-eval';
    style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
    img-src 'self' blob: data: https:;
    font-src 'self' https://fonts.gstatic.com;
    object-src 'none';
    base-uri 'none';
    form-action 'self';
    frame-ancestors 'none';
    frame-src 'self' https://checkout.razorpay.com https://api.razorpay.com;
    connect-src 'self' 
      https://*.onrender.com 
      https://*.vercel.app 
      https://ipapi.co
      ${process.env.NEXT_PUBLIC_API_BASE_URL || ""} 
      ${process.env.NEXT_PUBLIC_BACKEND_URL || ""};
    upgrade-insecure-requests;
  `.replace(/\s{2,}/g, " ").trim();

  // 3. Set Request Headers
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", cspHeader);

  // 4. Protected Route Logic
  const isDashboardRoute = request.nextUrl.pathname.startsWith("/dashboard");
  const isAuthenticated = !!request.auth;

  if (isDashboardRoute && !isAuthenticated) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("callbackUrl", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  const response = NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  });

  // 5. Set Response Headers
  response.headers.set("Content-Security-Policy", cspHeader);

  return response;
});

export const config = {
  matcher: ["/dashboard", "/dashboard/:path*", "/((?!api|_next/static|_next/image|favicon.ico).*)"],
};

