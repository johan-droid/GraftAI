import React from 'react';
import { motion } from 'framer-motion';

interface UsageProgressProps {
  label: string;
  current: number;
  limit: number;
  unit?: string;
  color?: string;
}

export const UsageProgress: React.FC<UsageProgressProps> = ({ 
  label, 
  current, 
  limit, 
  unit = "", 
  color = "bg-indigo-500" 
}) => {
  const percentage = Math.min(100, (current / limit) * 100);
  const isHigh = percentage > 80;
  const isCritical = percentage >= 100;

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-end">
        <div>
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-500">{label}</p>
          <p className="text-sm font-bold text-white">
            {current.toLocaleString()} <span className="text-slate-500 font-medium text-xs">/ {limit.toLocaleString()} {unit}</span>
          </p>
        </div>
        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${isCritical ? 'text-red-400 bg-red-400/10' : isHigh ? 'text-amber-400 bg-amber-400/10' : 'text-slate-400 bg-white/5'}`}>
          {percentage.toFixed(0)}%
        </span>
      </div>
      <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden border border-white/[0.03]">
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
          className={`h-full rounded-full ${isCritical ? 'bg-red-500' : isHigh ? 'bg-amber-500' : color}`}
        />
      </div>
    </div>
  );
};
