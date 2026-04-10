/**
 * Pull to Refresh Component
 * 
- Native-like pull-to-refresh for mobile
- Smooth elastic animation
- Progress indicator
 */

'use client';

import { useState, useRef, useCallback } from 'react';
import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import { RefreshCw } from 'lucide-react';

interface PullToRefreshProps {
  onRefresh: () => Promise<void>;
  children: React.ReactNode;
}

export default function PullToRefresh({ onRefresh, children }: PullToRefreshProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [pullProgress, setPullProgress] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const startY = useRef(0);
  const currentY = useRef(0);

  const y = useMotionValue(0);
  const rotate = useTransform(y, [0, 100], [0, 360]);
  const opacity = useTransform(y, [0, 50, 100], [0, 1, 1]);

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (window.scrollY === 0) {
      startY.current = e.touches[0].clientY;
    }
  }, []);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (window.scrollY === 0 && !isRefreshing) {
      currentY.current = e.touches[0].clientY;
      const diff = currentY.current - startY.current;
      
      if (diff > 0) {
        const progress = Math.min(diff / 150, 1);
        setPullProgress(progress);
        y.set(diff * 0.5);
      }
    }
  }, [isRefreshing, y]);

  const handleTouchEnd = useCallback(async () => {
    if (pullProgress >= 1 && !isRefreshing) {
      setIsRefreshing(true);
      y.set(80);
      
      try {
        await onRefresh();
      } finally {
        setIsRefreshing(false);
        setPullProgress(0);
        animate(y, 0, { type: 'spring', stiffness: 300, damping: 30 });
      }
    } else {
      setPullProgress(0);
      animate(y, 0, { type: 'spring', stiffness: 300, damping: 30 });
    }
  }, [pullProgress, isRefreshing, onRefresh, y]);

  return (
    <div
      ref={containerRef}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      className="relative touch-pan-y"
    >
      {/* Pull Indicator */}
      <motion.div
        style={{ y, opacity }}
        className="absolute top-0 left-0 right-0 z-10 flex items-center justify-center pt-4 pointer-events-none"
      >
        <motion.div
          style={{ rotate: isRefreshing ? undefined : rotate }}
          animate={isRefreshing ? { rotate: 360 } : {}}
          transition={isRefreshing ? { duration: 1, repeat: Infinity, ease: 'linear' } : {}}
          className="w-10 h-10 rounded-full bg-slate-800/90 backdrop-blur-sm border border-slate-700/50 flex items-center justify-center shadow-lg"
        >
          <RefreshCw className="w-5 h-5 text-blue-400" />
        </motion.div>
      </motion.div>

      {/* Progress Bar */}
      <motion.div
        className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-purple-500 z-20"
        initial={{ scaleX: 0 }}
        animate={{ scaleX: pullProgress }}
        style={{ transformOrigin: 'left' }}
      />

      {/* Content */}
      <motion.div style={{ y }}>
        {children}
      </motion.div>
    </div>
  );
}
