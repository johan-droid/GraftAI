/**
 * Mobile-Responsive Calendar Page
 * 
 * Following Material Design 3 principles:
 * - Adaptive calendar views (month grid desktop, day view mobile)
 * - FAB for primary action on mobile
 * - Compact weekday headers (single letter on mobile)
 * - Touch-friendly day cells (min 48dp)
 * - Bottom sheet for event details
 * 
 * @see https://m3.material.io/components/calendar/overview
 */

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ChevronLeft, 
  ChevronRight, 
  Plus, 
  Calendar as CalendarIcon, 
  Loader2,
  X,
  Clock,
  User
} from "lucide-react";
import { useCalendar } from "@/hooks/useCalendar";
import { Booking } from "@/types/api";
import { useTheme } from "@/contexts/ThemeContext";

// M3 Motion tokens
const m3Motion = {
  standard: { duration: 0.15, ease: "easeOut" as const },
  emphasized: { duration: 0.3, ease: "easeInOut" as const },
};

// Responsive weekday labels
const DAYS_OF_WEEK_FULL = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const DAYS_OF_WEEK_SHORT = ["S", "M", "T", "W", "T", "F", "S"];

type CalendarView = "month" | "day" | "week";

export default function HeavyTileCalendar() {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [viewMode, setViewMode] = useState<CalendarView>("month");
  const { bookings, isLoading } = useCalendar(currentMonth);
  const router = useRouter();
  const { mode } = useTheme();
  const isDark = mode === "dark";
  const [isMobileScreen, setIsMobileScreen] = useState(false);

  // M3 Surface colors
  const surfaceColor = isDark ? "bg-[#1C1B1F]" : "bg-white";
  const surfaceVariantColor = isDark ? "bg-[#141415]" : "bg-[#F8F9FA]";
  const onSurfaceColor = isDark ? "text-[#E6E1E5]" : "text-[#202124]";
  const onSurfaceVariantColor = isDark ? "text-[#938F99]" : "text-[#5F6368]";
  const outlineColor = isDark ? "border-[#49454F]" : "border-[#DADCE0]";
  const outlineVariantColor = isDark ? "border-[#49454F]" : "border-[#F1F3F4]";

  const handleNewEvent = () => {
    router.push("/dashboard/calendar/new");
  };

  const handleDayClick = (day: number) => {
    const clickedDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
    setSelectedDate(clickedDate);
  };

  const closeDaySheet = () => {
    setSelectedDate(null);
  };

  const daysInMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0).getDate();
  const firstDayOfMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1).getDay();

  const calendarGrid = Array(firstDayOfMonth).fill(null).concat(Array.from({ length: daysInMonth }, (_, i) => i + 1));
  while (calendarGrid.length % 7 !== 0) calendarGrid.push(null);

  const activeDate = selectedDate ?? new Date();
  const activeDayBookings = getDayBookings(activeDate, bookings);
  const effectiveViewMode = isMobileScreen ? viewMode : "month";

  useEffect(() => {
    if (typeof window === "undefined") return;

    const updateIsMobile = () => {
      setIsMobileScreen(window.innerWidth < 640);
    };

    updateIsMobile();
    window.addEventListener("resize", updateIsMobile);
    return () => window.removeEventListener("resize", updateIsMobile);
  }, []);

  const prevMonth = () => {
    const newDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1);
    setCurrentMonth(newDate);
  };
  
  const nextMonth = () => {
    const newDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1);
    setCurrentMonth(newDate);
  };

  const formatTime = (isoString: string) => {
    return new Date(isoString).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="p-4 sm:p-6 md:p-8 max-w-7xl mx-auto w-full h-full flex flex-col relative">
      {/* Header - Responsive layout */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 sm:mb-6 gap-3 sm:gap-4 shrink-0">
        <div className="flex items-center gap-3 sm:gap-4">
          <div className={`
            w-10 h-10 sm:w-12 sm:h-12 rounded-2xl 
            flex items-center justify-center
            ${surfaceColor} ${outlineColor} border shadow-sm
            ${isDark ? "text-[#AAC7FF]" : "text-[#1A73E8]"}
          `}>
            {isLoading ? <Loader2 size={22} className={`animate-spin ${isDark ? "text-[#938F99]" : "text-[#5F6368]"}`} /> : <CalendarIcon size={22} />}
          </div>
          <div>
            <h1 className={`text-xl sm:text-2xl md:text-3xl font-normal tracking-tight ${onSurfaceColor}`}>
              {currentMonth.toLocaleString("default", { month: "long", year: "numeric" })}
            </h1>
            <p className={`text-sm ${onSurfaceVariantColor}`}>Your scheduling overview</p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3 w-full sm:w-auto">
          {/* View Mode Toggle - Mobile only */}
          <div className="flex sm:hidden items-center bg-[#1A73E8]/10 rounded-full p-1">
            <button
              onClick={() => setViewMode("month")}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                viewMode === "month" 
                  ? "bg-[#1A73E8] text-white" 
                  : isDark ? "text-[#AAC7FF]" : "text-[#1A73E8]"
              }`}
            >
              Month
            </button>
            <button
              onClick={() => setViewMode("day")}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                viewMode === "day" 
                  ? "bg-[#1A73E8] text-white" 
                  : isDark ? "text-[#AAC7FF]" : "text-[#1A73E8]"
              }`}
            >
              Day
            </button>
          </div>

          <div className={`
            flex items-center rounded-full p-1 shadow-sm
            ${surfaceColor} ${outlineColor} border
          `}>
            <motion.button
              whileTap={{ scale: 0.95 }}
              aria-label="Previous month"
              title="Previous month"
              onClick={prevMonth}
              className={`
                p-2 rounded-full transition-colors touch-manipulation
                ${isDark ? "hover:bg-[#49454F] text-[#938F99]" : "hover:bg-[#F1F3F4] text-[#5F6368]"}
              `}
              style={{ minWidth: '40px', minHeight: '40px' }}
            >
              <ChevronLeft size={20} />
            </motion.button>
            <button
              onClick={() => setCurrentMonth(new Date())}
              className={`
                px-3 sm:px-4 text-sm font-medium rounded-full transition-colors h-full
                ${isDark ? "text-[#E6E1E5] hover:bg-[#49454F]" : "text-[#202124] hover:bg-[#F1F3F4]"}
              `}
            >
              Today
            </button>
            <motion.button
              whileTap={{ scale: 0.95 }}
              aria-label="Next month"
              title="Next month"
              onClick={nextMonth}
              className={`
                p-2 rounded-full transition-colors touch-manipulation
                ${isDark ? "hover:bg-[#49454F] text-[#938F99]" : "hover:bg-[#F1F3F4] text-[#5F6368]"}
              `}
              style={{ minWidth: '40px', minHeight: '40px' }}
            >
              <ChevronRight size={20} />
            </motion.button>
          </div>

          {/* Desktop New Event Button */}
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={handleNewEvent}
            aria-label="Create new event"
            className="hidden sm:flex items-center gap-2 bg-[#1A73E8] text-white hover:bg-[#1557B0] px-5 py-2.5 rounded-full text-sm font-medium transition-colors shadow-sm"
          >
            <Plus size={18} />
            New Event
          </motion.button>
        </div>
      </div>

      {/* Calendar Container */}
      <div className={`
        flex-1 rounded-2xl overflow-hidden shadow-sm flex flex-col min-h-0
        ${surfaceColor} ${outlineColor} border
      `}>
        {/* Weekday Headers - Responsive */}
        <div className={`
          grid grid-cols-7 border-b
          ${isDark ? "bg-[#1C1B1F] border-[#49454F]" : "bg-[#F8F9FA] border-[#DADCE0]"}
          shrink-0
        `}>
          {(typeof window !== 'undefined' && window.innerWidth < 640 ? DAYS_OF_WEEK_SHORT : DAYS_OF_WEEK_FULL).map((day) => (
            <div 
              key={day} 
              className={`
                py-2 sm:py-3 text-center text-xs font-semibold uppercase tracking-wider
                ${onSurfaceVariantColor}
              `}
            >
              {day}
            </div>
          ))}
        </div>

        {effectiveViewMode === "month" ? (
          <div className={`
            flex-1 grid grid-cols-7 gap-[1px] overflow-y-auto
            ${isDark ? "bg-[#49454F]" : "bg-[#DADCE0]"}
          `}>
            {calendarGrid.map((day, index) => {
            const isToday =
              day === new Date().getDate() &&
              currentMonth.getMonth() === new Date().getMonth() &&
              currentMonth.getFullYear() === new Date().getFullYear();

            const dayBookings = bookings?.filter((b) => {
              if (!day) return false;
              const bookingDate = new Date(b.start_time);
              return (
                bookingDate.getFullYear() === currentMonth.getFullYear() &&
                bookingDate.getMonth() === currentMonth.getMonth() &&
                bookingDate.getDate() === day
              );
            }) || [];

            return (
              <motion.div
                key={index}
                whileTap={day ? { scale: 0.98 } : undefined}
                onClick={() => day && handleDayClick(day)}
                className={`
                  ${surfaceColor} 
                  min-h-[80px] sm:min-h-[100px] md:min-h-[140px] 
                  p-1 sm:p-2 transition-colors 
                  ${day ? "cursor-pointer touch-manipulation" : ""}
                  ${day && isDark ? "hover:bg-[#2D2D30]" : day ? "hover:bg-[#F8F9FA]" : ""}
                `}
                style={{ minHeight: '80px' }}
              >
                {day && (
                  <>
                    <div className="flex justify-between items-start mb-1 sm:mb-2">
                      <span
                        className={`
                          flex items-center justify-center 
                          w-6 h-6 sm:w-7 sm:h-7 
                          text-xs sm:text-sm font-medium rounded-full
                          ${isToday 
                            ? "bg-[#1A73E8] text-white shadow-sm" 
                            : isDark ? "text-[#C9C5CA]" : "text-[#5F6368]"
                          }
                        `}
                      >
                        {day}
                      </span>
                      {dayBookings.length > 0 && (
                        <span className={`
                          text-[10px] font-medium px-1.5 py-0.5 rounded-full
                          ${isDark ? "bg-[#004878] text-[#AAC7FF]" : "bg-[#E8F0FE] text-[#1A73E8]"}
                        `}>
                          {dayBookings.length}
                        </span>
                      )}
                    </div>

                    {/* Event Pills - Limited on mobile */}
                    <div className="flex flex-col gap-1 overflow-hidden">
                      {dayBookings.slice(0, 2).map((booking) => (
                        <div
                          key={booking.id}
                          className={`
                            px-1.5 sm:px-2 py-1 rounded-md 
                            text-[10px] sm:text-xs font-medium 
                            truncate shadow-sm
                            ${getTileColor(booking.status, isDark)}
                          `}
                        >
                          <span className="hidden sm:inline opacity-80 mr-1">{formatTime(booking.start_time)}</span>
                          <span className="truncate">{booking.attendee_name}</span>
                        </div>
                      ))}
                      {dayBookings.length > 2 && (
                        <div className={`
                          text-[10px] text-center py-0.5 rounded
                          ${isDark ? "text-[#938F99]" : "text-[#5F6368]"}
                        `}>
                          +{dayBookings.length - 2} more
                        </div>
                      )}
                    </div>
                  </>
                )}
              </motion.div>
            );
          })}
          </div>
        ) : (
          <div className={`
            flex-1 overflow-y-auto p-4
            ${surfaceColor}
          `}>
            <div className={`mb-4 rounded-3xl border px-4 py-3 ${surfaceVariantColor} ${outlineVariantColor}`}>
              <div className={`text-sm font-semibold ${onSurfaceColor}`}>
                {activeDate.toLocaleDateString("default", { weekday: "long", month: "short", day: "numeric" })}
              </div>
              <div className={`text-xs ${onSurfaceVariantColor}`}>
                {activeDayBookings.length} event{activeDayBookings.length === 1 ? "" : "s"}
              </div>
            </div>

            {activeDayBookings.length > 0 ? (
              <div className="space-y-3">
                {activeDayBookings.map((booking) => (
                  <div key={booking.id} className={`rounded-3xl border p-4 ${surfaceVariantColor} ${outlineColor}`}>
                    <div className="flex items-center justify-between gap-3 mb-2">
                      <div>
                        <p className={`text-sm font-semibold ${onSurfaceColor}`}>{booking.attendee_name}</p>
                        <p className={`text-xs ${onSurfaceVariantColor}`}>{formatTime(booking.start_time)} - {formatTime(booking.end_time)}</p>
                      </div>
                      <span className={`text-[10px] font-semibold uppercase px-2 py-1 rounded-full ${getTileColor(booking.status, isDark)}`}>{booking.status}</span>
                    </div>
                    <p className={`text-xs ${onSurfaceVariantColor}`}>{booking.attendee_email}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className={`rounded-3xl border p-6 text-center ${surfaceVariantColor} ${outlineColor}`}>
                <p className={`text-sm font-medium ${onSurfaceColor}`}>No events scheduled for this date.</p>
                <p className={`text-xs mt-2 ${onSurfaceVariantColor}`}>Tap any day in month view to preview a day schedule.</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Mobile FAB - Floating Action Button */}
      <motion.button
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        whileTap={{ scale: 0.9 }}
        onClick={handleNewEvent}
        className="
          sm:hidden fixed right-4 bottom-24 z-50
          w-14 h-14 rounded-2xl
          bg-[#1A73E8] text-white
          shadow-lg shadow-[#1A73E8]/30
          flex items-center justify-center
          transition-colors hover:bg-[#1557B0]
        "
        aria-label="Create new event"
      >
        <Plus size={24} />
      </motion.button>

      {/* Day Detail Bottom Sheet - Mobile */}
      <AnimatePresence>
        {selectedDate && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={closeDaySheet}
              className="fixed inset-0 bg-black/50 z-40 sm:hidden"
            />
            
            {/* Bottom Sheet */}
            <motion.div
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={m3Motion.emphasized}
              className={`
                fixed bottom-0 left-0 right-0 z-50
                rounded-t-3xl max-h-[70vh]
                sm:hidden
                ${isDark ? "bg-[#1C1B1F]" : "bg-white"}
              `}
            >
              {/* Drag Handle */}
              <div className="flex justify-center pt-3 pb-2">
                <div className={`
                  w-10 h-1 rounded-full
                  ${isDark ? "bg-[#49454F]" : "bg-[#DADCE0]"}
                `} />
              </div>
              
              {/* Header */}
              <div className="flex items-center justify-between px-4 pb-4">
                <div>
                  <h2 className={`text-lg font-semibold ${onSurfaceColor}`}>
                    {selectedDate.toLocaleDateString("default", { weekday: "long", month: "short", day: "numeric" })}
                  </h2>
                  <p className={`text-sm ${onSurfaceVariantColor}`}>
                    {getDayBookings(selectedDate, bookings).length} events
                  </p>
                </div>
                <motion.button
                  whileTap={{ scale: 0.9 }}
                  onClick={closeDaySheet}
                  className={`
                    p-2 rounded-full
                    ${isDark ? "hover:bg-[#49454F] text-[#938F99]" : "hover:bg-[#F1F3F4] text-[#5F6368]"}
                  `}
                >
                  <X size={20} />
                </motion.button>
              </div>
              
              {/* Events List */}
              <div className={`
                px-4 pb-8 overflow-y-auto max-h-[50vh]
                ${isDark ? "divide-y divide-[#49454F]" : "divide-y divide-[#F1F3F4]"}
              `}>
                {getDayBookings(selectedDate, bookings).length > 0 ? (
                  getDayBookings(selectedDate, bookings).map((booking) => (
                    <div key={booking.id} className="py-4 flex items-start gap-3">
                      <div className={`
                        w-12 h-12 rounded-xl flex items-center justify-center shrink-0
                        ${getTileColor(booking.status, isDark)}
                      `}>
                        <Clock size={20} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className={`font-semibold truncate ${onSurfaceColor}`}>
                          {booking.attendee_name}
                        </h3>
                        <p className={`text-sm ${onSurfaceVariantColor}`}>
                          {formatTime(booking.start_time)} - {formatTime(booking.end_time)}
                        </p>
                        <p className={`text-xs mt-1 ${onSurfaceVariantColor}`}>
                          <User size={12} className="inline mr-1" />
                          {booking.attendee_name}
                        </p>
                      </div>
                      <span className={`
                        px-2 py-1 rounded-full text-xs font-medium shrink-0
                        ${getTileColor(booking.status, isDark)}
                      `}>
                        {booking.status}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="py-12 text-center">
                    <div className={`
                      w-16 h-16 rounded-full mx-auto mb-3
                      flex items-center justify-center
                      ${isDark ? "bg-[#49454F] text-[#938F99]" : "bg-[#F8F9FA] text-[#DADCE0]"}
                    `}>
                      <CalendarIcon size={24} />
                    </div>
                    <p className={`text-sm ${onSurfaceVariantColor}`}>No events scheduled</p>
                  </div>
                )}
              </div>
              
              {/* Add Event Button */}
              <div className={`
                px-4 py-4 border-t
                ${isDark ? "border-[#49454F]" : "border-[#F1F3F4]"}
              `}>
                <motion.button
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    closeDaySheet();
                    handleNewEvent();
                  }}
                  className="
                    w-full py-3 rounded-xl
                    bg-[#1A73E8] text-white
                    font-medium text-sm
                    transition-colors hover:bg-[#1557B0]
                  "
                >
                  <Plus size={18} className="inline mr-2" />
                  Add Event
                </motion.button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

// Helper function to get bookings for a specific date
function getDayBookings(date: Date, bookings: Booking[] | undefined): Booking[] {
  if (!bookings) return [];
  return bookings.filter((b) => {
    const bookingDate = new Date(b.start_time);
    return (
      bookingDate.getFullYear() === date.getFullYear() &&
      bookingDate.getMonth() === date.getMonth() &&
      bookingDate.getDate() === date.getDate()
    );
  });
}

// Updated tile color function with dark mode support
function getTileColor(status: Booking["status"], isDark: boolean): string {
  switch (status) {
    case "confirmed":
      return isDark 
        ? "bg-[#004878] text-[#D7E3FC]" 
        : "bg-[#1A73E8] text-white";
    case "pending":
      return isDark 
        ? "bg-[#5C3B00] text-[#FFDEA2]" 
        : "bg-[#E37400] text-white";
    case "cancelled":
      return isDark 
        ? "bg-[#49454F] text-[#938F99] line-through" 
        : "bg-[#F1F3F4] text-[#5F6368] line-through";
    case "rescheduled":
      return isDark 
        ? "bg-[#580B74] text-[#F3D7FF]" 
        : "bg-[#9334E6] text-white";
    default:
      return isDark 
        ? "bg-[#004878] text-[#D7E3FC]" 
        : "bg-[#1A73E8] text-white";
  }
}
