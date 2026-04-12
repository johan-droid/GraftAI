import { defaultCache } from "@serwist/next/worker";
import type { PrecacheEntry, SerwistGlobalConfig } from "serwist";
import { Serwist } from "serwist";

declare global {
  interface ServiceWorkerGlobalScope extends SerwistGlobalConfig {
    __SW_MANIFEST: (string | PrecacheEntry)[] | undefined;
  }
}

declare const self: ServiceWorkerGlobalScope;

// EXTREMELY IMPORTANT: Completely bypass the Service Worker for API routes.
// This prevents cross-origin OAuth redirects from throwing opaque response errors.
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/api/")) {
    event.stopImmediatePropagation();
    return;
  }
});

const serwist = new Serwist({
  // Disable precaching temporarily to bypass 404 installation errors
  precacheEntries: [],
  skipWaiting: true,
  clientsClaim: true,
  navigationPreload: true,
  precacheOptions: {
    cleanupOutdatedCaches: true,
  },
  runtimeCaching: defaultCache,
});

serwist.addEventListeners();
