"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PingStatus } from "@/types/notifications";
import { cn } from "@/lib/utils";

interface PulsePingProps {
  status: PingStatus;
  className?: string;
}

const statusColors: Record<PingStatus, string> = {
  idle: "bg-slate-500/20",
  syncing: "bg-amber-400",
  completed: "bg-emerald-400",
  error: "bg-rose-400",
};

const PulsePing = ({ status, className }: PulsePingProps) => {
  return (
    <div className={cn("relative flex items-center justify-center w-3 h-3 group", className)}>
      {/* Background Glow */}
      <AnimatePresence>
        {status !== "idle" && (
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: [1, 2, 1], opacity: [0, 0.5, 0] }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ 
              duration: status === "syncing" ? 1.5 : 0.8, 
              repeat: status === "syncing" ? Infinity : 0,
              ease: "easeInOut" 
            }}
            className={cn("absolute inset-0 rounded-full blur-[2px]", statusColors[status])}
          />
        )}
      </AnimatePresence>

      {/* Main Pulse Core */}
      <motion.div
        animate={{ 
          scale: status === "syncing" ? [1, 1.2, 1] : 1,
          opacity: status === "idle" ? 0.3 : 1
        }}
        transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
        className={cn(
          "relative w-1.5 h-1.5 rounded-full transition-colors duration-300",
          statusColors[status]
        )}
      />

      {/* Tooltip Overlay (Mobile-First Tap) */}
      <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-slate-900/90 text-[10px] text-white px-2 py-1 rounded-lg border border-white/10 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
        {status === "idle" && "System Idle"}
        {status === "syncing" && "Syncing Universe..."}
        {status === "completed" && "Sync Perfect"}
        {status === "error" && "Sync Interrupted"}
      </div>
    </div>
  );
};

export default PulsePing;
