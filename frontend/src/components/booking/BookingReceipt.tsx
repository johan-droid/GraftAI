"use client";

import { useMemo } from "react";
import BookingStatusPill from "@/components/ui/BookingStatusPill";

interface BookingReceiptProps {
  bookingId: string;
  fullName: string;
  email: string;
  eventTitle: string;
  organizerName: string;
  organizerStartTime: string;
  organizerEndTime: string;
  inviteeStartTime: string;
  inviteeEndTime: string;
  inviteeZone: string;
  meetingUrl?: string;
  confirmationEmail?: string;
  rescheduleUrl?: string;
  cancelUrl?: string;
}

function makeIcs(booking: BookingReceiptProps) {
  const title = `Booking with ${booking.organizerName}`;
  const start = booking.organizerStartTime.replace(/[-:]/g, "").replace(/ /g, "T");
  const end = booking.organizerEndTime.replace(/[-:]/g, "").replace(/ /g, "T");

  return [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//GraftAI//EN",
    "CALSCALE:GREGORIAN",
    "BEGIN:VEVENT",
    `UID:${booking.bookingId}@graftai.tech`,
    `SUMMARY:${title}`,
    `DTSTART:${start}`,
    `DTEND:${end}`,
    `DESCRIPTION:Booking with ${booking.organizerName} (${booking.eventTitle})\\nAttendee: ${booking.fullName} <${booking.email}>`,
    booking.meetingUrl ? `URL:${booking.meetingUrl}` : "",
    "END:VEVENT",
    "END:VCALENDAR",
  ]
    .filter(Boolean)
    .join("\r\n");
}

export default function BookingReceipt(props: BookingReceiptProps) {
  const icsHref = useMemo(() => {
    const ics = makeIcs(props);
    const blob = new Blob([ics], { type: "text/calendar;charset=utf-8" });
    return URL.createObjectURL(blob);
  }, [props]);

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.25em] text-indigo-600">Booking Receipt</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-900">{props.eventTitle}</h2>
            <p className="mt-1 text-sm text-slate-600">Confirmed for {props.inviteeStartTime} — {props.inviteeEndTime} ({props.inviteeZone})</p>
          </div>
          <BookingStatusPill status="confirmed" />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Organizer</p>
            <p className="mt-2 font-semibold text-slate-900">{props.organizerName}</p>
          </div>
          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Confirmation sent to</p>
            <p className="mt-2 font-semibold text-slate-900">{props.confirmationEmail || props.email}</p>
          </div>
        </div>

        {props.meetingUrl ? (
          <div className="rounded-2xl bg-emerald-50 p-4 text-sm text-emerald-900">
            Meeting link: <a href={props.meetingUrl} className="font-semibold underline" target="_blank" rel="noreferrer">Join</a>
          </div>
        ) : null}

        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          <a
            href={icsHref}
            download={`graftai-booking-${props.bookingId}.ics`}
            className="inline-flex w-full items-center justify-center rounded-2xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-200 sm:w-auto"
          >
            Download .ics
          </a>
          <a
            href="https://calendar.google.com/calendar/r/eventedit"
            target="_blank"
            rel="noreferrer noopener"
            className="inline-flex w-full items-center justify-center rounded-2xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 sm:w-auto"
          >
            Add to Google Calendar
          </a>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {props.rescheduleUrl ? (
            <a
              href={props.rescheduleUrl}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-indigo-700 transition hover:bg-slate-50"
            >
              Reschedule booking
            </a>
          ) : null}
          {props.cancelUrl ? (
            <a
              href={props.cancelUrl}
              className="rounded-2xl border border-rose-200 bg-white px-4 py-3 text-sm font-semibold text-rose-700 transition hover:bg-rose-50"
            >
              Cancel booking
            </a>
          ) : null}
        </div>
      </div>
    </div>
  );
}
