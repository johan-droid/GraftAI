"use client";

import { Loader2, ArrowRight } from "lucide-react";
import { motion, HTMLMotionProps } from "framer-motion";

interface AuthButtonProps extends HTMLMotionProps<"button"> {
  label: string;
  loading?: boolean;
  variant?: "primary" | "secondary";
}

export default function AuthButton({ label, loading, variant = "primary", className, ...props }: AuthButtonProps) {
  const isPrimary = variant === "primary";

  return (
    <motion.button
      whileHover={{ scale: 1.01, translateY: -1 }}
      whileTap={{ scale: 0.99 }}
      className={`
        relative w-full h-11 rounded-xl font-semibold text-[11px] uppercase tracking-[0.2em] 
        flex items-center justify-center gap-3 transition-all duration-200
        ${isPrimary 
          ? "bg-[#0066FF] text-white shadow-lg shadow-[#0066FF]/20 hover:bg-[#0066FF]/90" 
          : "bg-white/5 text-slate-400 border border-white/5 hover:bg-white/10 hover:text-white"
        }
        disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden group ${className || ""}
      `}
      {...props}
      disabled={loading || props.disabled}
    >
      {/* Gloss Highlight Layer */}
      <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity" />
      
      {loading ? (
        <Loader2 className="w-5 h-5 animate-spin" />
      ) : (
        <>
          {label}
          {isPrimary && <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />}
        </>
      )}
    </motion.button>
  );
}
