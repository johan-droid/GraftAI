"use client";

import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, AlertCircle, Loader2, RefreshCcw } from "lucide-react";

interface SyncStatusProps {
  status: "idle" | "syncing" | "success" | "error";
  onSync?: () => void;
}

export function SyncStatus({ status, onSync }: SyncStatusProps) {
  return (
    <AnimatePresence mode="wait">
      {status === "syncing" && (
        <motion.div
          key="syncing"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          className="flex items-center gap-2 bg-blue-50 text-blue-700 px-4 py-2 rounded-xl border border-blue-200"
        >
          <Loader2 className="w-4 h-4 animate-spin" />
          <span className="text-sm font-semibold">Syncing calendars...</span>
        </motion.div>
      )}

      {status === "success" && (
        <motion.div
          key="success"
          initial={{ opacity: 0, scale: 0.9, y: -10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: -10 }}
          className="flex items-center gap-2 bg-emerald-50 text-emerald-700 px-4 py-2 rounded-xl border border-emerald-200"
        >
          <motion.span
            initial={{ scale: 0.7, rotate: -12 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: "spring", damping: 14, stiffness: 280 }}
            className="inline-flex"
          >
            <CheckCircle2 className="w-4 h-4" />
          </motion.span>
          <span className="text-sm font-semibold">Sync complete!</span>
        </motion.div>
      )}

      {status === "error" && (
        <motion.div
          key="error"
          initial={{ opacity: 0, scale: 0.9, y: -10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: -10 }}
          className="flex items-center gap-2 bg-red-50 text-red-700 px-4 py-2 rounded-xl border border-red-200"
        >
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm font-semibold">Sync failed</span>
          {onSync && (
            <button
              onClick={onSync}
              className="ml-2 text-xs underline hover:no-underline"
            >
              Retry
            </button>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Compact version for mobile
export function SyncStatusCompact({ status }: { status: "idle" | "syncing" | "success" | "error" }) {
  return (
    <AnimatePresence mode="wait">
      {status === "syncing" && (
        <motion.div
          key="syncing"
          initial={{ opacity: 0, rotate: 0 }}
          animate={{ opacity: 1, rotate: 360 }}
          exit={{ opacity: 0 }}
          transition={{ rotate: { duration: 1, repeat: Infinity, ease: "linear" } }}
        >
          <RefreshCcw className="w-4 h-4 text-blue-600" />
        </motion.div>
      )}

      {status === "success" && (
        <motion.div
          key="success"
          initial={{ opacity: 0, scale: 0.6, rotate: -10 }}
          animate={{ opacity: 1, scale: 1, rotate: 0 }}
          exit={{ opacity: 0, scale: 0, rotate: 10 }}
          transition={{ type: "spring", damping: 14, stiffness: 280 }}
        >
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
        </motion.div>
      )}

      {status === "error" && (
        <motion.div
          key="error"
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0 }}
        >
          <AlertCircle className="w-4 h-4 text-red-600" />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
