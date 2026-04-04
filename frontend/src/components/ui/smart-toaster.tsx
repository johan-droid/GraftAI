"use client";

import { AnimatePresence } from "framer-motion";
import { useNotificationContext } from "@/providers/notification-provider";
import Toast from "@/components/ui/Toast";

const SmartToaster = () => {
  const { notifications, removeNotification } = useNotificationContext();

  return (
    <div className="fixed bottom-6 right-6 z-[200] flex flex-col gap-3 pointer-events-none max-w-[min(calc(100vw-3rem),28rem)]">
      <AnimatePresence mode="popLayout">
        {notifications.map((notification, index) => (
          <Toast
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

export default SmartToaster;
