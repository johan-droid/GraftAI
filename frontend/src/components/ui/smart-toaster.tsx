"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  CheckCircle2, 
  AlertCircle, 
  Info, 
  XCircle, 
  X,
  Bell
} from "lucide-react";
import { useNotificationContext } from "@/providers/notification-provider";
import { Notification, NotificationType } from "@/types/notifications";
import { cn } from "@/lib/utils";

const icons: Record<NotificationType, React.ReactNode> = {
  success: <CheckCircle2 className="w-5 h-5 text-emerald-400" />,
  error: <XCircle className="w-5 h-5 text-rose-400" />,
  warning: <AlertCircle className="w-5 h-5 text-amber-400" />,
  info: <Info className="w-5 h-5 text-sky-400" />,
};

const SmartToaster = () => {
  const { notifications, removeNotification } = useNotificationContext();

  return (
    <div className="fixed bottom-6 right-6 z-[200] flex flex-col gap-3 pointer-events-none max-w-[min(calc(100vw-3rem),24rem)]">
      <AnimatePresence mode="popLayout">
        {notifications.map((notification, index) => (
          <ToastItem 
            key={notification.id} 
            notification={notification} 
            index={index}
            onDismiss={() => removeNotification(notification.id)} 
          />
        ))}
      </AnimatePresence>
    </div>
  );
};

const ToastItem = ({ 
  notification, 
  onDismiss,
  index 
}: { 
  notification: Notification; 
  onDismiss: () => void;
  index: number;
}) => {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20, scale: 0.9, filter: "blur(10px)" }}
      animate={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
      exit={{ opacity: 0, scale: 0.8, filter: "blur(10px)", transition: { duration: 0.2 } }}
      transition={{ 
        type: "spring", 
        stiffness: 150, 
        damping: 20,
        delay: index * 0.05 
      }}
      drag="x"
      dragConstraints={{ left: 0, right: 300 }}
      dragElastic={{ left: 0, right: 0.5 }}
      onDragEnd={(_, info) => {
        if (info.offset.x > 100) onDismiss();
      }}
      className={cn(
        "pointer-events-auto relative overflow-hidden",
        "bg-slate-900/70 backdrop-blur-xl border border-white/10 shadow-2xl rounded-2xl",
        "p-4 flex items-start gap-3 group select-none"
      )}
    >
      {/* Progress Bar (Auto-dismiss timer) */}
      {notification.duration !== Infinity && (
        <motion.div 
          initial={{ scaleX: 1 }}
          animate={{ scaleX: 0 }}
          transition={{ duration: (notification.duration || 5000) / 1000, ease: "linear" }}
          className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary/30 origin-left"
        />
      )}

      {/* Icon Wrapper */}
      <div className="mt-0.5 shrink-0">
        {icons[notification.type]}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 pr-4">
        <h4 className="text-sm font-bold text-slate-50 truncate">
          {notification.title}
        </h4>
        {notification.message && (
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            {notification.message}
          </p>
        )}
      </div>

      {/* Dismiss Button */}
      <button 
        onClick={onDismiss}
        className="shrink-0 p-1 rounded-full text-slate-500 hover:text-slate-200 hover:bg-white/5 transition-colors"
      >
        <X className="w-4 h-4" />
      </button>

      {/* Subtle Haptic Pulse Overlay */}
      <motion.div
        initial={{ opacity: 0, scale: 1 }}
        animate={{ opacity: [0, 0.4, 0], scale: [1, 1.05, 1] }}
        transition={{ duration: 0.5 }}
        className="absolute inset-0 bg-primary/5 pointer-events-none"
      />
    </motion.div>
  );
};

export default SmartToaster;
