"use client";

import { useParams, useSearchParams } from "next/navigation";
import { useState } from "react";
import { cancelPublicBooking } from "@/lib/api";
import CancellationModal from "@/components/booking/CancellationModal";

export default function CancelBookingPage() {
  const params = useParams<{ bookingId: string }>();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null);

  async function onCancel(reason?: string) {
    setResult(null);

    if (!token) {
      setResult({ ok: false, message: "Missing action token in URL." });
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await cancelPublicBooking(params.bookingId, token, reason);
      setResult({ ok: true, message: response.message || "Booking cancelled successfully." });
      setIsModalOpen(false);
    } catch (error) {
      setResult({
        ok: false,
        message: error instanceof Error ? error.message : "Unable to cancel this booking.",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 sm:px-6">
      <section className="mx-auto w-full max-w-xl rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-indigo-600">Public Booking</p>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">Cancel Booking</h1>
        <p className="mt-2 text-sm text-slate-600">
          This action will release your slot and send cancellation updates to both you and the organizer.
        </p>

        {result ? (
          <div className={`mt-6 rounded-xl px-4 py-3 text-sm ${result.ok ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}>
            {result.message}
          </div>
        ) : null}

        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            disabled={isSubmitting || result?.ok === true}
            className="inline-flex w-full items-center justify-center rounded-xl bg-rose-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-rose-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {result?.ok ? "Booking Cancelled" : "Cancel Booking"}
          </button>
        </div>
      </section>

      <CancellationModal
        isOpen={isModalOpen}
        isSubmitting={isSubmitting}
        onClose={() => setIsModalOpen(false)}
        onConfirm={onCancel}
      />
    </main>
  );
}
