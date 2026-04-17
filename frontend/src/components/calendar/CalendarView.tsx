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

  const getEventTitle = (event: Event) => {
    const normalized = event.title?.trim();
    return normalized ? normalized : "Untitled event";
  };

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
    <div className="flex flex-col h-full lg:h-[700px] bg-transparent font-mono">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 gap-4 border-b border-solid border-[var(--border-subtle)] mb-5">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-[var(--text-primary)] min-w-[120px]">
            {currentDate.toLocaleDateString("en-US", { month: "long", year: "numeric" })}
          </h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate("prev")}
              aria-label="Previous period"
              className="p-1.5 border border-[var(--border-subtle)] hover:border-[var(--primary)] text-[var(--text-muted)] hover:text-[var(--primary)] transition-all bg-transparent"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => navigate("next")}
              aria-label="Next period"
              className="p-1.5 border border-[var(--border-subtle)] hover:border-[var(--primary)] text-[var(--text-muted)] hover:text-[var(--primary)] transition-all bg-transparent"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-4 w-full sm:w-auto">
          <div className="flex gap-2">
            {(["month", "week", "day"] as const).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={cn(
                  "px-2 py-1 text-sm font-medium transition-all",
                  view === v 
                    ? "border-[var(--primary)] text-[var(--primary)] bg-[var(--bg-hover)]" 
                    : "border-transparent text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
                )}
              >
                {v}
              </button>
            ))}
          </div>
          <div className="w-px h-4 bg-[var(--border-subtle)] hidden sm:block" />
          <button
            onClick={onCreateEvent}
            className="flex items-center gap-2 text-white bg-[var(--primary)] px-3 py-1.5 font-medium rounded-sm text-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Event</span>
          </button>
        </div>
      </div>

      {/* Calendar Grid */}
      {view === "month" && (
        <div className="flex-1 flex flex-col bg-[var(--bg-base)] border border-[var(--border-subtle)] overflow-hidden">
          {/* Weekday Headers */}
          <div className="grid grid-cols-7 bg-[var(--bg-elevated)] border-b border-[var(--border-subtle)]">
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
              <div key={day} className="text-center text-xs font-semibold text-[var(--text-muted)] py-2 bg-[var(--bg-card)]">
                {day}
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
                    "relative flex flex-col p-2 cursor-pointer transition-all border-b border-r border-[var(--border-subtle)] last:border-r-0 group h-20 md:h-28",
                    isCurrentMonth(day)
                      ? "hover:bg-[var(--bg-hover)]"
                      : "opacity-30 cursor-default bg-transparent",
                    (idx + 1) % 7 === 0 && "border-r-0"
                  )}
                >
                  <div className="flex justify-between items-center mb-2">
                    <div
                      className={cn(
                        "w-7 h-7 flex items-center justify-center text-[10px] font-bold border transition-all",
                        isToday(day)
                          ? "border-[var(--primary)] text-[var(--primary)] shadow-[0_0_10px_var(--primary-glow)]"
                          : isCurrentMonth(day)
                          ? "text-[var(--text-secondary)] border-transparent group-hover:border-[var(--border-subtle)]"
                          : "text-[var(--text-faint)] border-transparent"
                      )}
                    >
                      {day.getDate()}
                    </div>
                  </div>

                  <div className="space-y-1 flex-1 overflow-hidden">
                    {dayEvents.slice(0, 4).map((event) => {
                      const colorToken = event.source === 'google' ? 'var(--accent)' : event.source === 'microsoft' ? 'var(--secondary)' : 'var(--primary)';
                      return (
                        <div
                          key={event.id}
                          onClick={(e) => {
                            e.stopPropagation();
                            onEventClick(event);
                          }}
                          className={cn(
                            "flex items-center gap-2 px-2 py-0.5 bg-transparent border-l-2 transition-all group/event",
                            event.source === 'google' ? 'border-[var(--accent)]' : event.source === 'microsoft' ? 'border-[var(--secondary)]' : 'border-[var(--primary)]'
                          )}
                        >
                          <span className="text-[11px] text-[var(--text-secondary)] truncate">
                            {new Date(event.start_time).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }).toLowerCase()} {getEventTitle(event)}
                          </span>
                        </div>
                      )
                    })}
                    {dayEvents.length > 4 && (
                      <div className="text-[11px] text-[var(--text-muted)] font-medium px-1 pt-1">
                        + {dayEvents.length - 4} items
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
        <div className="flex-1 overflow-auto bg-[var(--bg-base)] border border-[var(--border-subtle)]">
          <div className="grid grid-cols-7 h-full min-h-[600px]">
            {days.slice(0, 7).map((day, idx) => {
              const dayEvents = getEventsForDay(day);
              return (
                <div key={idx} className="flex flex-col border-r border-dashed border-[var(--border-subtle)] last:border-r-0">
                  <div className={cn(
                    "text-center py-4 border-b border-dashed border-[var(--border-subtle)] bg-[var(--bg-elevated)]",
                    isToday(day) && "bg-[var(--bg-hover)] border-b-[var(--primary)]"
                  )}>
                    <div className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-widest mb-1">
                      {day.toLocaleDateString("en-US", { weekday: "short" })}
                    </div>
                    <div className={cn(
                      "text-sm font-bold",
                      isToday(day) ? "text-[var(--primary)]" : "text-[var(--text-secondary)]"
                    )}>
                      {day.getDate()}
                    </div>
                  </div>
                  <div className="flex-1 p-2 space-y-2 hover:bg-[var(--bg-hover)] transition-all relative">
                    {dayEvents.map((event) => {
                      const colorToken = event.source === 'google' ? 'var(--accent)' : event.source === 'microsoft' ? 'var(--secondary)' : 'var(--primary)';
                      return (
                        <div
                          key={event.id}
                          onClick={() => onEventClick(event)}
                          className={cn(
                            "group/event p-3 bg-[var(--bg-elevated)] border-l-2 border-transparent hover:border-l-[var(--primary)] cursor-pointer transition-all border border-[var(--border-subtle)] flex flex-col gap-1",
                            event.source === 'google' ? 'border-[var(--accent)]' : event.source === 'microsoft' ? 'border-[var(--secondary)]' : 'border-[var(--primary)]'
                          )}
                        >
                          <div className="text-[11px] text-[var(--text-primary)] font-bold truncate">
                            {getEventTitle(event)}
                          </div>
                          <div className="text-[10px] text-[var(--text-muted)] flex items-center gap-1">
                            <Clock className="w-3 h-3 opacity-70" />
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
        <div className="flex-1 overflow-auto bg-[var(--bg-base)] relative">
          <div className="max-w-4xl mx-auto py-10 px-6">
            <div className="mb-12 pl-6 border-l-2 border-[var(--primary)]">
              <div className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-[0.2em] mb-2">
                {currentDate.toLocaleDateString("en-US", { weekday: "long" })}
              </div>
              <div className="text-4xl font-black text-[var(--text-primary)] tracking-tighter uppercase">
                {currentDate.toLocaleDateString("en-US", { month: "long", day: "numeric" })}
              </div>
            </div>
            
            <div className="space-y-6 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-[1px] before:border-l before:border-dashed before:border-[var(--border-subtle)]">
              {getEventsForDay(currentDate).map((event) => {
                const colorToken = event.source === 'google' ? 'var(--accent)' : event.source === 'microsoft' ? 'var(--secondary)' : 'var(--primary)';
                
                return (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    onClick={() => onEventClick(event)}
                    className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group cursor-pointer"
                  >
                    <div className="flex items-center justify-center w-10 h-10 border border-[var(--border-subtle)] bg-[var(--bg-elevated)] shadow-lg shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 absolute left-0 md:left-1/2 -translate-x-1/2 z-10 transition-all group-hover:border-[var(--primary)]">
                            <div className={cn(
                              "w-2.5 h-2.5 shadow-sm",
                              event.source === 'google' ? 'bg-[var(--accent)]' : event.source === 'microsoft' ? 'bg-[var(--secondary)]' : 'bg-[var(--primary)]'
                            )} />
                      
                      <div className="flex flex-col gap-2 text-xs font-bold text-[var(--text-secondary)]">
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4 text-[var(--primary)]" />
                          <span>
                            {new Date(event.start_time).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })} -{" "}
                            {new Date(event.end_time).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}
                          </span>
                        </div>
                        {event.location && (
                          <div className="flex items-center gap-2">
                            <MapPin className="w-4 h-4 text-[var(--accent)]" />
                            <span className="truncate">{event.location}</span>
                          </div>
                        )}
                      </div>
                      
                      {event.description && (
                         <div className="mt-4 pt-4 border-t border-dashed border-[var(--border-subtle)]">
                          <p className="text-xs text-[var(--text-muted)] leading-relaxed italic line-clamp-2">
                            {event.description}
                          </p>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )
              })}
              
              {getEventsForDay(currentDate).length === 0 && (
                <div className="text-center py-24 border border-[var(--border-subtle)] border-dashed bg-[var(--bg-elevated)]">
                  <CalendarIcon className="w-10 h-10 mx-auto mb-4 text-[var(--text-muted)]" strokeWidth={1} />
                  <h3 className="text-xs font-bold text-[var(--text-muted)] mb-1 uppercase tracking-widest">System idle: No operations scheduled</h3>
                  <button 
                    onClick={onCreateEvent}
                    className="mt-6 px-6 py-2 bg-[var(--primary)] text-black text-[10px] font-black uppercase tracking-widest hover:brightness-110 transition-all shadow-[0_0_15px_var(--primary-glow)]"
                  >
                    Initialize Event
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
