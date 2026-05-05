"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { OAuthButtons } from "@/components/auth/OAuthButtons";

function isValidCallbackUrl(value: string | null): value is string {
  if (!value || value.trim() === "") return false;
  if (value.startsWith("/") && !value.startsWith("//")) return true;

  try {
    const baseOrigin =
      typeof window !== "undefined" ? window.location.origin : "https://www.graftai.tech";
    const url = new URL(value, baseOrigin);
    const trustedHosts = ["www.graftai.tech", "graftai.tech", "localhost", "127.0.0.1"];
    return trustedHosts.includes(url.hostname);
  } catch {
    return false;
  }
}

export default function LoginPage() {
  const searchParams = useSearchParams();
  const requestedCallbackUrl = searchParams.get("callbackUrl");
  const authError = searchParams.get("error");
  const callbackUrl = isValidCallbackUrl(requestedCallbackUrl)
    ? requestedCallbackUrl
    : "/dashboard";
  const authErrorMessage = authError
    ? "Sign in could not be completed. Please try again, or check the production auth configuration if this keeps happening."
    : null;

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to pick up your schedule, messages, and automations where you left off."
    >
      <div className="space-y-5">
        {authErrorMessage ? (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {authErrorMessage}
          </div>
        ) : null}

        <OAuthButtons callbackURL={callbackUrl} actionText="Sign in" />

        {/* Divider */}
        <div className="flex items-center gap-3">
          <div className="h-px flex-1 bg-[#DADCE0]" />
          <span className="text-[11px] font-medium text-[#9AA0A6] uppercase tracking-wider">or</span>
          <div className="h-px flex-1 bg-[#DADCE0]" />
        </div>

        {/* Tip */}
        <p className="text-[13px] text-[#5F6368] text-center leading-relaxed">
          On a shared device? A private window or quick sign-out keeps things tidy.
        </p>

        {/* Switch link */}
        <div className="pt-4 border-t border-[#F1F3F4] text-center">
          <p className="text-[14px] text-[#5F6368]">
            Don&apos;t have an account?{" "}
            <Link
              href="/signup"
              className="font-medium text-[#1A73E8] hover:text-[#1557B0] transition-colors"
            >
              Create account
            </Link>
          </p>
        </div>
      </div>
    </AuthLayout>
  );
}
