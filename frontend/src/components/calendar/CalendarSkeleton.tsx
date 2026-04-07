import React from "react";

const CalendarSkeleton = () => {
  return (
    <div className="flex flex-col h-full animate-fade-in">
      {/* Header Skeleton */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.06] bg-[#040a18]/40">
        <div className="flex items-center gap-4">
          <div className="w-40 h-8 rounded-xl bg-white/5 animate-pulse" />
          <div className="flex gap-1">
            <div className="w-10 h-10 rounded-lg bg-white/5 animate-pulse" />
            <div className="w-10 h-10 rounded-lg bg-white/5 animate-pulse" />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-24 h-10 rounded-xl bg-white/5 animate-pulse" />
          <div className="w-32 h-10 rounded-xl bg-indigo-500/20 animate-pulse" />
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Main Grid Skeleton */}
        <div className="flex-1 overflow-auto bg-[#030712]">
          <div className="grid grid-cols-7 border-b border-white/[0.06]">
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
              <div key={day} className="py-3 text-center border-r border-white/[0.06]">
                <div className="w-8 h-3 mx-auto rounded bg-white/5 animate-pulse" />
              </div>
            ))}
          </div>

          <div className="grid grid-cols-7 grid-rows-6 h-[calc(100%-41px)] min-h-[600px]">
            {Array.from({ length: 42 }).map((_, i) => (
              <div
                key={i}
                className="relative border-r border-b border-white/[0.04] p-2 space-y-1"
              >
                <div className="w-6 h-6 rounded bg-white/5 animate-pulse mb-2" />
                {i % 5 === 0 && (
                  <div className="w-full h-8 rounded-lg bg-indigo-500/10 animate-pulse" />
                )}
                {i % 7 === 2 && (
                  <div className="w-4/5 h-8 rounded-lg bg-emerald-500/10 animate-pulse" />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Sidebar Skeleton */}
        <div className="hidden xl:flex w-72 flex-col border-l border-white/[0.06] bg-[#040a18]/20 p-6 space-y-8">
          <div className="space-y-4">
            <div className="w-24 h-4 rounded bg-white/5 animate-pulse" />
            <div className="space-y-2">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="w-full h-12 rounded-xl bg-white/5 animate-pulse" />
              ))}
            </div>
          </div>
          <div className="space-y-4">
            <div className="w-32 h-4 rounded bg-white/5 animate-pulse" />
            <div className="grid grid-cols-2 gap-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-20 rounded-2xl bg-white/5 animate-pulse" />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CalendarSkeleton;
