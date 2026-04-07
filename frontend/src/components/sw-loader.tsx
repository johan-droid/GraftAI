"use client";

import { useEffect } from "react";

export default function ServiceWorkerLoader() {
  useEffect(() => {
    if (typeof window !== "undefined" && "serviceWorker" in navigator) {
      const registerSW = async () => {
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
