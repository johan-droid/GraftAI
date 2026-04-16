"use client";

import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-white overflow-hidden selection:bg-[#D2E3FC] selection:text-[#1967D2]">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0 bg-[#F8F9FA]">
        <Topbar />
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
