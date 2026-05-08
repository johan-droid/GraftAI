"use client"

import React, { useEffect, useRef } from "react";

declare global {
  interface Window {
    JitsiMeetExternalAPI?: any;
  }
}

type Props = {
  roomName: string;
  displayName?: string;
  onLoad?: () => void;
  parentNodeId?: string;
};

export default function JitsiWidget({
  roomName,
  displayName,
  onLoad,
  parentNodeId = "jitsi-container",
}: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!roomName) return;

    const domain = "meet.jit.si";
    const scriptId = "jitsi-external-api";

    const ensureScript = () =>
      new Promise<void>((resolve, reject) => {
        if (window.JitsiMeetExternalAPI) {
          resolve();
          return;
        }

        if (document.getElementById(scriptId)) {
          const check = setInterval(() => {
            if (window.JitsiMeetExternalAPI) {
              clearInterval(check);
              resolve();
            }
          }, 100);
          return;
        }

        const script = document.createElement("script");
        script.id = scriptId;
        script.src = "https://meet.jit.si/external_api.js";
        script.async = true;
        script.onload = () => resolve();
        script.onerror = (e) => reject(e);
        document.body.appendChild(script);
      });

    let api: any = null;

    ensureScript()
      .then(() => {
        try {
          const options = {
            roomName,
            parentNode: containerRef.current,
            userInfo: { displayName: displayName || "" },
            width: "100%",
            height: "100%",
          } as any;

          // @ts-ignore - external script runtime type
          api = new window.JitsiMeetExternalAPI(domain, options);

          if (onLoad) onLoad();
        } catch (err) {
          console.error("Jitsi init error", err);
        }
      })
      .catch((err) => {
        console.error("Failed to load Jitsi script", err);
      });

    return () => {
      try {
        if (api && typeof api.dispose === "function") api.dispose();
      } catch (e) {
        // ignore
      }
    };
  }, [roomName, displayName, onLoad]);

  return <div id={parentNodeId} ref={containerRef} style={{ width: "100%", height: "100%" }} />;
}
