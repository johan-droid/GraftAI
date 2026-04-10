"use client";

import React, { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="flex h-[100dvh] w-full overflow-hidden bg-[#080d17] text-slate-200">
      {/* Desktop Sidebar */}
      <div className="hidden lg:flex lg:w-72 lg:flex-col lg:border-r lg:border-white/[0.06] lg:bg-white/[0.02]">
        <Sidebar />
      </div>

      {/* Main Content Area */}
      <div className="relative flex flex-1 flex-col overflow-hidden">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_12%_8%,rgba(99,102,241,0.08),transparent_38%),radial-gradient(circle_at_88%_92%,rgba(148,163,184,0.06),transparent_34%)]" />
        <Topbar />
        
        <main className="relative z-10 flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6 lg:p-8 scroll-smooth pb-safe">
          <div className="relative mx-auto h-full w-full max-w-6xl">
             {children}
          </div>
        </main>
      </div>

      {/* Mobile Bottom Nav handles navigation on small screens. Inserted at layout level if needed, or in Sidebar. */}
    </div>
  );
}
