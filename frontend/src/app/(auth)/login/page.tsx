"use client";

import Link from "next/link";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { OAuthButtons } from "@/components/auth/OAuthButtons";

export default function LoginPage() {
  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to pick up your schedule, messages, and automations where you left off."
    >
      <div className="space-y-5">
        <OAuthButtons callbackURL="/dashboard" actionText="Sign in" />

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
