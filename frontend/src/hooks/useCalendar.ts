import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Booking } from "@/types/api";

export function useCalendar(currentDate: Date) {
  const startOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1).toISOString();
  const endOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0).toISOString();

  const { data: bookings = [], isLoading, error } = useQuery<Booking[]>({
    queryKey: ["bookings", currentDate.getFullYear(), currentDate.getMonth()],
    queryFn: () =>
      apiClient.get<Booking[]>("/bookings", {
        start_date: startOfMonth,
        end_date: endOfMonth,
      }),
    initialData: [],
  });

  return {
    bookings,
    isLoading,
    error,
  };
}
