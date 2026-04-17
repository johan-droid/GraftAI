"use client";

import { useSession } from "next-auth/react";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";
import { Loader2 } from "lucide-react";
import { MobileSidebar } from "@/components/dashboard/MobileSidebar";
import { BottomNav } from "@/components/dashboard/BottomNav";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { status } = useSession();
  const router = useRouter();
  const pathname = usePathname();
  const hasPageMobileNav = pathname.startsWith("/dashboard/book");

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push(`/login?callbackUrl=${encodeURIComponent(pathname)}`);
    }
  }, [status, router, pathname]);

  if (status === "loading") {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-[#F8F9FA]">
        <Loader2 className="h-8 w-8 animate-spin text-[#1A73E8]" />
      </div>
    );
  }

  if (status === "authenticated") {
    return (
      <div className="flex min-h-dvh bg-white overflow-hidden selection:bg-[#D2E3FC] selection:text-[#1967D2]">
        {!hasPageMobileNav && <MobileSidebar />}
        <Sidebar />
        <div className="flex flex-col flex-1 min-w-0 bg-[#F8F9FA]">
          <Topbar />
          <main className="flex-1 overflow-y-auto relative pb-20 md:pb-0">
            {children}
          </main>
        </div>
        {!hasPageMobileNav && <BottomNav />}
      </div>
    );
  }

  return null;
}
