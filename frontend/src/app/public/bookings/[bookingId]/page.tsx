"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { PublicBookingDetailsResponse, getPublicBookingDetails } from "@/lib/api";

export default function PublicBookingDetailsPage() {
  const params = useParams<{ bookingId: string }>();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const [booking, setBooking] = useState<PublicBookingDetailsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadBooking() {
      if (!token) {
        setError("Missing action token in URL.");
        setIsLoading(false);
        return;
      }

      try {
        const response = await getPublicBookingDetails(params.bookingId, token);
        if (!cancelled) {
          setBooking(response);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unable to load this booking.");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadBooking();
    return () => {
      cancelled = true;
    };
  }, [params.bookingId, token]);

  const canManage = booking?.status === "confirmed";

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 sm:px-6">
      <section className="mx-auto w-full max-w-2xl rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-indigo-600">Public Booking</p>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">Manage Booking</h1>

        {isLoading ? (
          <p className="mt-6 text-sm text-slate-600">Loading booking details...</p>
        ) : null}

        {error ? (
          <div className="mt-6 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
        ) : null}

        {booking ? (
          <>
            <dl className="mt-6 grid gap-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:grid-cols-2 sm:gap-5 sm:p-5">
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Event</dt>
                <dd className="mt-1 text-sm font-semibold text-slate-900">{booking.event_title}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Status</dt>
                <dd className="mt-1 text-sm font-semibold text-slate-900 capitalize">{booking.status}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Organizer</dt>
                <dd className="mt-1 text-sm text-slate-800">{booking.organizer_name}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Attendee</dt>
                <dd className="mt-1 text-sm text-slate-800">{booking.full_name} ({booking.email})</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Organizer Time</dt>
                <dd className="mt-1 text-sm text-slate-800">
                  {booking.organizer_start_time} - {booking.organizer_end_time}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Your Time</dt>
                <dd className="mt-1 text-sm text-slate-800">
                  {booking.invitee_start_time} - {booking.invitee_end_time} ({booking.invitee_zone})
                </dd>
              </div>
            </dl>

            {booking.meeting_url ? (
              <div className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                Meeting link: <a href={booking.meeting_url} className="font-semibold underline" target="_blank" rel="noreferrer">Join meeting</a>
              </div>
            ) : null}

            {canManage ? (
              <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                <Link
                  href={booking.reschedule_url}
                  className="inline-flex w-full items-center justify-center rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 sm:w-auto"
                >
                  Reschedule
                </Link>
                <Link
                  href={booking.cancel_url}
                  className="inline-flex w-full items-center justify-center rounded-xl border border-rose-200 bg-white px-4 py-3 text-sm font-semibold text-rose-700 transition hover:bg-rose-50 sm:w-auto"
                >
                  Cancel Booking
                </Link>
              </div>
            ) : (
              <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                This booking can no longer be changed from this page.
              </div>
            )}
          </>
        ) : null}
      </section>
    </main>
  );
}
