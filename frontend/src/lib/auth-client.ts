const API_URL = "/api/auth";

async function postJson(path: string, payload: unknown) {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  });

  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message =
      typeof body.detail === "string"
        ? body.detail
        : typeof body.message === "string"
        ? body.message
        : "Request failed";
    return { error: { message } };
  }
  return { data: body };
}

export const authClient = {
  signIn: {
    async email({ email, password }: { email: string; password: string }) {
      return postJson("/signin", { email, password });
    },

    async social({ provider, callbackURL }: { provider: string; callbackURL: string }) {
      const redirectTarget = callbackURL === "/auth-callback" ? "/dashboard" : callbackURL;
      const redirectUrl = `/api/auth/social/${encodeURIComponent(provider)}?redirect_to=${encodeURIComponent(
        redirectTarget
      )}`;
      if (typeof window !== "undefined") {
        window.location.href = redirectUrl;
      }
      return { error: null };
    },
  },
};
