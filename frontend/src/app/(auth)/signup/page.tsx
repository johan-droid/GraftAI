"use client";

import Link from "next/link";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { OAuthButtons } from "@/components/auth/OAuthButtons";

export default function SignupPage() {
  return (
    <AuthLayout
      title="Create your account"
      subtitle="Set up your workspace in seconds — no credit card required."
    >
      <div className="space-y-5">
        <OAuthButtons callbackURL="/dashboard" actionText="Sign up" />

        {/* Divider */}
        <div className="flex items-center gap-3">
          <div className="h-px flex-1 bg-[#DADCE0]" />
          <span className="text-[11px] font-medium text-[#9AA0A6] uppercase tracking-wider">secure</span>
          <div className="h-px flex-1 bg-[#DADCE0]" />
        </div>

        {/* Terms */}
        <p className="text-[12px] text-[#5F6368] text-center leading-relaxed max-w-xs mx-auto">
          By creating an account, you agree to the{" "}
          <Link href="/terms" className="text-[#1A73E8] hover:underline">
            Terms of Service
          </Link>{" "}
          and{" "}
          <Link href="/privacy" className="text-[#1A73E8] hover:underline">
            Privacy Policy
          </Link>
          .
        </p>

        {/* Switch link */}
        <div className="pt-4 border-t border-[#F1F3F4] text-center">
          <p className="text-[14px] text-[#5F6368]">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-medium text-[#1A73E8] hover:text-[#1557B0] transition-colors"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </AuthLayout>
  );
}
