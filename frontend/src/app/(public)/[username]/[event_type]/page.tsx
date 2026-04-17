"use client";

import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Clock, Video, Globe, ChevronLeft, ChevronRight, Calendar as CalendarIcon, ArrowRight } from "lucide-react";
import Link from "next/link";
import { getPublicEventDetails, getPublicEventAvailability, getPublicEventAvailabilityByDate, type PublicEventDetailsResponse, type PublicAvailabilitySlot } from "@/lib/api";

const WEEK_DAYS = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];

export default function PublicBookingPage({ params }: { params: { username: string; event_type: string } }) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<number | null>(null);
  const [selectedTime, setSelectedTime] = useState<string | null>(null);
  const [eventDetails, setEventDetails] = useState<PublicEventDetailsResponse | null>(null);
  const [monthlyAvailability, setMonthlyAvailability] = useState<Record<string, string[]>>({});
  const [dailySlots, setDailySlots] = useState<PublicAvailabilitySlot[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const monthKey = useMemo(
    () => `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, "0")}`,
    [currentDate]
  );

  const today = useMemo(() => new Date(), []);

  useEffect(() => {
    const loadEvent = async () => {
      setIsLoading(true);
      setErrorMessage(null);
      setSelectedDate(null);
      setSelectedTime(null);
      setDailySlots([]);

      try {
        const event = await getPublicEventDetails(params.username, params.event_type);
        setEventDetails(event);

        const timeZone = event.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
        const availability = await getPublicEventAvailability(params.username, params.event_type, monthKey, timeZone);
        setMonthlyAvailability(availability.availability ?? {});
      } catch {
        setErrorMessage("Unable to load booking details. Please try again later.");
      } finally {
        setIsLoading(false);
      }
    };

    loadEvent();
  }, [params.username, params.event_type, monthKey]);

  useEffect(() => {
    if (selectedDate === null) {
      setDailySlots([]);
      return;
    }

    const loadDaySlots = async () => {
      setIsLoadingSlots(true);
      setSelectedTime(null);
      try {
        const selectedDateString = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, "0")}-${String(selectedDate).padStart(2, "0")}`;
        const response = await getPublicEventAvailabilityByDate(params.username, params.event_type, selectedDateString, eventDetails?.timezone);
        setDailySlots(response.slots ?? []);
      } catch {
        setDailySlots([]);
      } finally {
        setIsLoadingSlots(false);
      }
    };

    loadDaySlots();
  }, [selectedDate, params.username, params.event_type, currentDate, eventDetails?.timezone]);

  const daysInMonth = useMemo(
    () => new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0).getDate(),
    [currentDate]
  );

  const firstDayOfMonth = useMemo(
    () => new Date(currentDate.getFullYear(), currentDate.getMonth(), 1).getDay(),
    [currentDate]
  );

  const days = useMemo(() => Array.from({ length: daysInMonth }, (_, i) => i + 1), [daysInMonth]);
  const blanks = useMemo(() => Array.from({ length: firstDayOfMonth }, (_, i) => i), [firstDayOfMonth]);

  const availableDays = useMemo(() => {
    return new Set(
      Object.keys(monthlyAvailability)
        .map((date) => new Date(date))
        .filter((date) => date.getFullYear() === currentDate.getFullYear() && date.getMonth() === currentDate.getMonth())
        .map((date) => date.getDate())
    );
  }, [monthlyAvailability, currentDate]);

  const isMonthInPast = useMemo(() => {
    return (
      currentDate.getFullYear() < today.getFullYear() ||
      (currentDate.getFullYear() === today.getFullYear() && currentDate.getMonth() < today.getMonth())
    );
  }, [currentDate, today]);

  const getDayStatus = (day: number) => {
    if (isMonthInPast) return "disabled";
    if (currentDate.getFullYear() === today.getFullYear() && currentDate.getMonth() === today.getMonth() && day < today.getDate()) {
      return "disabled";
    }
    if (!availableDays.has(day)) return "disabled";
    return selectedDate === day ? "selected" : "available";
  };

  const eventTitle = eventDetails?.title ?? `${params.event_type.replace(/-/g, " ")}`;
  const hostName = eventDetails?.username ?? params.username;
  const eventDescription = eventDetails?.description ?? "Choose a time below to lock in your slot.";
  const eventDuration = eventDetails ? `${eventDetails.duration_minutes} min` : "—";
  const locationLabel = eventDetails?.meeting_provider ? eventDetails.meeting_provider : "Video Call";
  const timeZoneLabel = eventDetails?.timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="bg-white border border-[#DADCE0] rounded-3xl shadow-sm overflow-hidden flex flex-col md:flex-row min-h-[600px]"
    >
      <div className="w-full md:w-[35%] bg-[#F8F9FA] p-8 md:p-10 border-b md:border-b-0 md:border-r border-[#DADCE0] flex flex-col">
        {isLoading ? (
          <div className="space-y-4 animate-pulse">
            <div className="w-16 h-16 rounded-full bg-[#E8F0FE]" />
            <div className="h-4 rounded bg-[#E8F0FE] w-3/4" />
            <div className="h-8 rounded bg-[#E8F0FE] w-full" />
            <div className="space-y-3 pt-6">
              <div className="h-3 rounded bg-[#E8F0FE]" />
              <div className="h-3 rounded bg-[#E8F0FE] w-5/6" />
            </div>
          </div>
        ) : errorMessage ? (
          <div className="text-sm text-[#B3261E]">{errorMessage}</div>
        ) : (
          <>
            <div className="mb-6">
              <div className="w-16 h-16 rounded-full bg-[#E8F0FE] text-[#1A73E8] flex items-center justify-center text-2xl font-medium mb-4 border border-[#DADCE0]">
                {hostName.charAt(0).toUpperCase()}
              </div>
              <p className="text-sm font-semibold text-[#5F6368] uppercase tracking-wider mb-1">
                {hostName}
              </p>
              <h1 className="text-2xl font-semibold text-[#202124] tracking-tight mb-6">
                {eventTitle}
              </h1>

              <div className="space-y-4 text-[15px] font-medium text-[#5F6368]">
                <div className="flex items-center gap-3">
                  <Clock size={20} className="text-[#1A73E8]" />
                  {eventDuration}
                </div>
                <div className="flex items-center gap-3">
                  <Video size={20} className="text-[#137333]" />
                  {locationLabel}
                </div>
                <div className="flex items-center gap-3">
                  <Globe size={20} className="text-[#E37400]" />
                  {timeZoneLabel}
                </div>
              </div>
            </div>

            <div className="mt-4 pt-6 border-t border-[#DADCE0]">
              <p className="text-sm text-[#5F6368] leading-relaxed">
                {eventDescription}
              </p>
            </div>
          </>
        )}
      </div>

      <div className="w-full md:w-[65%] p-8 md:p-10 flex flex-col md:flex-row gap-8">
        <div className={`flex-1 transition-all duration-300 ${selectedDate ? "md:pr-8 md:border-r border-[#F1F3F4]" : ""}`}>
          <h2 className="text-xl font-semibold text-[#202124] mb-6">Select a Date & Time</h2>

          <div className="flex items-center justify-between mb-6">
            <span className="text-[15px] font-medium text-[#202124]">
              {currentDate.toLocaleString("default", { month: "long", year: "numeric" })}
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                aria-label="Previous month"
                title="Previous month"
                onClick={() => {
                  setSelectedDate(null);
                  setSelectedTime(null);
                  setDailySlots([]);
                  setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
                }}
                className="w-8 h-8 rounded-full flex items-center justify-center text-[#1A73E8] hover:bg-[#E8F0FE] transition-colors"
              >
                <ChevronLeft size={20} />
              </button>
              <button
                type="button"
                aria-label="Next month"
                title="Next month"
                onClick={() => {
                  setSelectedDate(null);
                  setSelectedTime(null);
                  setDailySlots([]);
                  setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
                }}
                className="w-8 h-8 rounded-full flex items-center justify-center text-[#1A73E8] hover:bg-[#E8F0FE] transition-colors"
              >
                <ChevronRight size={20} />
              </button>
            </div>
          </div>

          <div className="grid grid-cols-7 gap-y-2 text-center mb-2">
            {WEEK_DAYS.map((d) => (
              <div key={d} className="text-[11px] font-bold text-[#5F6368] tracking-wider">
                {d}
              </div>
            ))}
          </div>

          <div className="grid grid-cols-7 gap-1 text-center">
            {blanks.map((blank) => (
              <div key={`blank-${blank}`} className="h-10" />
            ))}
            {days.map((day) => {
              const status = getDayStatus(day);
              const isSelected = selectedDate === day;

              return (
                <button
                  key={day}
                  type="button"
                  disabled={status === "disabled" || isLoading}
                  onClick={() => {
                    setSelectedDate(day);
                    setSelectedTime(null);
                  }}
                  className={`h-10 w-10 mx-auto rounded-full flex items-center justify-center text-sm font-medium transition-all ${
                    status === "disabled"
                      ? "text-[#DADCE0] cursor-not-allowed bg-transparent"
                      : isSelected
                        ? "bg-[#1A73E8] text-white shadow-md scale-105"
                        : "text-[#1A73E8] bg-[#E8F0FE] hover:bg-[#1A73E8] hover:text-white"
                  }`}
                >
                  {day}
                </button>
              );
            })}
          </div>
        </div>

        <AnimatePresence>
          {selectedDate && (
            <motion.div
              initial={{ opacity: 0, width: 0, x: 20 }}
              animate={{ opacity: 1, width: "auto", x: 0 }}
              exit={{ opacity: 0, width: 0, x: 20 }}
              className="md:w-[220px] shrink-0"
            >
              <h3 className="text-[15px] font-medium text-[#202124] mb-4 flex items-center gap-2">
                <CalendarIcon size={16} className="text-[#5F6368]" />
                {currentDate.toLocaleString("default", { month: "short" })} {selectedDate}
              </h3>

              <div className="flex flex-col gap-2 max-h-[350px] overflow-y-auto pr-2 custom-scrollbar">
                {isLoadingSlots ? (
                  <div className="space-y-3">
                    <div className="h-12 rounded-2xl bg-[#E8F0FE] animate-pulse" />
                    <div className="h-12 rounded-2xl bg-[#E8F0FE] animate-pulse" />
                    <div className="h-12 rounded-2xl bg-[#E8F0FE] animate-pulse" />
                  </div>
                ) : dailySlots.length > 0 ? (
                  dailySlots.map((slot, index) => {
                    const timeLabel = slot.invitee_start;
                    return (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.2 }}
                        key={`${slot.invitee_start}-${slot.invitee_end}-${index}`}
                        className="flex gap-2"
                      >
                        <button
                          type="button"
                          onClick={() => setSelectedTime(timeLabel)}
                          className={`flex-1 py-3 px-4 rounded-xl text-sm font-medium transition-all border ${
                            selectedTime === timeLabel
                              ? "bg-[#5F6368] border-[#5F6368] text-white"
                              : "bg-white border-[#1A73E8] text-[#1A73E8] hover:border-[2px]"
                          }`}
                        >
                          {timeLabel}
                        </button>

                        {selectedTime === timeLabel && (
                          <Link
                            href={`/book?username=${encodeURIComponent(params.username)}&event_type=${encodeURIComponent(params.event_type)}&date=${encodeURIComponent(
                              `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, "0")}-${String(selectedDate).padStart(2, "0")}`
                            )}&time=${encodeURIComponent(timeLabel)}`}
                            aria-label="Continue to booking"
                            title="Continue to booking"
                            className="w-14 rounded-xl bg-[#1A73E8] text-white flex items-center justify-center hover:bg-[#1557B0] transition-colors"
                          >
                            <ArrowRight size={20} />
                          </Link>
                        )}
                      </motion.div>
                    );
                  })
                ) : (
                  <div className="rounded-3xl border border-[#DADCE0] bg-[#F8F9FA] p-5 text-sm text-[#5F6368]">
                    No available times for this date yet. Please choose another day.
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
