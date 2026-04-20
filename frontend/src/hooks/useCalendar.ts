import { useQuery } from "@tanstack/react-query";
import { enhancedApiClient } from "@/lib/api-client-enhanced";
import { Booking } from "@/types/api";

export function useCalendar(currentDate: Date) {
  const startOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1).toISOString();
  const endOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0).toISOString();

  const { data: bookings = [], isLoading, error } = useQuery<Booking[]>({
    queryKey: ["bookings", currentDate.getFullYear(), currentDate.getMonth()],
    queryFn: () =>
      enhancedApiClient.get<Booking[]>("/bookings", {
        params: {
          start_date: startOfMonth,
          end_date: endOfMonth,
        },
      }),
    initialData: [],
  });

  return {
    bookings,
    isLoading,
    error,
  };
}
