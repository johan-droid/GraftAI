"use client";

import { useSession } from "next-auth/react";
import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { MobileSidebar } from "@/components/dashboard/MobileSidebar";
import { BottomNav } from "@/components/dashboard/BottomNav";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { AppLoadingScreen } from "@/components/ui/AppLoadingScreen";
import { getProfileSetupStatus } from "@/lib/api";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { status } = useSession();
  const router = useRouter();
  const pathname = usePathname();
  const hasPageMobileNav = pathname.startsWith("/dashboard/book");
  const [isCheckingOnboarding, setIsCheckingOnboarding] = useState(false);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push(`/login?callbackUrl=${encodeURIComponent(pathname)}`);
    }
  }, [status, router, pathname]);

  useEffect(() => {
    if (status !== "authenticated") {
      return;
    }

    let cancelled = false;

    const checkOnboarding = async () => {
      try {
        setIsCheckingOnboarding(true);
        const setupStatus = await getProfileSetupStatus();
        const hasCompletedInitialSetup = Boolean(
          setupStatus.profile_setup_completed || setupStatus.onboarding_completed
        );

        if (!cancelled && !hasCompletedInitialSetup && !pathname.startsWith("/profile/setup")) {
          router.replace("/profile/setup");
        }
      } catch (error) {
        console.error("Failed to verify profile setup status:", error);
      } finally {
        if (!cancelled) {
          setIsCheckingOnboarding(false);
        }
      }
    };

    void checkOnboarding();

    return () => {
      cancelled = true;
    };
  }, [status, pathname, router]);

  if (status === "loading" || isCheckingOnboarding) {
    return <AppLoadingScreen variant="dashboard" title="Preparing your dashboard" subtitle="Checking your session and onboarding status before rendering live data." />;
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
