"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

interface CancellationModalProps {
  isOpen: boolean;
  isSubmitting: boolean;
  onClose: () => void;
  onConfirm: (reason?: string) => void;
}

type ReasonValue = "conflict" | "no_longer_needed" | "wrong_time" | "other";

const REASON_OPTIONS: Array<{ value: ReasonValue; label: string }> = [
  { value: "conflict", label: "Scheduling conflict" },
  { value: "no_longer_needed", label: "No longer needed" },
  { value: "wrong_time", label: "Wrong time selected" },
  { value: "other", label: "Other" },
];

function reasonToLabel(value: ReasonValue): string {
  const option = REASON_OPTIONS.find((item) => item.value === value);
  return option?.label || "Other";
}

export default function CancellationModal({ isOpen, isSubmitting, onClose, onConfirm }: CancellationModalProps) {
  const [reason, setReason] = useState<ReasonValue>("no_longer_needed");
  const [customReason, setCustomReason] = useState("");

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !isSubmitting) {
        onClose();
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [isOpen, isSubmitting, onClose]);

  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        setReason("no_longer_needed");
        setCustomReason("");
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  const resolvedReason = useMemo(() => {
    if (reason !== "other") {
      return reasonToLabel(reason);
    }
    const trimmed = customReason.trim();
    return trimmed || "Other";
  }, [reason, customReason]);

  function handleConfirm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onConfirm(resolvedReason);
  }

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Close cancellation modal"
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => {
          if (!isSubmitting) {
            onClose();
          }
        }}
      />

      <form
        onSubmit={handleConfirm}
        role="dialog"
        aria-modal="true"
        className="relative z-10 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl"
      >
        <h2 className="text-lg font-semibold text-slate-900">Cancel this booking?</h2>
        <p className="mt-2 text-sm text-slate-600">
          This will free the slot and notify both attendee and organizer.
        </p>

        <div className="mt-4 space-y-2">
          <label htmlFor="cancel-reason" className="block text-sm font-medium text-slate-700">
            Reason (optional)
          </label>
          <select
            id="cancel-reason"
            value={reason}
            onChange={(event) => setReason(event.target.value as ReasonValue)}
            className="w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white"
            disabled={isSubmitting}
          >
            {REASON_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {reason === "other" ? (
          <div className="mt-3">
            <label htmlFor="cancel-reason-custom" className="block text-sm font-medium text-slate-700">
              Add details
            </label>
            <textarea
              id="cancel-reason-custom"
              rows={3}
              maxLength={300}
              value={customReason}
              onChange={(event) => setCustomReason(event.target.value)}
              placeholder="Share a short reason"
              className="mt-2 w-full resize-none rounded-xl border border-slate-300 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white"
              disabled={isSubmitting}
            />
          </div>
        ) : null}

        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="inline-flex w-full items-center justify-center rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-70"
          >
            Keep booking
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex w-full items-center justify-center rounded-xl bg-rose-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-rose-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {isSubmitting ? "Cancelling..." : "Confirm cancellation"}
          </button>
        </div>
      </form>
    </div>
  );
}
