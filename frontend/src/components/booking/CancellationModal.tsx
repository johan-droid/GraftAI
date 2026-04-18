"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { FormControl, InputLabel, MenuItem, Select } from "@mui/material";
import { googleOverlayStyles } from "@/components/ui/googleOverlayStyles";

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
        className={googleOverlayStyles.backdrop}
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
        className="relative z-10 w-full max-w-md rounded-[28px] border border-[#DADCE0] bg-white p-6 shadow-[0_24px_60px_-36px_rgba(32,33,36,0.35)]"
      >
        <h2 className="text-lg font-semibold text-[#202124]">Cancel this booking?</h2>
        <p className="mt-2 text-sm text-[#5F6368]">
          This will free the slot and notify both attendee and organizer.
        </p>

        <div className="mt-4 space-y-2">
          <label htmlFor="cancel-reason" className="block text-sm font-medium text-[#202124]">
            Reason (optional)
          </label>
          <FormControl fullWidth>
            <InputLabel id="cancel-reason-label">Reason</InputLabel>
            <Select
              labelId="cancel-reason-label"
              id="cancel-reason"
              value={reason}
              label="Reason"
              onChange={(event) => setReason(event.target.value as ReasonValue)}
              disabled={isSubmitting}
            >
              {REASON_OPTIONS.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </div>

        {reason === "other" ? (
          <div className="mt-3">
            <label htmlFor="cancel-reason-custom" className="block text-sm font-medium text-[#202124]">
              Add details
            </label>
            <textarea
              id="cancel-reason-custom"
              rows={3}
              maxLength={300}
              value={customReason}
              onChange={(event) => setCustomReason(event.target.value)}
              placeholder="Share a short reason"
              className={googleOverlayStyles.fieldMuted + " mt-2 resize-none"}
              disabled={isSubmitting}
            />
          </div>
        ) : null}

        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="inline-flex w-full items-center justify-center rounded-xl border border-[#DADCE0] bg-white px-4 py-3 text-sm font-semibold text-[#202124] transition hover:bg-[#F1F3F4] disabled:cursor-not-allowed disabled:opacity-70"
          >
            Keep booking
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex w-full items-center justify-center rounded-xl bg-[#D93025] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#B3261E] disabled:cursor-not-allowed disabled:bg-[#FDE7E9] disabled:text-[#D93025]"
          >
            {isSubmitting ? "Cancelling..." : "Confirm cancellation"}
          </button>
        </div>
      </form>
    </div>
  );
}
