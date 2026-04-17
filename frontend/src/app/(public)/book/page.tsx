"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Clock, Video, Globe, Calendar as CalendarIcon,
  ArrowLeft, User, Mail, MessageSquare, CheckCircle2, Loader2
} from "lucide-react";
import Link from "next/link";
import {
  bookPublicEvent,
  confirmPublicPaymentIntent,
  createPublicPaymentIntent,
  getPublicEventDetails,
  type PublicBookingConfirmation,
  type PublicEventDetailsResponse,
} from "@/lib/api";

type CustomQuestionDefinition = {
  id?: string;
  question?: string;
  type?: string;
  required?: boolean;
  options?: Array<string | { label?: string; value?: string }>;
};

function formatDateLabel(dateParam: string | null) {
  if (!dateParam) return "No date selected";

  const parsed = new Date(`${dateParam}T12:00:00`);
  if (Number.isNaN(parsed.getTime())) return "No date selected";

  return parsed.toLocaleDateString("default", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}

function parseSelectedStart(dateParam: string | null, timeParam: string | null) {
  if (!timeParam) return null;

  const fullMatch = timeParam.match(/^(\d{4}-\d{2}-\d{2})\s+(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
  if (fullMatch) {
    const [, dateValue, hourRaw, minuteRaw, meridiemRaw] = fullMatch;
    const [year, month, day] = dateValue.split("-").map(Number);
    let hour = Number(hourRaw);
    const minute = Number(minuteRaw);
    const meridiem = meridiemRaw.toUpperCase();

    if (meridiem === "PM" && hour !== 12) hour += 12;
    if (meridiem === "AM" && hour === 12) hour = 0;

    return new Date(year, month - 1, day, hour, minute, 0, 0);
  }

  const timeOnlyMatch = timeParam.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
  if (timeOnlyMatch && dateParam) {
    const [, hourRaw, minuteRaw, meridiemRaw] = timeOnlyMatch;
    const [year, month, day] = dateParam.split("-").map(Number);
    let hour = Number(hourRaw);
    const minute = Number(minuteRaw);
    const meridiem = meridiemRaw.toUpperCase();

    if (meridiem === "PM" && hour !== 12) hour += 12;
    if (meridiem === "AM" && hour === 12) hour = 0;

    return new Date(year, month - 1, day, hour, minute, 0, 0);
  }

  return null;
}

function formatTimeWindowLabel(timeParam: string | null, eventDetails: PublicEventDetailsResponse | null) {
  if (timeParam) return timeParam;
  if (eventDetails) return `${eventDetails.duration_minutes} minute meeting`;
  return "Selected time";
}

function BookingForm() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const username = searchParams.get("username");
  const eventType = searchParams.get("event_type");
  const dateParam = searchParams.get("date");
  const timeParam = searchParams.get("time");

  const [browserTimezone, setBrowserTimezone] = useState<string>("");
  const [eventDetails, setEventDetails] = useState<PublicEventDetailsResponse | null>(null);
  const [isLoadingDetails, setIsLoadingDetails] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [bookingResult, setBookingResult] = useState<PublicBookingConfirmation | null>(null);
  const [customAnswers, setCustomAnswers] = useState<Record<string, string | boolean>>({});
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    notes: "",
  });

  const formattedDate = formatDateLabel(dateParam);
  const selectedStart = parseSelectedStart(dateParam, timeParam);
  const selectedEnd = selectedStart && eventDetails
    ? new Date(selectedStart.getTime() + eventDetails.duration_minutes * 60000)
    : null;
  const customQuestions = (eventDetails?.custom_questions ?? []) as CustomQuestionDefinition[];

  useEffect(() => {
    setBrowserTimezone(Intl.DateTimeFormat().resolvedOptions().timeZone);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadEventDetails() {
      if (!username || !eventType) {
        setLoadError("Missing booking details in the link.");
        setIsLoadingDetails(false);
        return;
      }

      try {
        setIsLoadingDetails(true);
        setLoadError(null);
        const details = await getPublicEventDetails(username, eventType);
        if (!cancelled) {
          setEventDetails(details);
          const defaultAnswers: Record<string, string | boolean> = {};
          for (const question of (details.custom_questions ?? []) as CustomQuestionDefinition[]) {
            const questionId = question.id?.trim();
            if (!questionId) {
              continue;
            }
            if ((question.type ?? "text").toLowerCase() === "checkbox") {
              defaultAnswers[questionId] = false;
            } else {
              defaultAnswers[questionId] = "";
            }
          }
          setCustomAnswers(defaultAnswers);
        }
      } catch (error) {
        if (!cancelled) {
          setLoadError(error instanceof Error ? error.message : "Unable to load booking details.");
        }
      } finally {
        if (!cancelled) {
          setIsLoadingDetails(false);
        }
      }
    }

    void loadEventDetails();

    return () => {
      cancelled = true;
    };
  }, [eventType, username]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !eventType) {
      setLoadError("Missing booking details in the link.");
      return;
    }

    if (!eventDetails) {
      setLoadError("Booking details are still loading.");
      return;
    }

    if (!selectedStart || !selectedEnd) {
      setLoadError("Unable to parse the selected time. Please go back and choose another slot.");
      return;
    }

    setIsSubmitting(true);
    setLoadError(null);

    try {
      if (eventDetails.requires_payment) {
        const paymentIntent = await createPublicPaymentIntent(username, eventType);
        await confirmPublicPaymentIntent(username, eventType, {
          payment_intent_id: paymentIntent.payment_intent_id,
          payment_method: "simulated_card",
        });
      }

      const booking = await bookPublicEvent(username, eventType, {
        full_name: formData.name.trim(),
        email: formData.email.trim(),
        start_time: selectedStart.toISOString(),
        end_time: selectedEnd.toISOString(),
        time_zone: browserTimezone,
        questions: {
          ...customAnswers,
          ...(formData.notes.trim() ? { notes: formData.notes.trim() } : {}),
        },
        metadata: {
          source: "public-book-page",
          date_param: dateParam,
          time_param: timeParam,
          payment_verified: !eventDetails.requires_payment ? undefined : true,
          payment_status: eventDetails.requires_payment ? "paid" : undefined,
        },
      });

      setBookingResult(booking);
      setIsSuccess(true);
    } catch {
      setLoadError("We could not complete the booking. Please try again.");
    }

    setIsSubmitting(false);
  };

  if (isLoadingDetails) {
    return (
      <div className="w-full min-h-[500px] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-[#1A73E8] animate-spin" />
      </div>
    );
  }

  if (loadError && !eventDetails) {
    return (
      <div className="w-full min-h-[500px] flex items-center justify-center px-4">
        <div className="max-w-lg w-full rounded-3xl border border-[#DADCE0] bg-white p-8 text-center shadow-sm">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#FCE8E6] text-[#D93025]">
            <CheckCircle2 className="h-7 w-7" />
          </div>
          <h1 className="text-2xl font-semibold text-[#202124]">Booking details unavailable</h1>
          <p className="mt-3 text-sm leading-relaxed text-[#5F6368]">{loadError}</p>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <button
              type="button"
              onClick={() => router.back()}
              className="inline-flex items-center justify-center rounded-full border border-[#DADCE0] px-5 py-2.5 text-sm font-medium text-[#202124] transition-colors hover:bg-[#F8F9FA]"
            >
              Go back
            </button>
            <Link
              href="/"
              className="inline-flex items-center justify-center rounded-full bg-[#1A73E8] px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#1557B0]"
            >
              Return home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (isSuccess) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white border border-[#DADCE0] rounded-3xl shadow-sm p-10 md:p-16 text-center max-w-2xl mx-auto w-full"
      >
        <div className="w-20 h-20 bg-[#E6F4EA] rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle2 className="w-10 h-10 text-[#137333]" />
        </div>
        <h1 className="text-3xl font-semibold text-[#202124] tracking-tight mb-4">
          You are scheduled!
        </h1>
        <p className="text-base text-[#5F6368] mb-8 leading-relaxed max-w-md mx-auto">
          A calendar invitation has been sent to your email address. If you need to reschedule or cancel, you can use the link in the email.
        </p>

        <div className="bg-[#F8F9FA] border border-[#DADCE0] rounded-2xl p-6 text-left max-w-sm mx-auto mb-8">
          <h3 className="font-semibold text-[#202124] mb-4">{eventDetails?.title ?? "Your booking"}</h3>
          <div className="space-y-3 text-sm text-[#5F6368]">
            <div className="flex items-center gap-3">
              <CalendarIcon size={18} className="text-[#1A73E8]" />
              {formattedDate}
            </div>
            <div className="flex items-center gap-3">
              <Clock size={18} className="text-[#1A73E8]" />
              {formatTimeWindowLabel(timeParam, eventDetails)}
            </div>
            <div className="flex items-center gap-3">
              <Video size={18} className="text-[#137333]" />
              {eventDetails?.meeting_provider || "Video meeting"}
            </div>
          </div>
        </div>

        {bookingResult?.meeting_url ? (
          <a href={bookingResult.meeting_url} className="mb-6 inline-flex text-sm font-medium text-[#1A73E8] hover:underline" target="_blank" rel="noreferrer">
            Open meeting link
          </a>
        ) : null}

        {bookingResult?.manage_url ? (
          <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <a href={bookingResult.manage_url} className="inline-flex items-center justify-center rounded-full border border-[#DADCE0] px-5 py-2.5 text-sm font-medium text-[#202124] transition-colors hover:bg-[#F8F9FA]">
              Manage booking
            </a>
            <a href={bookingResult.reschedule_url ?? bookingResult.manage_url} className="inline-flex items-center justify-center rounded-full bg-[#1A73E8] px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#1557B0]">
              Reschedule
            </a>
          </div>
        ) : null}

        <Link href="/" className="text-sm font-medium text-[#1A73E8] hover:underline">
          Return to home
        </Link>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border border-[#DADCE0] rounded-3xl shadow-sm overflow-hidden flex flex-col md:flex-row w-full"
    >
      <div className="w-full md:w-[40%] bg-[#F8F9FA] p-8 md:p-10 border-b md:border-b-0 md:border-r border-[#DADCE0] flex flex-col">
        <button
          type="button"
          aria-label="Go back"
          title="Go back"
          onClick={() => router.back()}
          className="w-10 h-10 rounded-full flex items-center justify-center bg-white border border-[#DADCE0] text-[#5F6368] hover:text-[#202124] hover:bg-[#F1F3F4] transition-colors mb-8 shadow-sm"
        >
          <ArrowLeft size={20} />
        </button>

        <p className="text-sm font-semibold text-[#5F6368] uppercase tracking-wider mb-1">
          {eventDetails?.username ?? username ?? "Host"}
        </p>
        <h2 className="text-2xl font-semibold text-[#202124] tracking-tight mb-6">
          {eventDetails?.title ?? "Booking details"}
        </h2>

        <div className="space-y-4 text-[15px] font-medium text-[#5F6368] bg-white border border-[#DADCE0] p-5 rounded-2xl shadow-sm">
          <div className="flex items-start gap-3">
            <CalendarIcon size={20} className="text-[#1A73E8] shrink-0 mt-0.5" />
            <span className="leading-snug">
              {formattedDate}
              <br />
              {formatTimeWindowLabel(timeParam, eventDetails)}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <Globe size={20} className="text-[#E37400] shrink-0" />
            {eventDetails?.timezone ?? browserTimezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone}
          </div>
          <div className="flex items-center gap-3">
            <Video size={20} className="text-[#137333] shrink-0" />
            {eventDetails?.meeting_provider || "Video meeting"}
          </div>
        </div>
      </div>

      <div className="w-full md:w-[60%] p-8 md:p-10">
        <h2 className="text-xl font-semibold text-[#202124] mb-6">Enter Details</h2>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-2 flex items-center gap-2">
              <User size={14} /> Full Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full bg-[#F8F9FA] border border-[#DADCE0] rounded-xl px-4 py-3 text-[#202124] focus:outline-none focus:ring-2 focus:ring-[#1A73E8]/20 focus:border-[#1A73E8] transition-all placeholder:text-[#9AA0A6]"
              placeholder="e.g. Jane Doe"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-2 flex items-center gap-2">
              <Mail size={14} /> Email Address *
            </label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full bg-[#F8F9FA] border border-[#DADCE0] rounded-xl px-4 py-3 text-[#202124] focus:outline-none focus:ring-2 focus:ring-[#1A73E8]/20 focus:border-[#1A73E8] transition-all placeholder:text-[#9AA0A6]"
              placeholder="jane@company.com"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-2 flex items-center gap-2">
              <MessageSquare size={14} /> Additional Notes
            </label>
            <textarea
              rows={3}
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full bg-[#F8F9FA] border border-[#DADCE0] rounded-xl px-4 py-3 text-[#202124] focus:outline-none focus:ring-2 focus:ring-[#1A73E8]/20 focus:border-[#1A73E8] transition-all resize-none placeholder:text-[#9AA0A6]"
              placeholder="Please share anything that will help prepare for our meeting..."
            />
          </div>

          {customQuestions.length > 0 ? (
            <div className="space-y-4 rounded-2xl border border-[#DADCE0] bg-[#F8F9FA] p-4 sm:p-5">
              <div>
                <p className="text-sm font-semibold text-[#202124]">Custom questions</p>
                <p className="text-xs text-[#5F6368]">Please answer the organizer's questions to finish booking.</p>
              </div>

              {customQuestions.map((question, index) => {
                const questionId = question.id?.trim() || `question-${index}`;
                const questionLabel = question.question?.trim() || `Question ${index + 1}`;
                const questionType = (question.type ?? "text").toLowerCase();
                const isRequired = Boolean(question.required);

                if (questionType === "checkbox") {
                  return (
                    <label key={questionId} className="flex items-start gap-3 rounded-xl border border-[#DADCE0] bg-white px-4 py-3 text-sm text-[#202124]">
                      <input
                        type="checkbox"
                        checked={Boolean(customAnswers[questionId])}
                        onChange={(event) => setCustomAnswers((prev) => ({ ...prev, [questionId]: event.target.checked }))}
                        className="mt-1 h-4 w-4 rounded border-[#DADCE0] text-[#1A73E8] focus:ring-[#1A73E8]"
                      />
                      <span>
                        {questionLabel}
                        {isRequired ? <span className="ml-1 text-[#D93025]">*</span> : null}
                      </span>
                    </label>
                  );
                }

                if (questionType === "textarea") {
                  return (
                    <div key={questionId}>
                      <label className="block text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-2">
                        {questionLabel}
                        {isRequired ? <span className="ml-1 text-[#D93025]">*</span> : null}
                      </label>
                      <textarea
                        rows={3}
                        required={isRequired}
                        aria-label={questionLabel}
                        title={questionLabel}
                        placeholder={questionLabel}
                        value={String(customAnswers[questionId] ?? "")}
                        onChange={(event) => setCustomAnswers((prev) => ({ ...prev, [questionId]: event.target.value }))}
                        className="w-full bg-white border border-[#DADCE0] rounded-xl px-4 py-3 text-[#202124] focus:outline-none focus:ring-2 focus:ring-[#1A73E8]/20 focus:border-[#1A73E8] transition-all resize-none placeholder:text-[#9AA0A6]"
                      />
                    </div>
                  );
                }

                if (questionType === "select") {
                  const options = question.options ?? [];
                  return (
                    <div key={questionId}>
                      <label className="block text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-2">
                        {questionLabel}
                        {isRequired ? <span className="ml-1 text-[#D93025]">*</span> : null}
                      </label>
                      <select
                        required={isRequired}
                        aria-label={questionLabel}
                        title={questionLabel}
                        value={String(customAnswers[questionId] ?? "")}
                        onChange={(event) => setCustomAnswers((prev) => ({ ...prev, [questionId]: event.target.value }))}
                        className="w-full bg-white border border-[#DADCE0] rounded-xl px-4 py-3 text-[#202124] focus:outline-none focus:ring-2 focus:ring-[#1A73E8]/20 focus:border-[#1A73E8] transition-all"
                      >
                        <option value="">Select an option</option>
                        {options.map((option) => {
                          const optionValue = typeof option === "string" ? option : option.value ?? option.label ?? "";
                          const optionLabel = typeof option === "string" ? option : option.label ?? option.value ?? "Option";
                          return (
                            <option key={optionValue || optionLabel} value={optionValue}>
                              {optionLabel}
                            </option>
                          );
                        })}
                      </select>
                    </div>
                  );
                }

                return (
                  <div key={questionId}>
                    <label className="block text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-2">
                      {questionLabel}
                      {isRequired ? <span className="ml-1 text-[#D93025]">*</span> : null}
                    </label>
                    <input
                      type="text"
                      required={isRequired}
                      aria-label={questionLabel}
                      title={questionLabel}
                      placeholder={questionLabel}
                      value={String(customAnswers[questionId] ?? "")}
                      onChange={(event) => setCustomAnswers((prev) => ({ ...prev, [questionId]: event.target.value }))}
                      className="w-full bg-white border border-[#DADCE0] rounded-xl px-4 py-3 text-[#202124] focus:outline-none focus:ring-2 focus:ring-[#1A73E8]/20 focus:border-[#1A73E8] transition-all placeholder:text-[#9AA0A6]"
                    />
                  </div>
                );
              })}
            </div>
          ) : null}

          <div className="pt-4 mt-6 border-t border-[#F1F3F4]">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full sm:w-auto flex items-center justify-center gap-2 text-sm font-medium bg-[#1A73E8] text-white hover:bg-[#1557B0] px-8 py-3.5 rounded-full transition-colors shadow-sm disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <><Loader2 size={18} className="animate-spin" /> Scheduling...</>
              ) : (
                eventDetails?.requires_payment ? "Confirm and schedule" : "Schedule Event"
              )}
            </button>
          </div>

          {eventDetails?.requires_payment ? (
            <div className="rounded-2xl border border-[#DADCE0] bg-[#FEF7E0] px-4 py-3 text-sm text-[#8A5A00]">
              This event requires payment. We will confirm the payment before finalizing your booking.
            </div>
          ) : null}

          {loadError ? (
            <div className="rounded-2xl border border-[#FCE8E6] bg-[#FCE8E6] px-4 py-3 text-sm text-[#B3261E]">
              {loadError}
            </div>
          ) : null}
        </form>
      </div>
    </motion.div>
  );
}

export default function BookPage() {
  return (
    <Suspense
      fallback={
        <div className="w-full min-h-[500px] flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-[#1A73E8] animate-spin" />
        </div>
      }
    >
      <BookingForm />
    </Suspense>
  );
}
