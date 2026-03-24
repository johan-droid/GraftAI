"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { setToken } from "@/lib/auth";

export default function AuthCallback() {
  const router = useRouter();
  const [status, setStatus] = useState("Processing...");

  const code = typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("code") : null;
  const state = typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("state") : null;

  useEffect(() => {
    if (!code || !state) {
      return;
    }

    const fetchCallback = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/sso/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}&fetch=true`,
          {
            headers: {
              "Accept": "application/json",
            },
          }
        );
        const data = await response.json();

        if (!response.ok) {
          const errorMsg = data.detail || `Server error (${response.status})`;
          console.error("SSO Error:", data);
          setStatus(errorMsg);
          return;
        }

        if (data.token?.access_token) {
          setToken(data.token.access_token);
          const finalRedirect = data.redirect_to || "/dashboard";
          router.replace(finalRedirect);
          return;
        }

        setStatus("No access token returned from callback");
      } catch (err) {
        console.error("Fetch failure:", err);
        setStatus("Connection error: Ensure NEXT_PUBLIC_API_BASE_URL is set on Vercel.");
      }
    };

    fetchCallback();
  }, [code, state, router]);

  if (!code || !state) {
    return (
      <main className="app-shell flex min-h-screen items-center justify-center px-4 py-8">
        <div className="w-full max-w-md rounded-2xl bg-white p-6 text-center shadow-xl dark:bg-slate-900">
          <p className="text-base text-slate-700 dark:text-slate-200">Missing SSO code/state</p>
        </div>
      </main>
    );
  }

  return (
    <main className="app-shell flex min-h-screen items-center justify-center px-4 py-8">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 text-center shadow-xl dark:bg-slate-900">
        <p className="text-base text-slate-700 dark:text-slate-200">{status}</p>
      </div>
    </main>
  );
}
