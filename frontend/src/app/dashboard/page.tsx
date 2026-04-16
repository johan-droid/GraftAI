"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { Calendar, Link as LinkIcon, Plus, Inbox, Clock, ArrowRight } from "lucide-react";
import Link from "next/link";
import { toast } from "@/components/ui/Toast";

export default function DashboardPage() {
  const { data: session } = useSession();
  const [isLoading, setIsLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [currentTime, setCurrentTime] = useState(new Date());

  // 1. Live Clock Timer
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // 2. Fetch Dashboard Data
  useEffect(() => {
    async function fetchDashboard() {
      try {
        setIsLoading(true);
        // TODO: Swap with actual backend endpoint
        // const response = await apiClient.get('/dashboard/summary');
        // keep a small artificial delay to show loading skeletons
        await new Promise((resolve) => setTimeout(resolve, 600));
        setDashboardData({ upcomingEvents: [] });
        setIsLoading(false);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
        toast.error("Failed to load dashboard data. Please try again.");
        setIsLoading(false);
      }
    }
    fetchDashboard();
  }, []);

  const handleCopyBookingLink = async () => {
    const slug =
      (session as any)?.user?.bookingSlug ??
      (session as any)?.user?.booking_slug ??
      dashboardData?.bookingSlug ??
      dashboardData?.user?.bookingSlug;

    if (!slug) {
      toast.error("No booking link configured for your account.");
      return;
    }

    const origin = typeof window !== "undefined" ? window.location.origin : "https://graftai.com";
    const url = `${origin}/${encodeURIComponent(String(slug))}`;

    try {
      await navigator.clipboard.writeText(url);
      toast.success("Booking link copied to clipboard!");
    } catch (err) {
      console.error("Failed to copy booking link:", err);
      toast.error("Failed to copy booking link. Please copy manually.");
    }
  };

  // Dynamic Greeting Logic
  const currentHour = currentTime.getHours();
  let greeting = "Good evening";
  if (currentHour < 12) greeting = "Good morning";
  else if (currentHour < 17) greeting = "Good afternoon";

  // Extract First Name securely
  const userName = session?.user?.name?.split(' ')[0] || "there";

  if (isLoading) {
    return (
      <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-8 w-full animate-pulse">
        <div className="h-40 bg-[#F1F3F4] rounded-3xl w-full mb-10"></div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="h-36 bg-[#F1F3F4] rounded-2xl"></div>
          <div className="h-36 bg-[#F1F3F4] rounded-2xl"></div>
          <div className="h-36 bg-[#F1F3F4] rounded-2xl"></div>
        </div>
        <div className="h-64 bg-[#F1F3F4] rounded-2xl mt-8"></div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto w-full space-y-8">
      
      {/* BOLDER WELCOME BANNER */}
      <div className="relative overflow-hidden bg-[#1A73E8] rounded-3xl p-8 md:p-10 shadow-md">
        {/* Decorative background elements for that "SaaS pop" */}
        <div className="absolute top-0 right-0 -mt-16 -mr-16 w-64 h-64 bg-white opacity-10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-32 -mb-16 w-48 h-48 bg-[#8AB4F8] opacity-20 rounded-full blur-2xl"></div>
        
        <div className="relative z-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 text-[#E8F0FE] mb-2 text-sm font-medium tracking-wide uppercase">
              <Clock size={16} />
              <time suppressHydrationWarning>
                {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </time>
            </div>
            <h1 className="text-3xl md:text-5xl font-medium text-white tracking-tight leading-tight">
              {greeting},<br />{userName}.
            </h1>
          </div>
          
          <div className="flex items-center gap-3">
             <Link 
               href="/dashboard/event-types" 
               className="bg-white text-[#1A73E8] hover:bg-[#F8F9FA] px-6 py-3 rounded-full font-medium text-sm transition-colors shadow-sm flex items-center gap-2"
             >
               <Plus size={18} />
               Create Event
             </Link>
          </div>
        </div>
      </div>

      {/* QUICK ACTIONS GRID */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <button 
          onClick={handleCopyBookingLink}
          className="group flex flex-col items-start p-6 bg-white border border-[#DADCE0] rounded-2xl hover:border-[#1A73E8] hover:shadow-md transition-all text-left"
        >
          <div className="w-12 h-12 rounded-full bg-[#E8F0FE] text-[#1A73E8] flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
            <LinkIcon size={22} />
          </div>
          <span className="font-semibold text-[#202124] text-lg mb-1">Copy Link</span>
          <span className="text-sm text-[#5F6368] mb-4">Share your default booking page</span>
          <div className="mt-auto flex items-center text-sm font-medium text-[#1A73E8]">
            Copy to clipboard <ArrowRight size={16} className="ml-1 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
          </div>
        </button>

        <Link href="/dashboard/calendar" className="group flex flex-col items-start p-6 bg-white border border-[#DADCE0] rounded-2xl hover:border-[#E37400] hover:shadow-md transition-all">
          <div className="w-12 h-12 rounded-full bg-[#FEF7E0] text-[#E37400] flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
            <Calendar size={22} />
          </div>
          <span className="font-semibold text-[#202124] text-lg mb-1">My Calendar</span>
          <span className="text-sm text-[#5F6368] mb-4">View and manage your schedule</span>
          <div className="mt-auto flex items-center text-sm font-medium text-[#E37400]">
            Open calendar <ArrowRight size={16} className="ml-1 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
          </div>
        </Link>

        <Link href="/dashboard/settings/integrations" className="group flex flex-col items-start p-6 bg-white border border-[#DADCE0] rounded-2xl hover:border-[#137333] hover:shadow-md transition-all">
          <div className="w-12 h-12 rounded-full bg-[#E6F4EA] text-[#137333] flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
            <Inbox size={22} />
          </div>
          <span className="font-semibold text-[#202124] text-lg mb-1">Integrations</span>
          <span className="text-sm text-[#5F6368] mb-4">Connect Zoom, Google Meet & more</span>
          <div className="mt-auto flex items-center text-sm font-medium text-[#137333]">
            Manage apps <ArrowRight size={16} className="ml-1 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
          </div>
        </Link>
      </div>

      {/* UPCOMING MEETINGS WIDGET */}
      <div className="bg-white border border-[#DADCE0] rounded-2xl p-6 md:p-8 shadow-sm">
        <div className="flex items-center justify-between mb-8 pb-4 border-b border-[#F1F3F4]">
          <div>
            <h2 className="text-xl font-semibold text-[#202124]">Upcoming Meetings</h2>
            <p className="text-sm text-[#5F6368] mt-1">Your schedule for the next 7 days</p>
          </div>
          <Link href="/dashboard/calendar" className="text-sm font-medium text-[#1A73E8] hover:bg-[#E8F0FE] px-4 py-2 rounded-full transition-colors">
            View all
          </Link>
        </div>

        {dashboardData?.upcomingEvents?.length > 0 ? (
          <div className="space-y-4">
             {/* Map events here */}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-20 h-20 rounded-full bg-[#F8F9FA] flex items-center justify-center text-[#DADCE0] mb-5">
              <Calendar size={40} strokeWidth={1.5} />
            </div>
            <h3 className="text-lg font-semibold text-[#202124] mb-2">Your calendar is clear</h3>
            <p className="text-base text-[#5F6368] max-w-sm mx-auto">
              You do not have any upcoming meetings scheduled. Share your link to get booked!
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
