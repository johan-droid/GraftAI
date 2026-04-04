"use client";

import React from "react";
import { useNotification } from "@/hooks/use-notification";
import { motion } from "framer-motion";
import { Sparkles, RefreshCw, CheckCircle, AlertTriangle } from "lucide-react";

export default function DebugNotificationsPage() {
  const { notify, ping } = useNotification();

  return (
    <div className="container mx-auto px-6 py-24 min-h-screen flex flex-col items-center justify-center gap-12">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-4xl font-black tracking-tighter sm:text-6xl mb-4 bg-clip-text text-transparent bg-gradient-to-r from-white via-white/80 to-white/50">
          Smart Observability
        </h1>
        <p className="text-slate-400 max-w-md mx-auto text-sm sm:text-base">
          Testing the pinpoint accuracy of our glassmorphic HUD and human-centric notification engine.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-2xl">
        <button
          onClick={() => notify("System Perfect", "All background synchronizations are green.", "success")}
          className="p-6 rounded-3xl bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/20 transition-all flex flex-col items-center gap-3 group"
        >
          <CheckCircle className="w-8 h-8 text-emerald-400 group-hover:scale-110 transition-transform" />
          <span className="text-xs font-bold uppercase tracking-widest text-emerald-400">Trigger Success</span>
        </button>

        <button
          onClick={() => notify("Sync Interrupted", "Neural linkage lost in Sector 7G.", "error")}
          className="p-6 rounded-3xl bg-rose-500/10 border border-rose-500/20 hover:bg-rose-500/20 transition-all flex flex-col items-center gap-3 group"
        >
          <AlertTriangle className="w-8 h-8 text-rose-400 group-hover:scale-110 transition-transform" />
          <span className="text-xs font-bold uppercase tracking-widest text-rose-400">Trigger Error</span>
        </button>

        <button
          onClick={() => {
            ping("syncing");
            notify("Resync Initiated", "Querying the interstellar calendar graph...", "info");
          }}
          className="p-6 rounded-3xl bg-sky-500/10 border border-sky-500/20 hover:bg-sky-500/20 transition-all flex flex-col items-center gap-3 group"
        >
          <RefreshCw className="w-8 h-8 text-sky-400 group-hover:rotate-180 transition-transform duration-500" />
          <span className="text-xs font-bold uppercase tracking-widest text-sky-400">Start Sync (Ping)</span>
        </button>

        <button
          onClick={() => {
            ping("completed");
            notify("Universe Synchronized", "All temporal anomalies resolved.", "success");
          }}
          className="p-6 rounded-3xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all flex flex-col items-center gap-3 group"
        >
          <Sparkles className="w-8 h-8 text-white group-hover:scale-125 transition-transform" />
          <span className="text-xs font-bold uppercase tracking-widest text-white">Complete Sync (Ping)</span>
        </button>
      </div>
    </div>
  );
}
