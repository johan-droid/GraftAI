const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://graftai.onrender.com";

async function postJson(path: string, payload: unknown) {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
    async email({ email, password, callbackURL }: { email: string; password: string; callbackURL: string }) {
      return postJson("/api/v1/auth/login", { email, password, callbackURL });
    },

    async social({ provider, callbackURL }: { provider: string; callbackURL: string }) {
      const redirectUrl = `${API_URL}/api/v1/auth/${provider}/login?redirect_uri=${encodeURIComponent(callbackURL)}`;
      if (typeof window !== "undefined") {
        window.location.href = redirectUrl;
      }
      return { error: null };
    },

    async magicLink({ email, callbackURL }: { email: string; callbackURL: string }) {
      return postJson("/api/v1/auth/magic-link", { email, callbackURL });
    },

    async passkey(_: Record<string, unknown>) {
      return postJson("/api/v1/auth/passkey", {});
    },
  },
};
