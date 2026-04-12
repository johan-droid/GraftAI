"use client";

import { useEffect } from "react";

export default function ServiceWorkerLoader() {
  useEffect(() => {
    if (typeof window !== "undefined" && "serviceWorker" in navigator) {
      const disableSW = process.env.NEXT_PUBLIC_DISABLE_SERVICE_WORKER === "true";

      const unregisterExistingSW = async () => {
        if (navigator.serviceWorker.controller) {
          const registrations = await navigator.serviceWorker.getRegistrations();
          await Promise.all(
            registrations.map(async (registration) => {
              try {
                await registration.unregister();
              } catch (error) {
                console.warn("📦 [PWA] Failed to unregister service worker:", error);
              }
            })
          );
        }
      };

      const registerSW = async () => {
        if (disableSW) {
          await unregisterExistingSW();
          console.log("📦 [PWA] Service worker disabled by NEXT_PUBLIC_DISABLE_SERVICE_WORKER");
          return;
        }

        try {
          const registration = await navigator.serviceWorker.register("/sw.js", {
            scope: "/",
          });
          
          if (registration.installing) {
            console.log("📦 [PWA] Service worker installing...");
          } else if (registration.waiting) {
            console.log("📦 [PWA] Service worker installed!");
          } else if (registration.active) {
            console.log("📦 [PWA] Service worker active!");
          }
        } catch (error) {
          console.error("📦 [PWA] Service worker registration failed:", error);
        }
      };

      void registerSW();
    }
  }, []);

  return null;
}
