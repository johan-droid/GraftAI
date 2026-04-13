import { auth as nextAuth } from "@/auth";

export const auth = {
  api: {
    getSession: async ({ headers }: { headers: any }) => {
      const authHeader = headers.get("authorization");
      if (authHeader?.startsWith("Bearer ")) {
        return { session: { token: authHeader.split(" ")[1] } };
      }

      const cookieHeader = headers.get("cookie");
      if (cookieHeader) {
        const parseCookie = (name: string) => {
          const match = cookieHeader.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
          return match ? decodeURIComponent(match[1]) : null;
        };

        const authToken = parseCookie("auth_token") || parseCookie("graftai_access_token");
        if (authToken) {
          return { session: { token: authToken } };
        }
      }

      try {
        const session = await nextAuth();
        const backendToken = (session as any)?.backendToken || (session as any)?.session?.backendToken;
        if (backendToken) {
          return { session: { token: backendToken } };
        }
      } catch (error) {
        console.warn("NextAuth session resolution failed:", error);
      }

      return null;
    },
  },
};
