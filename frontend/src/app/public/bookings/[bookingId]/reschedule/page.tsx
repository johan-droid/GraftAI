"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  PublicAvailabilitySlot,
  PublicBookingDetailsResponse,
  getPublicBookingDetails,
  getPublicEventAvailabilityByDate,
  reschedulePublicBooking,
} from "@/lib/api";

function toLocalDateInputValue(date: Date) {
  const copy = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return copy.toISOString().slice(0, 10);
}

function slotLabel(slot: PublicAvailabilitySlot) {
  return `${slot.invitee_start} - ${slot.invitee_end} (${slot.invitee_zone})`;
}

export default function RescheduleBookingPage({ params }: { params: { bookingId: string } }) {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const [timeZone, setTimeZone] = useState("UTC");
  const [booking, setBooking] = useState<PublicBookingDetailsResponse | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(() => toLocalDateInputValue(new Date()));
  const [slots, setSlots] = useState<PublicAvailabilitySlot[]>([]);
  const [selectedSlotStart, setSelectedSlotStart] = useState<string>("");
  const [isLoadingBooking, setIsLoadingBooking] = useState(true);
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);
  const [pageError, setPageError] = useState<string>("");
  const [slotError, setSlotError] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null);

  const minDate = useMemo(() => toLocalDateInputValue(new Date()), []);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const detected = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
      setTimeZone(detected);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadBookingDetails() {
      setPageError("");
      setResult(null);

      if (!token) {
        setPageError("Missing action token in URL.");
        setIsLoadingBooking(false);
        return;
      }

      setIsLoadingBooking(true);
      try {
        const response = await getPublicBookingDetails(params.bookingId, token);
        if (!cancelled) {
          setBooking(response);
        }
      } catch (error) {
        if (!cancelled) {
          setPageError(error instanceof Error ? error.message : "Unable to load this booking.");
        }
      } finally {
        if (!cancelled) {
          setIsLoadingBooking(false);
        }
      }
    }

    void loadBookingDetails();
    return () => {
      cancelled = true;
    };
  }, [params.bookingId, token]);

  useEffect(() => {
    let cancelled = false;

    async function loadSlots() {
      if (!booking || !booking.event_type_slug || booking.status === "cancelled") {
        setSlots([]);
        setSelectedSlotStart("");
        return;
      }

      setIsLoadingSlots(true);
      setSlotError("");
      try {
        const response = await getPublicEventAvailabilityByDate(
          booking.organizer_username,
          booking.event_type_slug,
          selectedDate,
          timeZone
        );

        if (!cancelled) {
          setSlots(response.slots || []);
          setSelectedSlotStart((response.slots && response.slots.length > 0) ? response.slots[0].start : "");
        }
      } catch (error) {
        if (!cancelled) {
          setSlots([]);
          setSelectedSlotStart("");
          setSlotError(error instanceof Error ? error.message : "Unable to load slots for this date.");
        }
      } finally {
        if (!cancelled) {
          setIsLoadingSlots(false);
        }
      }
    }

    void loadSlots();
    return () => {
      cancelled = true;
    };
  }, [booking, selectedDate, timeZone]);

  const canReschedule = Boolean(booking && booking.status !== "cancelled" && booking.event_type_slug);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setResult(null);

    if (!token || !booking) {
      setResult({ ok: false, message: "Unable to validate booking action token." });
      return;
    }

    if (!canReschedule) {
      setResult({ ok: false, message: "This booking cannot be rescheduled." });
      return;
    }

    if (!selectedSlotStart) {
      setResult({ ok: false, message: "Please select an available slot." });
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await reschedulePublicBooking(params.bookingId, token, {
        new_start_time: selectedSlotStart,
        time_zone: timeZone,
      });
      setResult({ ok: true, message: response.message || "Booking rescheduled successfully." });

      const refreshed = await getPublicBookingDetails(params.bookingId, token);
      setBooking(refreshed);
    } catch (error) {
      setResult({
        ok: false,
        message: error instanceof Error ? error.message : "Unable to reschedule this booking.",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 sm:px-6">
      <section className="mx-auto w-full max-w-xl rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-indigo-600">Public Booking</p>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">Reschedule Booking</h1>
        <p className="mt-2 text-sm text-slate-600">
          Choose a new slot in your local timezone (<strong>{timeZone}</strong>).
        </p>

        {isLoadingBooking ? (
          <p className="mt-5 text-sm text-slate-600">Loading booking details...</p>
        ) : null}

        {pageError ? (
          <div className="mt-5 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {pageError}
          </div>
        ) : null}

        {booking ? (
          <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            <p className="font-semibold text-slate-900">Current booking</p>
            <p className="mt-1">{booking.event_title}</p>
            <p>{booking.invitee_start_time} - {booking.invitee_end_time} ({booking.invitee_zone})</p>
            <p className="text-slate-500">Organizer time: {booking.organizer_start_time} - {booking.organizer_end_time}</p>
          </div>
        ) : null}

        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <div>
            <label htmlFor="new-date" className="mb-2 block text-sm font-medium text-slate-700">
              New date
            </label>
            <input
              id="new-date"
              type="date"
              min={minDate}
              value={selectedDate}
              onChange={(event) => setSelectedDate(event.target.value)}
              className="w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white"
              disabled={!canReschedule || isLoadingSlots}
            />
          </div>

          <div>
            <p className="mb-2 block text-sm font-medium text-slate-700">Available slots</p>
            {isLoadingSlots ? (
              <p className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-500">Loading slots...</p>
            ) : null}

            {slotError ? (
              <p className="rounded-xl bg-rose-50 px-3 py-2.5 text-sm text-rose-700">{slotError}</p>
            ) : null}

            {!isLoadingSlots && !slotError ? (
              slots.length > 0 ? (
                <div className="grid gap-2 sm:grid-cols-2">
                  {slots.map((slot) => (
                    <button
                      key={slot.start}
                      type="button"
                      onClick={() => setSelectedSlotStart(slot.start)}
                      className={`rounded-xl border px-3 py-2 text-left text-sm transition ${
                        selectedSlotStart === slot.start
                          ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                          : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
                      }`}
                    >
                      {slotLabel(slot)}
                    </button>
                  ))}
                </div>
              ) : (
                <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-500">
                  No slots available for this date.
                </p>
              )
            ) : null}
          </div>

          {result ? (
            <div className={`rounded-xl px-4 py-3 text-sm ${result.ok ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}>
              {result.message}
            </div>
          ) : null}

          <button
            type="submit"
            disabled={isSubmitting || !selectedSlotStart || !canReschedule}
            className="inline-flex w-full items-center justify-center rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {isSubmitting ? "Rescheduling..." : "Confirm Reschedule"}
          </button>
        </form>
      </section>
    </main>
  );
}
