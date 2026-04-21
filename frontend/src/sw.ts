import { defaultCache } from "@serwist/next/worker";
import type { PrecacheEntry, SerwistGlobalConfig } from "serwist";
import { Serwist } from "serwist";

declare global {
  interface ServiceWorkerGlobalScope extends SerwistGlobalConfig {
    __SW_MANIFEST: (string | PrecacheEntry)[] | undefined;
    addEventListener(type: string, listener: (event: any) => void): void;
    skipWaiting(): void;
    clients: {
      claim(): Promise<void>;
    };
  }
  interface ExtendableEvent extends Event {
    waitUntil(fn: Promise<any>): void;
  }
  interface FetchEvent extends ExtendableEvent {
    request: Request;
    respondWith(response: Promise<Response> | Response): void;
    stopImmediatePropagation(): void;
  }
}

declare const self: ServiceWorkerGlobalScope;

// Force immediate activation to kick out the old broken worker.
self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event: ExtendableEvent) => {
  event.waitUntil(self.clients.claim());
});

// EXTREMELY IMPORTANT: Completely bypass the Service Worker for API routes.
// This prevents cross-origin OAuth redirects from throwing opaque response errors.
self.addEventListener("fetch", (event: FetchEvent) => {
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/api/")) {
    event.stopImmediatePropagation();
    event.respondWith(fetch(event.request));
    return;
  }
});

const normalizePrecacheEntries = (
  entries: (string | PrecacheEntry)[] | undefined,
): (string | PrecacheEntry)[] | undefined => {
  if (!entries) {
    return entries;
  }

  return entries.map((entry) => {
    if (typeof entry === "string") {
      return entry.replace(/\\/g, "/");
    }

    return {
      ...entry,
      url: entry.url?.replace(/\\/g, "/"),
    };
  });
};

const serwist = new Serwist({
  precacheEntries: normalizePrecacheEntries(self.__SW_MANIFEST),
  skipWaiting: true,
  clientsClaim: true,
  navigationPreload: true,
  precacheOptions: {
    cleanupOutdatedCaches: true,
  },
  runtimeCaching: defaultCache,
});

serwist.addEventListeners();
