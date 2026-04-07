import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface DayCellProps {
  day: Date;
  today: Date;
  currentDate: Date;
  selectedDate: Date | null;
  dayEvents: any[];
  onSelect: (day: Date) => void;
  categories: any;
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
        "relative flex flex-col p-2 rounded-xl cursor-pointer min-h-[80px] md:min-h-[100px] transition-all border",
        isSelected
          ? "border-indigo-500/60 bg-indigo-600/10"
          : isCurrentMonth
          ? "border-white/[0.05] bg-white/[0.02] hover:border-white/10 hover:bg-white/[0.04]"
          : "border-transparent opacity-30 cursor-default"
      )}
    >
      <div
        className={cn(
          "w-7 h-7 rounded-full flex items-center justify-center text-sm font-semibold mb-1 self-center",
          isToday ? "bg-indigo-600 text-white" : isSelected ? "text-indigo-300" : "text-slate-400"
        )}
      >
        {day.getDate()}
      </div>

      <div className="space-y-0.5 flex-1">
        {dayEvents.slice(0, 2).map((ev) => (
          <div
            key={ev.id}
            className={cn(
              "text-[10px] font-medium px-1.5 py-0.5 rounded-md truncate border",
              categories[ev.category]?.bg ?? "bg-slate-500/10 border-slate-500/20",
              categories[ev.category]?.text ?? "text-slate-300"
            )}
          >
            {ev.title}
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
