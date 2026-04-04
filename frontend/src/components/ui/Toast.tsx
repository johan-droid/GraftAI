"use client";

import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, XCircle, Info, AlertTriangle, X } from "lucide-react";
import { useToastState } from "@/hooks/use-toast";

const ICONS = {
  success: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
  error: <XCircle className="w-4 h-4 text-red-400" />,
  info: <Info className="w-4 h-4 text-blue-400" />,
  warning: <AlertTriangle className="w-4 h-4 text-amber-400" />,
};

const BARS = {
  success: "bg-emerald-400",
  error: "bg-red-400",
  info: "bg-blue-400",
  warning: "bg-amber-400",
};

const BORDERS = {
  success: "border-emerald-500/20",
  error: "border-red-500/20",
  info: "border-blue-500/20",
  warning: "border-amber-500/20",
};

export function ToastContainer() {
  const { toasts, dismiss } = useToastState();

  return (
    <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map((t) => (
          <motion.div
            key={t.id}
            layout
            initial={{ opacity: 0, y: 20, scale: 0.92, filter: "blur(4px)" }}
            animate={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
            exit={{ opacity: 0, x: 60, scale: 0.88, filter: "blur(4px)" }}
            transition={{ type: "spring", stiffness: 380, damping: 30 }}
            className={`pointer-events-auto relative flex items-start gap-3 overflow-hidden rounded-2xl border bg-slate-900/95 backdrop-blur-xl px-4 py-3.5 shadow-2xl shadow-black/40 min-w-[280px] max-w-[360px] ${BORDERS[t.type]}`}
          >
            <motion.div
              className={`absolute bottom-0 left-0 h-[2px] ${BARS[t.type]}`}
              initial={{ width: "100%" }}
              animate={{ width: "0%" }}
              transition={{ duration: (t.duration ?? 3500) / 1000, ease: "linear" }}
            />

            <div className="mt-0.5 shrink-0">{ICONS[t.type]}</div>

            <p className="flex-1 text-[13px] font-medium leading-snug text-slate-200">
              {t.message}
            </p>

            <button
              onClick={() => dismiss(t.id)}
              className="shrink-0 rounded-lg p-1 text-slate-500 transition-colors hover:bg-slate-800 hover:text-slate-300"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
