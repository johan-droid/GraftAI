"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, Plus, Calendar as CalendarIcon, Loader2 } from "lucide-react";
import { useCalendar } from "@/hooks/useCalendar";
import { Booking } from "@/types/api";

const DAYS_OF_WEEK = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export default function HeavyTileCalendar() {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const { bookings, isLoading } = useCalendar(currentMonth);
  const router = useRouter();

  const handleNewEvent = () => {
    // Navigate to the new event flow (page may be implemented separately)
    router.push("/dashboard/calendar/new");
  };

  const daysInMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0).getDate();
  const firstDayOfMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1).getDay();

  const calendarGrid = Array(firstDayOfMonth).fill(null).concat(Array.from({ length: daysInMonth }, (_, i) => i + 1));
  while (calendarGrid.length % 7 !== 0) calendarGrid.push(null);

  const prevMonth = () => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1));
  const nextMonth = () => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1));

  const getTileColor = (status: Booking["status"]) => {
    switch (status) {
      case "confirmed":
        return "bg-[#1A73E8] text-white";
      case "pending":
        return "bg-[#E37400] text-white";
      case "cancelled":
        return "bg-[#F1F3F4] text-[#5F6368] line-through";
      case "rescheduled":
        return "bg-[#9334E6] text-white";
      default:
        return "bg-[#1A73E8] text-white";
    }
  };

  const formatTime = (isoString: string) => {
    return new Date(isoString).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto w-full h-full flex flex-col">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4 shrink-0">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-white border border-[#DADCE0] shadow-sm flex items-center justify-center text-[#1A73E8]">
            {isLoading ? <Loader2 size={24} className="animate-spin text-[#5F6368]" /> : <CalendarIcon size={24} />}
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-normal text-[#202124] tracking-tight">
              {currentMonth.toLocaleString("default", { month: "long", year: "numeric" })}
            </h1>
            <p className="text-sm text-[#5F6368]">Your scheduling overview</p>
          </div>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="flex items-center bg-white border border-[#DADCE0] rounded-full p-1 shadow-sm">
            <button
              aria-label="Previous month"
              title="Previous month"
              onClick={prevMonth}
              className="p-2 rounded-full hover:bg-[#F1F3F4] text-[#5F6368] transition-colors"
            >
              <ChevronLeft size={20} />
            </button>
            <button
              onClick={() => setCurrentMonth(new Date())}
              className="px-4 text-sm font-medium text-[#202124] hover:bg-[#F1F3F4] rounded-full transition-colors h-full"
            >
              Today
            </button>
            <button
              aria-label="Next month"
              title="Next month"
              onClick={nextMonth}
              className="p-2 rounded-full hover:bg-[#F1F3F4] text-[#5F6368] transition-colors"
            >
              <ChevronRight size={20} />
            </button>
          </div>

          <button
            onClick={handleNewEvent}
            aria-label="Create new event"
            className="hidden sm:flex items-center gap-2 bg-[#1A73E8] text-white hover:bg-[#1557B0] px-5 py-2.5 rounded-full text-sm font-medium transition-colors shadow-sm"
          >
            <Plus size={18} />
            New Event
          </button>
        </div>
      </div>

      <div className="flex-1 bg-white border border-[#DADCE0] rounded-2xl overflow-hidden shadow-sm flex flex-col min-h-0">
        <div className="grid grid-cols-7 border-b border-[#DADCE0] bg-[#F8F9FA] shrink-0">
          {DAYS_OF_WEEK.map((day) => (
            <div key={day} className="py-3 text-center text-xs font-semibold text-[#5F6368] uppercase tracking-wider">
              {day}
            </div>
          ))}
        </div>

        <div className="flex-1 grid grid-cols-7 gap-[1px] bg-[#DADCE0] overflow-y-auto">
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
              <div
                key={index}
                className={`bg-white min-h-[100px] sm:min-h-[140px] p-1 sm:p-2 transition-colors group ${day ? "hover:bg-[#F8F9FA] cursor-pointer" : ""}`}
              >
                {day && (
                  <>
                    <div className="flex justify-between items-start mb-2">
                      <span
                        className={`flex items-center justify-center w-7 h-7 text-sm font-medium rounded-full ${
                          isToday ? "bg-[#1A73E8] text-white shadow-sm" : "text-[#5F6368]"
                        }`}
                      >
                        {day}
                      </span>
                    </div>

                    <div className="flex flex-col gap-1 overflow-hidden">
                      {dayBookings.map((booking) => (
                        <div
                          key={booking.id}
                          title={`${booking.attendee_name} - ${booking.status}`}
                          className={`px-2 py-1.5 rounded-md text-xs font-medium truncate shadow-sm transition-transform hover:scale-[1.02] ${getTileColor(
                            booking.status
                          )}`}
                        >
                          <span className="opacity-80 mr-1">{formatTime(booking.start_time)}</span>
                          {booking.attendee_name}
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
