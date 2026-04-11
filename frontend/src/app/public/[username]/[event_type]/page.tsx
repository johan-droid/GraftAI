"use client";

import { useEffect, useMemo, useState } from "react";
import {
  bookPublicEvent,
  confirmPublicPaymentIntent,
  createPublicPaymentIntent,
  getPublicEventAvailability,
  getPublicEventDetails,
  PublicAvailabilityResponse,
  PublicBookingConfirmation,
  PublicEventDetailsResponse,
} from "@/lib/api";
import BookingReceipt from "@/components/booking/BookingReceipt";

function pad(value: number) {
  return String(value).padStart(2, "0");
}

function formatLocalDateTime(date: Date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}:00`;
}

function parseInviteeSlot(slotLabel: string) {
  const [datePart, timePart, ampm] = slotLabel.split(" ");
  if (!datePart || !timePart || !ampm) {
    return null;
  }

  const [year, month, day] = datePart.split("-").map(Number);
  const [hourRaw, minute] = timePart.split(":").map(Number);
  let hour = hourRaw;
  if (ampm === "PM" && hour !== 12) hour += 12;
  if (ampm === "AM" && hour === 12) hour = 0;

  return new Date(year, month - 1, day, hour, minute, 0, 0);
}

export default function PublicBookingPage({ params }: { params: { username: string; event_type: string } }) {
  const [browserTimezone, setBrowserTimezone] = useState<string>("");
  const [eventDetails, setEventDetails] = useState<PublicEventDetailsResponse | null>(null);
  const [availability, setAvailability] = useState<PublicAvailabilityResponse | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [selectedSlot, setSelectedSlot] = useState<string>("");
  const [fullName, setFullName] = useState<string>("");
  const [email, setEmail] = useState<string>("");
  const [questionAnswers, setQuestionAnswers] = useState<Record<string, string | boolean>>({});
  const [paymentIntent, setPaymentIntent] = useState<{ payment_intent_id: string; amount: number; currency: string; status: string; client_secret?: string } | null>(null);
  const [paymentConfirmed, setPaymentConfirmed] = useState<boolean>(false);
  const [paymentLoading, setPaymentLoading] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [submissionState, setSubmissionState] = useState<{ success: boolean; message: string } | null>(null);
  const [bookingResult, setBookingResult] = useState<PublicBookingConfirmation | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>("");

  const currentMonth = useMemo(() => {
    const now = new Date();
    return `${now.getFullYear()}-${pad(now.getMonth() + 1)}`;
  }, []);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      setBrowserTimezone(tz || "UTC");
    }
  }, []);

  useEffect(() => {
    if (!browserTimezone) {
      return;
    }

    setLoading(true);
    setErrorMessage("");

    Promise.all([
      getPublicEventDetails(params.username, params.event_type),
      getPublicEventAvailability(params.username, params.event_type, currentMonth, browserTimezone),
    ])
      .then(([eventData, availabilityData]) => {
        setEventDetails(eventData);
        setAvailability(availabilityData);

        const firstAvailableDate = Object.keys(availabilityData.availability).find(
          (date) => availabilityData.availability[date]?.length > 0
        );

        setSelectedDate(firstAvailableDate || "");
        setSelectedSlot(
          firstAvailableDate ? availabilityData.availability[firstAvailableDate][0] : ""
        );
      })
      .catch((error) => {
        setErrorMessage(error instanceof Error ? error.message : "Unable to load booking availability.");
      })
      .finally(() => setLoading(false));
  }, [browserTimezone, params.username, params.event_type, currentMonth]);

  const availableDates = useMemo(() => {
    if (!availability) return [];
    return Object.entries(availability.availability || {})
      .filter(([, slots]) => slots.length > 0)
      .sort(([a], [b]) => a.localeCompare(b));
  }, [availability]);

  const selectedSlots = selectedDate ? availability?.availability[selectedDate] || [] : [];

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmissionState(null);
    setErrorMessage("");

    if (!selectedSlot) {
      setErrorMessage("Please choose a slot before booking.");
      return;
    }

    const slotDate = parseInviteeSlot(selectedSlot);
    if (!slotDate || !eventDetails) {
      setErrorMessage("Unable to parse the selected slot. Please choose another slot.");
      return;
    }

    const startTime = formatLocalDateTime(slotDate);
    const bookingEnd = new Date(slotDate.getTime() + eventDetails.duration_minutes * 60 * 1000);
    const endTime = formatLocalDateTime(bookingEnd);

    setLoading(true);

    try {
      const payload: Record<string, unknown> = {
        full_name: fullName,
        email,
        start_time: startTime,
        end_time: endTime,
        time_zone: browserTimezone,
      };

      if (Object.keys(questionAnswers).length > 0) {
        payload.questions = questionAnswers;
      }

      if (eventDetails?.requires_payment) {
        if (!paymentConfirmed) {
          throw new Error("Please confirm payment before booking this paid event.");
        }
        payload.metadata = {
          payment_status: "paid",
          payment_verified: true,
        };
      }

      const bookingResponse = await bookPublicEvent(params.username, params.event_type, payload);

      setBookingResult(bookingResponse);
      setSubmissionState({ success: true, message: "Booking confirmed!" });
    } catch (error) {
      setSubmissionState({ success: false, message: error instanceof Error ? error.message : "Booking failed." });
    } finally {
      setLoading(false);
    }
  };

  async function createPaymentIntent() {
    if (!eventDetails || !eventDetails.requires_payment) return;
    setPaymentLoading(true);
    try {
      const intent = await createPublicPaymentIntent(params.username, params.event_type);
      setPaymentIntent(intent);
      setPaymentConfirmed(false);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to create payment intent.");
    } finally {
      setPaymentLoading(false);
    }
  }

  async function confirmPaymentIntent() {
    if (!eventDetails || !paymentIntent) return;
    setPaymentLoading(true);
    try {
      const confirmation = await confirmPublicPaymentIntent(params.username, params.event_type, {
        payment_intent_id: paymentIntent.payment_intent_id,
        payment_method: "simulated_card",
      });
      if (confirmation.success && confirmation.payment_status === "paid") {
        setPaymentConfirmed(true);
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Payment confirmation failed.");
    } finally {
      setPaymentLoading(false);
    }
  }

  if (loading && !eventDetails) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 py-10">
        <div className="max-w-lg w-full text-center">
          <p className="text-slate-500">Loading public booking details...</p>
        </div>
      </div>
    );
  }

  if (errorMessage && !eventDetails) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 py-10">
        <div className="max-w-lg w-full rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <h1 className="text-xl font-semibold text-slate-900">Booking unavailable</h1>
          <p className="mt-4 text-slate-600">{errorMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl space-y-8">
        <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <div className="space-y-3">
            <p className="text-sm uppercase tracking-[0.25em] text-indigo-600">Public Booking</p>
            <h1 className="text-3xl font-semibold text-slate-900">{eventDetails?.title?.trim() || "Booking"}</h1>
            {eventDetails?.description ? (
              <p className="text-slate-600">{eventDetails.description}</p>
            ) : null}
            <div className="flex flex-col gap-2 text-sm text-slate-500 sm:flex-row sm:items-center">
              <span>Organizer timezone: <strong>{eventDetails?.timezone || "UTC"}</strong></span>
              <span>Visitor timezone: <strong>{browserTimezone || "UTC"}</strong></span>
            </div>
          </div>
        </div>

        <div className="grid gap-8 lg:grid-cols-[1.4fr_0.8fr]">
          <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
            <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.25em] text-slate-500">Available slots</p>
                <h2 className="text-xl font-semibold text-slate-900">{currentMonth}</h2>
              </div>
              <div className="text-sm text-slate-500">
                Showing slots in your current browser timezone.
              </div>
            </div>

            {availableDates.length === 0 ? (
              <div className="rounded-3xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center text-slate-500">
                No slots are available this month. Please check back later.
              </div>
            ) : (
              <div className="space-y-6">
                <div className="grid gap-3 sm:grid-cols-2">
                  {availableDates.map(([date]) => (
                    <button
                      key={date}
                      type="button"
                      onClick={() => {
                        setSelectedDate(date);
                        const defaultSlot = availability?.availability[date]?.[0] || "";
                        setSelectedSlot(defaultSlot);
                      }}
                      className={`rounded-2xl border px-4 py-3 text-left transition ${
                        date === selectedDate
                          ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                          : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
                      }`}
                    >
                      <p className="font-semibold">{date}</p>
                      <p className="text-sm text-slate-500">{availability?.availability[date]?.length ?? 0} slot(s)</p>
                    </button>
                  ))}
                </div>

                {selectedDate ? (
                  <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
                    <h3 className="text-lg font-semibold text-slate-900">Slots on {selectedDate}</h3>
                    <div className="mt-4 grid gap-3 sm:grid-cols-2">
                      {selectedSlots.map((slot) => (
                        <button
                          key={slot}
                          type="button"
                          onClick={() => setSelectedSlot(slot)}
                          className={`rounded-2xl border px-4 py-3 text-left transition ${
                            slot === selectedSlot
                              ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                              : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
                          }`}
                        >
                          <span className="block text-base font-medium">{slot}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            )}
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">Book this slot</h2>
            <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="booking-full-name" className="mb-2 block text-sm font-medium text-slate-700">Full name</label>
                <input
                  id="booking-full-name"
                  type="text"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  className="w-full rounded-2xl border border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white"
                  required
                />
              </div>

              <div>
                <label htmlFor="booking-email" className="mb-2 block text-sm font-medium text-slate-700">Email address</label>
                <input
                  id="booking-email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="w-full rounded-2xl border border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white"
                  required
                />
              </div>

              <div className="space-y-2 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                <p><strong>Selected slot</strong></p>
                <p>{selectedSlot || "Choose a date and slot above."}</p>
                {eventDetails?.duration_minutes ? (
                  <p>Duration: {eventDetails.duration_minutes} minutes</p>
                ) : null}
                {eventDetails?.requires_attendee_confirmation ? (
                  <p className="text-slate-700">This booking requires organizer confirmation and will be marked pending until approved.</p>
                ) : null}
                {eventDetails?.requires_payment ? (
                  <p className="text-slate-700">Payment required: {eventDetails.payment_amount?.toFixed(2)} {eventDetails.payment_currency || "USD"}</p>
                ) : null}
                {eventDetails?.custom_questions && eventDetails.custom_questions.length > 0 ? (
                  <p className="text-slate-700">Additional questions are required for this booking.</p>
                ) : null}
              </div>

              {eventDetails?.custom_questions && eventDetails.custom_questions.length > 0 ? (
                <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
                  <h3 className="text-lg font-semibold text-slate-900">Additional questions</h3>
                  <div className="mt-4 space-y-4">
                    {eventDetails.custom_questions.map((question, index) => {
                      const questionId = String(question.id || question.question || `question-${index}`);
                      const questionLabel = String(question.question || questionId);
                      const questionType = String((question.type || "text")).toLowerCase();
                      const required = Boolean(question.required);
                      const answer = questionAnswers[questionId] ?? "";

                      return (
                        <div key={questionId} className="space-y-2">
                          <label className="block text-sm font-medium text-slate-700" htmlFor={questionId}>
                            {questionLabel}{required ? " *" : ""}
                          </label>
                          {questionType === "textarea" ? (
                            <textarea
                              id={questionId}
                              value={String(answer)}
                              onChange={(event) => setQuestionAnswers({ ...questionAnswers, [questionId]: event.target.value })}
                              rows={4}
                              className="w-full rounded-2xl border border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white"
                              required={required}
                            />
                          ) : questionType === "checkbox" ? (
                            <label className="inline-flex items-center gap-3 text-sm text-slate-700">
                              <input
                                id={questionId}
                                type="checkbox"
                                checked={Boolean(answer)}
                                onChange={(event) => setQuestionAnswers({ ...questionAnswers, [questionId]: event.target.checked })}
                                className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                              />
                              {questionLabel}
                            </label>
                          ) : questionType === "select" && Array.isArray(question.options) ? (
                            <select
                              id={questionId}
                              value={String(answer)}
                              onChange={(event) => setQuestionAnswers({ ...questionAnswers, [questionId]: event.target.value })}
                              className="w-full rounded-2xl border border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white"
                              required={required}
                            >
                              <option value="">Select an answer</option>
                              {question.options.map((option: any) => (
                                <option key={String(option)} value={String(option)}>{String(option)}</option>
                              ))}
                            </select>
                          ) : (
                            <input
                              id={questionId}
                              type="text"
                              value={String(answer)}
                              onChange={(event) => setQuestionAnswers({ ...questionAnswers, [questionId]: event.target.value })}
                              className="w-full rounded-2xl border border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white"
                              required={required}
                            />
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : null}

              {eventDetails?.requires_payment ? (
                <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
                  <h3 className="text-lg font-semibold text-slate-900">Payment</h3>
                  <p className="mt-3 text-sm text-slate-600">
                    This event requires payment before booking can complete. Use the checkout flow below.
                  </p>

                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700">
                      <p className="font-medium">Amount</p>
                      <p>{eventDetails.payment_amount?.toFixed(2) ?? "0.00"} {eventDetails.payment_currency || "USD"}</p>
                    </div>
                    <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700">
                      <p className="font-medium">Status</p>
                      <p>{paymentConfirmed ? "Paid" : paymentIntent ? "Ready to confirm" : "Pending"}</p>
                    </div>
                  </div>

                  {!paymentIntent ? (
                    <button
                      type="button"
                      onClick={createPaymentIntent}
                      disabled={paymentLoading}
                      className="mt-5 inline-flex w-full items-center justify-center rounded-2xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                    >
                      {paymentLoading ? "Initializing payment..." : "Start checkout"}
                    </button>
                  ) : !paymentConfirmed ? (
                    <div className="space-y-3 mt-5">
                      <p className="text-sm text-slate-600">Payment intent created: {paymentIntent.payment_intent_id}</p>
                      <button
                        type="button"
                        onClick={confirmPaymentIntent}
                        disabled={paymentLoading}
                        className="inline-flex w-full items-center justify-center rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                      >
                        {paymentLoading ? "Confirming payment..." : "Confirm payment"}
                      </button>
                    </div>
                  ) : (
                    <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
                      Payment confirmed, you may submit the booking.
                    </div>
                  )}
                </div>
              ) : null}

              {submissionState ? (
                <div className={`rounded-2xl px-4 py-3 text-sm ${submissionState.success ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}>
                  {submissionState.message}
                </div>
              ) : null}

              {bookingResult ? (
                <BookingReceipt
                  bookingId={bookingResult.booking_id}
                  fullName={fullName}
                  email={email}
                  eventTitle={eventDetails?.title || "Booking"}
                  organizerName={eventDetails?.username || "Organizer"}
                  organizerStartTime={bookingResult.organizer_start_time}
                  organizerEndTime={bookingResult.organizer_end_time}
                  inviteeStartTime={bookingResult.invitee_start_time}
                  inviteeEndTime={bookingResult.invitee_end_time}
                  inviteeZone={bookingResult.invitee_zone}
                  meetingUrl={bookingResult.meeting_url ?? undefined}
                  confirmationEmail={email}
                  rescheduleUrl={bookingResult.reschedule_url ?? undefined}
                  cancelUrl={bookingResult.cancel_url ?? undefined}
                />
              ) : null}

              {errorMessage && bookingResult === null ? (
                <p className="text-sm text-rose-600">{errorMessage}</p>
              ) : null}

              <button
                type="submit"
                disabled={!selectedSlot || loading || (eventDetails?.requires_payment && !paymentConfirmed)}
                className="inline-flex w-full items-center justify-center rounded-2xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                {loading ? "Booking..." : "Confirm booking"}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
