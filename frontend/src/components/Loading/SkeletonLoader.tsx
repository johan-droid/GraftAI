/**
 * Skeleton Loading Components
 * 
- Mobile-first responsive skeletons
- Shimmer gradient effects
- Content-aware layouts
 */

'use client';

import { motion } from 'framer-motion';

// Base shimmer animation wrapper
const ShimmerWrapper = ({ children, className = '' }: { children?: React.ReactNode; className?: string }) => (
  <div className={`relative overflow-hidden ${className}`}>
    {children}
    <motion.div
      className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
      animate={{ x: ['-100%', '100%'] }}
      transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
    />
  </div>
);

// Dashboard Card Skeleton
export function DashboardCardSkeleton() {
  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-4 sm:p-6 border border-slate-700/50">
      <div className="flex items-start justify-between mb-4">
        <ShimmerWrapper className="w-12 h-12 rounded-xl bg-slate-700" />
        <ShimmerWrapper className="w-20 h-6 rounded-lg bg-slate-700" />
      </div>
      <ShimmerWrapper className="w-3/4 h-8 rounded-lg bg-slate-700 mb-2" />
      <ShimmerWrapper className="w-1/2 h-4 rounded-lg bg-slate-700" />
    </div>
  );
}

// Event List Item Skeleton
export function EventItemSkeleton() {
  return (
    <div className="flex items-center gap-3 sm:gap-4 p-3 sm:p-4 bg-slate-800/30 rounded-xl border border-slate-700/30">
      <ShimmerWrapper className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-slate-700 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <ShimmerWrapper className="w-3/4 h-5 rounded-lg bg-slate-700 mb-2" />
        <ShimmerWrapper className="w-1/2 h-3 rounded-lg bg-slate-700" />
      </div>
      <ShimmerWrapper className="w-16 h-8 rounded-lg bg-slate-700 flex-shrink-0 hidden sm:block" />
    </div>
  );
}

// Calendar Day Skeleton
export function CalendarDaySkeleton() {
  return (
    <div className="bg-slate-800/30 rounded-xl p-3 sm:p-4 border border-slate-700/30">
      <ShimmerWrapper className="w-20 h-4 rounded-lg bg-slate-700 mb-3" />
      <div className="space-y-2">
        <ShimmerWrapper className="w-full h-8 rounded-lg bg-slate-700" />
        <ShimmerWrapper className="w-full h-8 rounded-lg bg-slate-700" />
        <ShimmerWrapper className="w-3/4 h-8 rounded-lg bg-slate-700" />
      </div>
    </div>
  );
}

// Stats Row Skeleton
export function StatsRowSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="bg-slate-800/50 rounded-xl p-3 sm:p-4 border border-slate-700/50">
          <ShimmerWrapper className="w-8 h-8 rounded-lg bg-slate-700 mb-3" />
          <ShimmerWrapper className="w-full h-6 rounded-lg bg-slate-700 mb-2" />
          <ShimmerWrapper className="w-2/3 h-3 rounded-lg bg-slate-700" />
        </div>
      ))}
    </div>
  );
}

// Full Page Skeleton for Dashboard
export function DashboardSkeleton() {
  return (
    <div className="space-y-4 sm:space-y-6 p-4 sm:p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <ShimmerWrapper className="w-48 h-8 rounded-lg bg-slate-700" />
        <ShimmerWrapper className="w-32 h-10 rounded-xl bg-slate-700" />
      </div>

      {/* Stats */}
      <StatsRowSkeleton />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Left Column - Calendar/Events */}
        <div className="lg:col-span-2 space-y-3 sm:space-y-4">
          <ShimmerWrapper className="w-40 h-6 rounded-lg bg-slate-700" />
          {[...Array(5)].map((_, i) => (
            <EventItemSkeleton key={i} />
          ))}
        </div>

        {/* Right Column - Insights/Quick Actions */}
        <div className="space-y-3 sm:space-y-4">
          <ShimmerWrapper className="w-32 h-6 rounded-lg bg-slate-700" />
          <DashboardCardSkeleton />
          <DashboardCardSkeleton />
        </div>
      </div>
    </div>
  );
}

// Table Skeleton
export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="bg-slate-800/30 rounded-xl border border-slate-700/30 overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-4 p-4 border-b border-slate-700/30 bg-slate-800/50">
        <ShimmerWrapper className="w-8 h-4 rounded bg-slate-700" />
        <ShimmerWrapper className="w-32 h-4 rounded bg-slate-700 flex-1" />
        <ShimmerWrapper className="w-24 h-4 rounded bg-slate-700" />
        <ShimmerWrapper className="w-20 h-4 rounded bg-slate-700" />
      </div>
      
      {/* Rows */}
      {[...Array(rows)].map((_, i) => (
        <div key={i} className="flex items-center gap-4 p-4 border-b border-slate-700/20 last:border-0">
          <ShimmerWrapper className="w-8 h-4 rounded bg-slate-700" />
          <ShimmerWrapper className="w-full h-4 rounded bg-slate-700 flex-1 max-w-[200px]" />
          <ShimmerWrapper className="w-24 h-4 rounded bg-slate-700" />
          <ShimmerWrapper className="w-20 h-8 rounded-lg bg-slate-700" />
        </div>
      ))}
    </div>
  );
}

// Chat Message Skeleton
export function ChatMessageSkeleton({ isUser = false }: { isUser?: boolean }) {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] sm:max-w-[70%] rounded-2xl p-3 sm:p-4 ${isUser ? 'bg-blue-600' : 'bg-slate-800'}`}>
        <ShimmerWrapper className={`w-full h-4 rounded mb-2 ${isUser ? 'bg-blue-500' : 'bg-slate-700'}`} />
        <ShimmerWrapper className={`w-2/3 h-4 rounded ${isUser ? 'bg-blue-500' : 'bg-slate-700'}`} />
      </div>
    </div>
  );
}

// Form Input Skeleton
export function FormSkeleton({ fields = 4 }: { fields?: number }) {
  return (
    <div className="space-y-4">
      {[...Array(fields)].map((_, i) => (
        <div key={i}>
          <ShimmerWrapper className="w-24 h-4 rounded bg-slate-700 mb-2" />
          <ShimmerWrapper className="w-full h-10 sm:h-12 rounded-xl bg-slate-700" />
        </div>
      ))}
      <ShimmerWrapper className="w-full h-12 rounded-xl bg-slate-700 mt-6" />
    </div>
  );
}
