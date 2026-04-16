// frontend/src/app/(public)/layout.tsx

import { ReactNode } from "react";
import Link from "next/link";
import { ShieldCheck } from "lucide-react";

export default function PublicBookingLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[#F8F9FA] flex flex-col font-sans selection:bg-[#D2E3FC]">
      {/* Ultra-minimal Header */}
      <header className="py-6 px-4 sm:px-6 flex justify-center">
        <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <div className="w-6 h-6 rounded-md bg-[#1A73E8] flex items-center justify-center text-white font-bold text-xs">
            G
          </div>
          <span className="font-medium tracking-tight text-[#202124]">GraftAI</span>
        </Link>
      </header>

      {/* Main Booking Content */}
      <main className="flex-1 flex flex-col items-center px-4 sm:px-6 pb-12">
        <div className="w-full max-w-4xl">
          {children}
        </div>
      </main>

      {/* Trust Footer */}
      <footer className="py-6 text-center text-xs text-[#5F6368] flex items-center justify-center gap-4">
        <span>Powered by GraftAI</span>
        <div className="w-1 h-1 rounded-full bg-[#DADCE0]"></div>
        <Link href="/terms" className="hover:text-[#202124] transition-colors">Report Abuse</Link>
        <div className="w-1 h-1 rounded-full bg-[#DADCE0]"></div>
        <span className="flex items-center gap-1"><ShieldCheck size={12} /> Secure Booking</span>
      </footer>
    </div>
  );
}
