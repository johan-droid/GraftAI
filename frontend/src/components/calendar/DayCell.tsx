import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface CalendarEventSummary {
  id: string | number;
  title: string;
  category?: string;
}

interface CategoryStyle {
  bg?: string;
  text?: string;
}

interface DayCellProps {
  day: Date;
  today: Date;
  currentDate: Date;
  selectedDate: Date | null;
  dayEvents: CalendarEventSummary[];
  onSelect: (day: Date) => void;
  categories: Record<string, CategoryStyle>;
}

export const DayCell = React.memo(({ 
  day, 
  today, 
  currentDate, 
  selectedDate, 
  dayEvents, 
  onSelect,
  categories 
}: DayCellProps) => {
  const isSelected = selectedDate?.toDateString() === day.toDateString();
  const isToday = day.toDateString() === today.toDateString();
  const isCurrentMonth = day.getMonth() === currentDate.getMonth();

  return (
    <motion.div
      whileHover={{ scale: isCurrentMonth ? 1.02 : 1 }}
      onClick={() => isCurrentMonth && onSelect(day)}
      className={cn(
        "relative flex flex-col p-1 rounded-md cursor-pointer min-h-[52px] sm:min-h-[72px] md:min-h-[92px] transition-all border",
        isSelected
          ? "border-indigo-400/40 bg-indigo-50"
          : isCurrentMonth
          ? "border-transparent bg-transparent hover:bg-[var(--bg-hover)]"
          : "border-transparent opacity-30 cursor-default"
      )}
    >
      <div
        className={cn(
          "w-7 h-7 rounded-full flex items-center justify-center text-sm font-semibold mb-1 self-center",
          isToday ? "bg-[var(--primary)] text-white" : isSelected ? "text-[var(--text-secondary)]" : "text-slate-400"
        )}
      >
        {day.getDate()}
      </div>

      <div className="space-y-0.5 flex-1">
        {dayEvents.slice(0, 2).map((ev) => (
          <div
            key={ev.id}
            className={cn(
              "text-[11px] font-medium px-1 py-0.5 rounded-sm truncate",
              categories[ev.category]?.bg ?? "bg-slate-200/10",
              categories[ev.category]?.text ?? "text-slate-300"
            )}
          >
            {ev.title?.trim() || "Untitled event"}
          </div>
        ))}
        {dayEvents.length > 2 && (
          <div className="text-[10px] text-slate-500 font-medium px-1">
            +{dayEvents.length - 2} more
          </div>
        )}
      </div>
    </motion.div>
  );
}, (prev, next) => {
  // Custom Comparison for maximum performance
  return (
    prev.day.toDateString() === next.day.toDateString() &&
    prev.selectedDate?.toDateString() === next.selectedDate?.toDateString() &&
    prev.currentDate.getMonth() === next.currentDate.getMonth() &&
    prev.dayEvents.length === next.dayEvents.length &&
    JSON.stringify(prev.dayEvents) === JSON.stringify(next.dayEvents)
  );
});

DayCell.displayName = "DayCell";
