'use client';

import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { normalizeWebSocketUrl } from '@/lib/ai-api';

interface TelemetryEvent {
  type: string;
  timestamp: string;
  data?: any;
}

const FLOW_PATHS = [
  "M 0 50 Q 25 50 50 50 T 100 50", // Center
  "M 0 50 Q 25 20 50 20 T 100 50", // Top Curve
  "M 0 50 Q 25 80 50 80 T 100 50", // Bottom Curve
];

export const TimeEngineAnimation: React.FC = () => {
  const [pulses, setPulses] = useState<{ id: number; path: number; color: string }[]>([]);
  const pulseIdRef = useRef(0);
  const wsRef = useRef<WebSocket | null>(null);

  const addPulse = (color: string = "var(--primary)") => {
    const id = pulseIdRef.current++;
    const path = Math.floor(Math.random() * FLOW_PATHS.length);
    setPulses(prev => [...prev, { id, path, color }]);
    
    // Remove pulse after animation finish (approx 3s)
    setTimeout(() => {
      setPulses(prev => prev.filter(p => p.id !== id));
    }, 3000);
  };

  useEffect(() => {
    // 1. Establish WebSocket Connection
    const wsUrl = normalizeWebSocketUrl(
      process.env.NEXT_PUBLIC_WS_URL || process.env.NEXT_PUBLIC_API_URL || "https://graftai.onrender.com"
    );

    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          // React to activity
          if (data.active_automations > 0 || data.recent_automations?.length > 0) {
            addPulse("var(--secondary)"); // Cyan for real activity
          }
        };

        ws.onclose = () => {
          console.log("Telemetry WebSocket disconnected. Retrying in 5s...");
          setTimeout(connect, 5000);
        };
      } catch (err) {
        console.error("Failed to connect to telemetry:", err);
      }
    };

    connect();

    // 2. Heartbeat Mechanism (Mock activity for vibrancy)
    const heartbeat = setInterval(() => {
      addPulse(); // Default Neon Green for heartbeat
    }, 2500);

    return () => {
      wsRef.current?.close();
      clearInterval(heartbeat);
    };
  }, []);

  return (
    <div className="absolute inset-0 pointer-events-none opacity-40 overflow-hidden">
      <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
        {/* Background static paths */}
        {FLOW_PATHS.map((d, i) => (
          <path
            key={i}
            d={d}
            fill="none"
            stroke="var(--border-subtle)"
            strokeWidth="0.1"
            vectorEffect="non-scaling-stroke"
          />
        ))}

        {/* Dynamic Pulses */}
        <AnimatePresence>
          {pulses.map(pulse => (
            <motion.path
              key={pulse.id}
              d={FLOW_PATHS[pulse.path]}
              fill="none"
              stroke={pulse.color}
              strokeWidth="0.5"
              strokeLinecap="round"
              vectorEffect="non-scaling-stroke"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ 
                pathLength: [0, 0.2, 0.2, 0],
                pathOffset: [0, 1],
                opacity: [0, 1, 1, 0]
              }}
              transition={{ 
                duration: 3, 
                ease: "linear",
              }}
            />
          ))}
        </AnimatePresence>

        {/* Nodes */}
        <circle cx="0" cy="50" r="1" fill="var(--primary)" />
        <circle cx="100" cy="50" r="1" fill="var(--secondary)" />
        <circle cx="50" cy="50" r="0.8" fill="var(--accent)" className="animate-pulse" />
      </svg>
      
      {/* Precision overlays */}
      <div className="absolute top-4 left-4 font-mono text-[10px] text-primary/50 uppercase tracking-widest">
        Engine_Status: Active
        <br />
        Graft_Link: Stable
      </div>
    </div>
  );
};
