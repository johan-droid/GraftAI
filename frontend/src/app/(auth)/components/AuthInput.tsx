"use client";

import { useState } from "react";
import { Eye, EyeOff, LucideIcon } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface AuthInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  icon: LucideIcon;
  error?: string;
  showToggle?: boolean;
}

export default function AuthInput({ label, icon: Icon, error, showToggle, type, ...props }: AuthInputProps) {
  const [showPassword, setShowPassword] = useState(false);
  const inputType = showToggle ? (showPassword ? "text" : "password") : type;

  return (
    <div className="space-y-1.5 group">
      <div className="flex justify-between items-center px-0.5">
        <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">{label}</label>
      </div>
      
      <div className="relative">
        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-[#0066FF] transition-colors">
          <Icon className="w-4 h-4" />
        </div>
        
        <input
          {...props}
          type={inputType}
          className={`
            w-full h-12 bg-white/5 border rounded-xl pl-12 pr-12 text-sm font-medium text-white placeholder:text-slate-700
            transition-all duration-200 outline-none
            ${error ? "border-rose-500/50" : "border-white/5 focus:border-[#0066FF]/50 focus:bg-white/[0.07]"}
          `}
        />

        {showToggle && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white transition-colors p-1"
          >
            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        )}
      </div>

      <AnimatePresence>
        {error && (
          <motion.p 
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            className="text-xs font-bold text-rose-500 ml-1 flex items-center gap-2"
          >
            <span className="w-1 h-1 rounded-full bg-rose-500 shrink-0" />
            {error}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
}
