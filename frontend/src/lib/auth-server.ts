export const auth = {
  api: {
    getSession: async ({ headers }: { headers: any }) => {
      const authHeader = headers.get("authorization");
      if (authHeader?.startsWith("Bearer ")) {
        return { session: { token: authHeader.split(" ")[1] } };
      }
      
      const cookieHeader = headers.get("cookie");
      if (cookieHeader?.includes("auth_token=")) {
         const token = cookieHeader.split("auth_token=")[1].split(";")[0];
         return { session: { token } };
      }
      return null;
    }
  }
};
