"use client";

import { useState } from "react";

interface EmailVerificationProps {
  email: string;
  onResend?: () => Promise<void>;
}

export default function EmailVerification({ email, onResend }: EmailVerificationProps) {
  const [isResending, setIsResending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleResend = async () => {
    if (!onResend) {
      setMessage("A confirmation email resend request would be triggered here.");
      return;
    }

    setIsResending(true);
    setMessage(null);
    try {
      await onResend();
      setMessage("Verification email resent successfully.");
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Unable to resend the verification email. Please try again."
      );
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6 text-sm text-slate-700 shadow-sm">
      <p className="font-semibold text-slate-900">Verify your email address</p>
      <p className="mt-3">
        A confirmation link has been sent to <strong>{email}</strong>. Check your inbox and follow the link to complete the booking.
      </p>
      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
        <button
          type="button"
          onClick={handleResend}
          disabled={isResending}
          className="inline-flex items-center justify-center rounded-2xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {isResending ? "Resending..." : "Resend confirmation email"}
        </button>
        <p className="text-slate-500">If you don&apos;t see it, check spam or use a different email provider.</p>
      </div>
      {message ? (
        <p className="mt-4 rounded-2xl bg-slate-100 px-4 py-3 text-sm text-slate-700">{message}</p>
      ) : null}
    </div>
  );
}
