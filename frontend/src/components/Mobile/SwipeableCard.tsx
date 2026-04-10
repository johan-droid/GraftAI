/**
 * Swipeable Card Component
 * 
- Swipe gestures for quick actions
- Reveal actions underneath
- Smooth spring animations
 */

'use client';

import { useState } from 'react';
import { motion, useMotionValue, useTransform, PanInfo } from 'framer-motion';
import { Trash2, Edit, Check } from 'lucide-react';

interface SwipeableCardProps {
  children: React.ReactNode;
  onDelete?: () => void;
  onEdit?: () => void;
  onComplete?: () => void;
}

export default function SwipeableCard({
  children,
  onDelete,
  onEdit,
  onComplete,
}: SwipeableCardProps) {
  const [isOpen, setIsOpen] = useState(false);
  const x = useMotionValue(0);
  
  const opacityLeft = useTransform(x, [-100, -50, 0], [1, 0.5, 0]);
  const opacityRight = useTransform(x, [0, 50, 100], [0, 0.5, 1]);
  const scaleLeft = useTransform(x, [-100, -50, 0], [1, 0.8, 0]);
  const scaleRight = useTransform(x, [0, 50, 100], [0, 0.8, 1]);

  const handleDragEnd = (event: any, info: PanInfo) => {
    const threshold = 80;
    
    if (info.offset.x < -threshold && onDelete) {
      onDelete();
    } else if (info.offset.x > threshold && onComplete) {
      onComplete();
    }
    
    setIsOpen(Math.abs(info.offset.x) > threshold / 2);
  };

  return (
    <div className="relative overflow-hidden rounded-xl">
      {/* Background Actions */}
      <div className="absolute inset-0 flex">
        {/* Left Action (Delete) */}
        {onDelete && (
          <motion.div
            style={{ opacity: opacityLeft, scale: scaleLeft }}
            className="flex-1 bg-red-500 flex items-center justify-start pl-4"
          >
            <div className="flex flex-col items-center text-white">
              <Trash2 className="w-6 h-6 mb-1" />
              <span className="text-xs font-medium">Delete</span>
            </div>
          </motion.div>
        )}
        
        {/* Spacer */}
        <div className="flex-[2]" />
        
        {/* Right Actions */}
        <div className="flex-1 flex">
          {onEdit && (
            <motion.div
              style={{ opacity: opacityRight, scale: scaleRight }}
              className="flex-1 bg-blue-500 flex items-center justify-center"
            >
              <div className="flex flex-col items-center text-white">
                <Edit className="w-5 h-5 mb-1" />
                <span className="text-xs font-medium">Edit</span>
              </div>
            </motion.div>
          )}
          {onComplete && (
            <motion.div
              style={{ opacity: opacityRight, scale: scaleRight }}
              className="flex-1 bg-green-500 flex items-center justify-end pr-4"
            >
              <div className="flex flex-col items-center text-white">
                <Check className="w-6 h-6 mb-1" />
                <span className="text-xs font-medium">Done</span>
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* Foreground Card */}
      <motion.div
        drag="x"
        dragConstraints={{ left: onDelete ? -150 : 0, right: (onEdit || onComplete) ? 150 : 0 }}
        dragElastic={0.1}
        onDragEnd={handleDragEnd}
        style={{ x }}
        animate={{ x: isOpen ? (x.get() > 0 ? 100 : -100) : 0 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="relative bg-slate-800/50 backdrop-blur-sm border border-slate-700/50"
      >
        {children}
      </motion.div>
    </div>
  );
}
