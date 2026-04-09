"use client";

import React, { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="flex h-[100dvh] w-full overflow-hidden bg-[#070711] text-slate-200">
      {/* Desktop Sidebar */}
      <div className="hidden lg:flex lg:w-72 lg:flex-col lg:border-r lg:border-white/[0.05]">
        <Sidebar />
      </div>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden relative">
        <Topbar />
        
        <main className="flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6 lg:p-8 scroll-smooth pb-safe">
          <div className="mx-auto max-w-6xl w-full h-full relative">
             {children}
          </div>
        </main>
      </div>

      {/* Mobile Bottom Nav handles navigation on small screens. Inserted at layout level if needed, or in Sidebar. */}
    </div>
  );
}
