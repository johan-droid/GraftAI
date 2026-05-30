import { useQuery } from "@tanstack/react-query";
import { getEvents, type CalendarEvent } from "@/lib/api";

export function useCalendar(currentDate: Date) {
  const startOfMonth = new Date(
    currentDate.getFullYear(),
    currentDate.getMonth(),
    1,
    0,
    0,
    0,
    0,
  ).toISOString();
  const startOfNextMonth = new Date(
    currentDate.getFullYear(),
    currentDate.getMonth() + 1,
    1,
    0,
    0,
    0,
    0,
  ).toISOString();

  const { data: events = [], isLoading, error } = useQuery<CalendarEvent[]>({
    queryKey: ["calendar-events", currentDate.getFullYear(), currentDate.getMonth()],
    queryFn: () => getEvents(startOfMonth, startOfNextMonth),
    initialData: [],
  });

  return {
    events,
    isLoading,
    error,
  };
}
