import { auth } from "@/lib/auth-server";

export default auth.middleware({
  // Redirects unauthenticated users from dashboard to login
  loginUrl: "/login",
});

export const config = {
  matcher: [
    "/dashboard/:path*", // Protect all dashboard sub-routes
  ],
};
