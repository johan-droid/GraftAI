"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon, Clock, MapPin, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

interface Event {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  source: string;
  description?: string;
  location?: string;
  meeting_url?: string;
}

interface CalendarViewProps {
  events: Event[];
  onEventClick: (event: Event) => void;
  onDateClick: (date: Date) => void;
  onCreateEvent: () => void;
}

export function CalendarView({ events, onEventClick, onDateClick, onCreateEvent }: CalendarViewProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<"month" | "week" | "day">("month");

  const monthRange = useMemo(() => {
    const monthStart = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const monthEnd = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
    const startDate = new Date(monthStart);
    startDate.setDate(startDate.getDate() - startDate.getDay());
    const endDate = new Date(monthEnd);
    endDate.setDate(endDate.getDate() + (6 - endDate.getDay()));
    return { startDate, endDate };
  }, [currentDate]);

  const days = useMemo(() => {
    const daysArray: Date[] = [];
    const current = new Date(monthRange.startDate);
    while (current <= monthRange.endDate) {
      daysArray.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }
    return daysArray;
  }, [monthRange]);

  const getEventsForDay = (day: Date) => {
    return events.filter(event => {
      const eventDate = new Date(event.start_time);
      return eventDate.toDateString() === day.toDateString();
    });
  };

  const navigate = (direction: "prev" | "next") => {
    const newDate = new Date(currentDate);
    if (view === "month") {
      newDate.setMonth(newDate.getMonth() + (direction === "next" ? 1 : -1));
    } else if (view === "week") {
      newDate.setDate(newDate.getDate() + (direction === "next" ? 7 : -7));
    } else {
      newDate.setDate(newDate.getDate() + (direction === "next" ? 1 : -1));
    }
    setCurrentDate(newDate);
  };

  const today = new Date();
  const isToday = (day: Date) => day.toDateString() === today.toDateString();
  const isCurrentMonth = (day: Date) => day.getMonth() === currentDate.getMonth();

  return (
    <div className="flex flex-col h-full lg:h-[750px] bg-transparent">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 gap-4">
        <div className="flex items-center gap-6">
          <h2 className="text-2xl font-medium text-white min-w-[160px]">
            {currentDate.toLocaleDateString("en-US", { month: "long", year: "numeric" })}
          </h2>
          <div className="flex items-center gap-1">
            <button
              onClick={() => navigate("prev")}
              className="p-1.5 hover:bg-white/5 text-gray-500 hover:text-white rounded-md transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => navigate("next")}
              className="p-1.5 hover:bg-white/5 text-gray-500 hover:text-white rounded-md transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-6 w-full sm:w-auto">
          <div className="flex gap-4">
            {(["month", "week", "day"] as const).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={cn(
                  "text-sm font-medium transition-colors capitalize pb-1 border-b-2",
                  view === v ? "border-white text-white" : "border-transparent text-gray-500 hover:text-gray-300"
                )}
              >
                {v}
              </button>
            ))}
          </div>
          <div className="w-px h-4 bg-white/10 hidden sm:block" />
          <button
            onClick={onCreateEvent}
            className="flex items-center gap-1.5 text-white bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-md font-medium transition-colors text-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New</span>
          </button>
        </div>
      </div>

      {/* Calendar Grid */}
      {view === "month" && (
        <div className="flex-1 flex flex-col bg-transparent rounded-xl border border-white/5 overflow-hidden">
          {/* Weekday Headers */}
          <div className="grid grid-cols-7 bg-white/[0.02] border-b border-white/5">
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
              <div key={day} className="text-center text-[10px] font-medium text-gray-500 uppercase tracking-widest py-3">
                <span className="hidden xl:inline">{day}</span>
                <span className="xl:hidden">{day[0]}</span>
              </div>
            ))}
          </div>

          {/* Days Grid */}
          <div className="grid grid-cols-7 flex-1">
            {days.map((day, idx) => {
              const dayEvents = getEventsForDay(day);
              
              return (
                <div
                  key={idx}
                  onClick={() => isCurrentMonth(day) && onDateClick(day)}
                  className={cn(
                    "relative flex flex-col p-2 cursor-pointer transition-colors border-b border-r border-white/5 last:border-r-0 group",
                    isCurrentMonth(day)
                      ? "hover:bg-white/[0.03]"
                      : "opacity-40 cursor-default bg-[#0a0a0f]/50",
                    (idx + 1) % 7 === 0 && "border-r-0"
                  )}
                >
                  <div className="flex justify-between items-center mb-2">
                    <div
                      className={cn(
                        "w-6 h-6 rounded-full flex items-center justify-center text-xs",
                        isToday(day)
                          ? "bg-white text-black font-semibold"
                          : isCurrentMonth(day)
                          ? "text-gray-300"
                          : "text-gray-600"
                      )}
                    >
                      {day.getDate()}
                    </div>
                  </div>

                  <div className="space-y-1 flex-1 overflow-hidden min-h-[60px] sm:min-h-[90px]">
                    {dayEvents.slice(0, 4).map((event) => {
                      const colorClass = event.source === 'google' ? 'bg-red-400' : event.source === 'microsoft' ? 'bg-blue-400' : 'bg-emerald-400';
                      return (
                        <div
                          key={event.id}
                          onClick={(e) => {
                            e.stopPropagation();
                            onEventClick(event);
                          }}
                          className="flex items-center gap-1.5 px-1.5 py-1 rounded hover:bg-white/10 transition-colors group/event"
                        >
                          <div className={cn("w-1.5 h-1.5 rounded-full shrink-0", colorClass)} />
                          <span className="text-[11px] text-gray-400 group-hover/event:text-white truncate">
                            {new Date(event.start_time).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }).replace(' ', '').toLowerCase()} {event.title}
                          </span>
                        </div>
                      )
                    })}
                    {dayEvents.length > 4 && (
                      <div className="text-[10px] text-gray-500 px-1 pt-1">
                        {dayEvents.length - 4} more
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Week View */}
      {view === "week" && (
        <div className="flex-1 overflow-auto bg-transparent rounded-xl border border-white/5">
          <div className="grid grid-cols-7 h-full min-h-[600px]">
            {days.slice(0, 7).map((day, idx) => {
              const dayEvents = getEventsForDay(day);
              return (
                <div key={idx} className="flex flex-col border-r border-white/5 last:border-r-0">
                  <div className={cn(
                    "text-center py-3 border-b border-white/5 bg-white/[0.02]",
                    isToday(day) && "bg-white/[0.04]"
                  )}>
                    <div className="text-[10px] font-medium text-gray-500 uppercase tracking-widest mb-1">
                      {day.toLocaleDateString("en-US", { weekday: "short" })}
                    </div>
                    <div className={cn(
                      "text-sm",
                      isToday(day) ? "text-white font-bold" : "text-gray-400"
                    )}>
                      {day.getDate()}
                    </div>
                  </div>
                  <div className="flex-1 p-2 space-y-1.5 hover:bg-white/[0.01] transition-colors relative">
                    {dayEvents.map((event) => {
                      const colorClass = event.source === 'google' ? 'bg-red-400' : event.source === 'microsoft' ? 'bg-blue-400' : 'bg-emerald-400';
                      return (
                        <div
                          key={event.id}
                          onClick={() => onEventClick(event)}
                          className="group/event p-2 rounded hover:bg-white/5 cursor-pointer transition-colors border border-transparent hover:border-white/5 flex flex-col gap-1"
                        >
                          <div className="flex items-center gap-2">
                            <div className={cn("w-1.5 h-1.5 rounded-full shrink-0", colorClass)} />
                            <div className="text-xs text-gray-300 group-hover/event:text-white font-medium truncate">
                              {event.title}
                            </div>
                          </div>
                          <div className="text-[10px] text-gray-500 pl-3.5 flex items-center gap-1">
                            <Clock className="w-3 h-3 opacity-50" />
                            {new Date(event.start_time).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }).toLowerCase()}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Day View */}
      {view === "day" && (
        <div className="flex-1 overflow-auto bg-transparent relative">
          <div className="max-w-4xl mx-auto py-8">
            <div className="mb-10 pl-4 border-l-2 border-white/10">
              <div className="text-sm font-medium text-gray-500 uppercase tracking-widest mb-1">
                {currentDate.toLocaleDateString("en-US", { weekday: "long" })}
              </div>
              <div className="text-3xl sm:text-4xl font-light text-white tracking-tight">
                {currentDate.toLocaleDateString("en-US", { month: "long", day: "numeric" })}
              </div>
            </div>
            
            <div className="space-y-3 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-white/5 before:to-transparent">
              {getEventsForDay(currentDate).map((event) => {
                const colorClass = event.source === 'google' ? 'bg-red-400' : event.source === 'microsoft' ? 'bg-blue-400' : 'bg-emerald-400';
                const textClass = event.source === 'google' ? 'text-red-400' : event.source === 'microsoft' ? 'text-blue-400' : 'text-emerald-400';
                
                return (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    onClick={() => onEventClick(event)}
                    className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group cursor-pointer"
                  >
                    <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white/10 bg-[#09090b] shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 absolute left-0 md:left-1/2 -translate-x-1/2 z-10 transition-colors group-hover:border-white/20">
                      <div className={cn("w-2.5 h-2.5 rounded-full shadow-sm", colorClass)} />
                    </div>
                    
                    <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-white/5 bg-white/[0.01] hover:bg-white/[0.03] transition-all ml-auto md:ml-0 shadow-sm">
                      <div className="flex items-start justify-between mb-2 gap-4">
                        <h3 className="text-base font-medium text-white group-hover:text-white transition-colors">{event.title}</h3>
                        <span className={cn("text-[10px] font-medium uppercase tracking-wider px-2 py-0.5 rounded-full bg-white/5 border border-white/5", textClass)}>
                          {event.source}
                        </span>
                      </div>
                      
                      <div className="flex flex-col gap-1.5 text-xs font-medium text-gray-500">
                        <div className="flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5" />
                          <span>
                            {new Date(event.start_time).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })} -{" "}
                            {new Date(event.end_time).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}
                          </span>
                        </div>
                        {event.location && (
                          <div className="flex items-center gap-1.5">
                            <MapPin className="w-3.5 h-3.5" />
                            <span className="truncate">{event.location}</span>
                          </div>
                        )}
                      </div>
                      
                      {event.description && (
                        <div className="mt-3 pt-3 border-t border-white/5">
                          <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed">{event.description}</p>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )
              })}
              
              {getEventsForDay(currentDate).length === 0 && (
                <div className="text-center py-24 rounded-2xl border border-white/5 border-dashed bg-white/[0.01]">
                  <CalendarIcon className="w-10 h-10 mx-auto mb-4 text-gray-600/50" strokeWidth={1.5} />
                  <h3 className="text-sm font-medium text-gray-400 mb-1">Your day is clear</h3>
                  <button 
                    onClick={onCreateEvent}
                    className="mt-6 px-4 py-2 bg-white/5 hover:bg-white/10 text-white text-xs font-medium rounded-lg transition-colors border border-white/5"
                  >
                    Add an Event
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
