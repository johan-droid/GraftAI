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

      return null;
    },
  },
};
