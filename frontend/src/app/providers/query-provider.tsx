"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 1000 * 60 * 10, // Keep data fresh for 10 minutes
            cacheTime: 1000 * 60 * 30, // Cache data for 30 minutes across views
            gcTime: 1000 * 60 * 15, // Release unused queries after 15 minutes
            refetchOnWindowFocus: true,
            refetchOnReconnect: true,
            refetchOnMount: false,
            retry: 1, // Only retry failed requests once for queries
            retryDelay: (attemptIndex: number) => Math.min(1000 * 2 ** attemptIndex, 30000),
          } as any,
          mutations: {
            retry: 0, // Disable retries by default for non-idempotent mutations.
          } as any,
        } as any,
      })
  );

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
