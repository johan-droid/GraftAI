import { useState, useEffect } from "react";
import { getToken } from "@/lib/auth-client";

export type SyncStatus = "idle" | "syncing" | "no_integrations" | "error" | "connected";

interface SyncEvent {
  status: SyncStatus;
  message?: string;
  lastSyncAt?: string;
}

export function useSyncStatus() {
  const [status, setStatus] = useState<SyncStatus>("idle");
  const [message, setMessage] = useState<string>("");
  const [lastSyncAt, setLastSyncAt] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;

    let baseUrl = "";
    if (typeof window === "undefined") {
      baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
    }
    const url = new URL("/api/v1/calendar/sync/stream", baseUrl || window.location.origin);
    url.searchParams.set("token", token); // Fallback for browsers rejecting EventSource with credentials

    const eventSource = new EventSource(url.toString());

    eventSource.onmessage = (event) => {
      try {
        const data: SyncEvent = JSON.parse(event.data);
        if (data.status) {
          setStatus(data.status);
        }
        if (data.message) {
          setMessage(data.message);
        }
        if (data.status === "idle") {
          setLastSyncAt(new Date().toISOString());
        }
      } catch (e) {
        console.error("Failed to parse sync event:", e);
      }
    };

    eventSource.onerror = (err) => {
      console.error("Sync SSE Stream error:", err);
      setStatus("error");
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  return { status, message, lastSyncAt, isSyncing: status === "syncing" };
}
