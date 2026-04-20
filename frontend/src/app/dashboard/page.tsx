/**
 * Mobile-Responsive Dashboard Page
 * 
 * Following Material Design 3 principles:
 * - Responsive grid layouts (4 cols mobile, 8 cols tablet, 12 cols desktop)
 * - Touch-friendly cards with 48dp minimum targets
 * - Adaptive typography scaling
 * - Horizontal scroll for stats on mobile
 * - Card-based list for meetings
 * 
 * @see https://m3.material.io/foundations/layout
 */

"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { Calendar, Link as LinkIcon, Plus, Inbox, Clock, ArrowRight } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { toast } from "@/components/ui/Toast";
import { getAnalyticsSummary } from "@/lib/api";
import { useTheme } from "@/contexts/ThemeContext";
import { BentoLayout } from "@/components/ui/BentoLayout";
import { BentoItem } from "@/components/ui/BentoItem";

type SessionUser = {
  bookingSlug?: string;
  booking_slug?: string;
  name?: string;
};

type DashboardSummaryResponse = Awaited<ReturnType<typeof getAnalyticsSummary>>;

// M3 Motion tokens
const m3Motion = {
  standard: { duration: 0.15, ease: "easeOut" as const },
  emphasized: { duration: 0.3, ease: "easeInOut" as const },
};

export default function DashboardPage() {
  const { data: session } = useSession();
  const user = session?.user as SessionUser | undefined;
  const { mode } = useTheme();
  const isDark = mode === "dark";
  const [isLoading, setIsLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState<DashboardSummaryResponse | null>(null);
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
        const response = await getAnalyticsSummary("7d");
        setDashboardData(response);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
        toast.error("Failed to load dashboard data. Please try again.");
        setDashboardData(null);
      } finally {
        setIsLoading(false);
      }
    }
    fetchDashboard();
  }, []);

  const handleCopyBookingLink = async () => {
    const slug = user?.bookingSlug ?? user?.booking_slug;

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
  const recentEvents = dashboardData?.details?.recent_events ?? [];
  const nextEvent = dashboardData?.details?.next_event ?? recentEvents[0] ?? null;


  if (isLoading) {
    return (
      <div className="p-4 sm:p-6 md:p-8 max-w-6xl mx-auto space-y-6 sm:space-y-8 w-full animate-pulse">
        {/* Skeleton banner */}
        <div className={`h-32 sm:h-40 rounded-3xl w-full mb-10 ${isDark ? "bg-[#49454F]" : "bg-[#F1F3F4]"}`}></div>
        {/* Skeleton stats - horizontal scroll on mobile */}
        <div className="flex gap-4 overflow-x-auto pb-2 -mx-4 px-4 sm:mx-0 sm:px-0 sm:grid sm:grid-cols-2 lg:grid-cols-4">
          <div className={`min-w-[140px] h-28 sm:h-32 rounded-2xl ${isDark ? "bg-[#49454F]" : "bg-[#F1F3F4]"}`}></div>
          <div className={`min-w-[140px] h-28 sm:h-32 rounded-2xl ${isDark ? "bg-[#49454F]" : "bg-[#F1F3F4]"}`}></div>
          <div className={`min-w-[140px] h-28 sm:h-32 rounded-2xl ${isDark ? "bg-[#49454F]" : "bg-[#F1F3F4]"}`}></div>
          <div className={`min-w-[140px] h-28 sm:h-32 rounded-2xl ${isDark ? "bg-[#49454F]" : "bg-[#F1F3F4]"}`}></div>
        </div>
        {/* Skeleton actions */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className={`h-40 sm:h-48 rounded-2xl ${isDark ? "bg-[#49454F]" : "bg-[#F1F3F4]"}`}></div>
          <div className={`h-40 sm:h-48 rounded-2xl ${isDark ? "bg-[#49454F]" : "bg-[#F1F3F4]"}`}></div>
          <div className={`h-40 sm:h-48 rounded-2xl ${isDark ? "bg-[#49454F]" : "bg-[#F1F3F4]"}`}></div>
        </div>
        {/* Skeleton meetings */}
        <div className={`h-64 rounded-2xl mt-8 ${isDark ? "bg-[#49454F]" : "bg-[#F1F3F4]"}`}></div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 md:p-8 max-w-6xl mx-auto w-full space-y-6 sm:space-y-8">
      
      {/* WELCOME BANNER - M3 Hero section */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={m3Motion.emphasized}
        className="relative overflow-hidden bg-[#1A73E8] rounded-3xl p-6 sm:p-8 md:p-10 shadow-md"
      >
        {/* Decorative background elements */}
        <div className="absolute top-0 right-0 -mt-8 sm:-mt-16 -mr-8 sm:-mr-16 w-32 sm:w-64 h-32 sm:h-64 bg-white opacity-10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-16 sm:right-32 -mb-8 sm:-mb-16 w-24 sm:w-48 h-24 sm:h-48 bg-[#8AB4F8] opacity-20 rounded-full blur-2xl"></div>
        
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-end justify-between gap-4 sm:gap-6">
          <div className="flex-1 min-w-0">
            {/* Clock - hidden on smallest screens, show on sm+ */}
            <div className="hidden sm:flex items-center gap-2 text-[#E8F0FE] mb-2 text-sm font-medium tracking-wide uppercase">
              <Clock size={16} />
              <time suppressHydrationWarning>
                {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </time>
            </div>
            
            {/* Greeting - responsive text size */}
            <h1 className="text-2xl sm:text-3xl md:text-5xl font-medium text-white tracking-tight leading-tight">
              {greeting},<br className="hidden sm:block" />
              <span className="sm:hidden"> </span>{userName}.
            </h1>
            
            {/* Summary - truncate on mobile */}
            {dashboardData?.summary ? (
              <p className="mt-3 sm:mt-4 max-w-2xl text-sm sm:text-base leading-relaxed text-[#E8F0FE] line-clamp-2 sm:line-clamp-none">
                {dashboardData.summary}
              </p>
            ) : (
              <p className="mt-3 sm:mt-4 max-w-2xl text-sm sm:text-base leading-relaxed text-[#E8F0FE] line-clamp-2 sm:line-clamp-none">
                Your dashboard is now pulling live data from the backend.
              </p>
            )}
          </div>
          
          {/* CTA Button - full width on mobile */}
          <div className="flex-shrink-0 sm:flex-none w-full sm:w-auto mt-2 sm:mt-0">
             <Link 
               href="/dashboard/event-types" 
               className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-white text-[#1A73E8] hover:bg-[#F8F9FA] px-6 py-3 rounded-full font-medium text-sm transition-colors shadow-sm"
             >
               <Plus size={18} />
               <span>Create Event</span>
             </Link>
          </div>
        </div>
      </motion.div>

      {/* STATS CARDS - Horizontal scroll on mobile, grid on desktop */}
      {dashboardData?.details ? (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...m3Motion.emphasized, delay: 0.1 }}
          className="flex gap-3 sm:gap-4 overflow-x-auto pb-2 -mx-4 px-4 sm:mx-0 sm:px-0 sm:grid sm:grid-cols-2 lg:grid-cols-4 scrollbar-hide"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          <StatCard 
            label="Meetings this week" 
            value={dashboardData.details.meetings} 
            isDark={isDark}
          />
          <StatCard 
            label="Scheduled hours" 
            value={dashboardData.details.hours.toFixed(1)} 
            isDark={isDark}
          />
          <StatCard 
            label="Week growth" 
            value={`${dashboardData.details.growth}%`} 
            isDark={isDark}
          />
          <StatCard 
            label="Cancellations" 
            value={dashboardData.details.cancellations ?? 0} 
            isDark={isDark}
          />
        </motion.div>
      ) : null}

      {/* Hide scrollbar for horizontal scroll */}
      <style jsx>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>

      {/* QUICK ACTIONS GRID - Responsive for mobile */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ ...m3Motion.emphasized, delay: 0.2 }}
      >
        <BentoLayout className="gap-4 sm:gap-5">
          <BentoItem>
            <QuickActionCard
              icon={LinkIcon}
              label="Copy Link"
              description="Share your default booking page"
              actionText="Copy to clipboard"
              color="blue"
              isDark={isDark}
              onClick={handleCopyBookingLink}
            />
          </BentoItem>

          <BentoItem>
            <QuickActionCard
              icon={Calendar}
              label="My Calendar"
              description="View and manage your schedule"
              actionText="Open calendar"
              color="orange"
              isDark={isDark}
              href="/dashboard/calendar"
            />
          </BentoItem>

          <BentoItem>
            <QuickActionCard
              icon={Inbox}
              label="Integrations"
              description="Connect Zoom, Google Meet & more"
              actionText="Manage apps"
              color="green"
              isDark={isDark}
              href="/integrations"
            />
          </BentoItem>
        </BentoLayout>
      </motion.div>

      {/* UPCOMING MEETINGS WIDGET - M3 Card */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ ...m3Motion.emphasized, delay: 0.3 }}
        className={`
          rounded-2xl p-4 sm:p-6 md:p-8 shadow-sm
          ${isDark 
            ? "bg-[#1C1B1F] border border-[#49454F]" 
            : "bg-white border border-[#DADCE0]"
          }
        `}
      >
        <div className={`
          flex flex-col sm:flex-row sm:items-center sm:justify-between 
          mb-6 sm:mb-8 pb-4 
          ${isDark ? "border-b border-[#49454F]" : "border-b border-[#F1F3F4]"}
        `}>
          <div className="mb-3 sm:mb-0">
            <h2 className={`text-lg sm:text-xl font-semibold ${isDark ? "text-[#E6E1E5]" : "text-[#202124]"}`}>
              Upcoming Meetings
            </h2>
            <p className={`text-sm mt-1 ${isDark ? "text-[#938F99]" : "text-[#5F6368]"}`}>
              Your schedule for the next 7 days
            </p>
          </div>
          <Link 
            href="/dashboard/calendar" 
            className={`
              text-sm font-medium px-4 py-2 rounded-full transition-colors
              ${isDark 
                ? "text-[#AAC7FF] hover:bg-[#004878]" 
                : "text-[#1A73E8] hover:bg-[#E8F0FE]"
              }
            `}
          >
            View all
          </Link>
        </div>

        {recentEvents.length > 0 || nextEvent ? (
          <div className="space-y-3 sm:space-y-4">
             {recentEvents.map((event) => (
               <div 
                 key={event.id} 
                 className={`
                   flex flex-col sm:flex-row sm:items-center sm:justify-between 
                   gap-2 sm:gap-4 rounded-2xl p-4
                   ${isDark 
                     ? "border border-[#49454F] bg-[#141415]" 
                     : "border border-[#DADCE0] bg-[#F8F9FA]"
                   }
                 `}
               >
                 <div className="min-w-0">
                   <p className={`font-semibold truncate ${isDark ? "text-[#E6E1E5]" : "text-[#202124]"}`}>
                     {event.title}
                   </p>
                   <p className={`text-sm ${isDark ? "text-[#938F99]" : "text-[#5F6368]"}`}>
                     {new Date(event.start_time).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                   </p>
                 </div>
                 <span className={`
                   self-start sm:self-auto
                   text-xs font-semibold uppercase tracking-wider 
                   ${isDark ? "text-[#AAC7FF]" : "text-[#1A73E8]"}
                 `}>
                   {event.category ?? "event"}
                 </span>
               </div>
             ))}

             {!recentEvents.length && nextEvent ? (
               <div className={`
                 rounded-2xl p-4
                 ${isDark 
                   ? "border border-[#49454F] bg-[#141415]" 
                   : "border border-[#DADCE0] bg-[#F8F9FA]"
                 }
               `}>
                 <p className={`font-semibold ${isDark ? "text-[#E6E1E5]" : "text-[#202124]"}`}>
                   {nextEvent.title}
                 </p>
                 <p className={`text-sm mt-1 ${isDark ? "text-[#938F99]" : "text-[#5F6368]"}`}>
                   {new Date(nextEvent.start_time).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                 </p>
               </div>
             ) : null}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 sm:py-16 text-center">
            <div className={`
              w-16 h-16 sm:w-20 sm:h-20 rounded-full 
              flex items-center justify-center mb-4 sm:mb-5
              ${isDark ? "bg-[#49454F] text-[#938F99]" : "bg-[#F8F9FA] text-[#DADCE0]"}
            `}>
              <Calendar size={32} strokeWidth={1.5} className="sm:w-10 sm:h-10" />
            </div>
            <h3 className={`text-lg font-semibold mb-2 ${isDark ? "text-[#E6E1E5]" : "text-[#202124]"}`}>
              Your calendar is clear
            </h3>
            <p className={`text-sm sm:text-base max-w-sm mx-auto ${isDark ? "text-[#938F99]" : "text-[#5F6368]"}`}>
              You do not have any upcoming meetings scheduled. Share your link to get booked!
            </p>
          </div>
        )}
      </motion.div>
    </div>
  );
}

// M3 Quick Action Card Component
interface QuickActionCardProps {
  icon: React.ElementType;
  label: string;
  description: string;
  actionText: string;
  color: 'blue' | 'orange' | 'green';
  isDark: boolean;
  onClick?: () => void;
  href?: string;
}

function QuickActionCard({ 
  icon: Icon, 
  label, 
  description, 
  actionText, 
  color,
  isDark,
  onClick,
  href 
}: QuickActionCardProps) {
  const colorStyles = {
    blue: {
      light: { bg: "bg-[#E8F0FE]", text: "text-[#1A73E8]", hover: "hover:border-[#1A73E8]" },
      dark: { bg: "bg-[#004878]", text: "text-[#AAC7FF]", hover: "hover:border-[#AAC7FF]" }
    },
    orange: {
      light: { bg: "bg-[#FEF7E0]", text: "text-[#E37400]", hover: "hover:border-[#E37400]" },
      dark: { bg: "bg-[#5C3B00]", text: "text-[#FFC56D]", hover: "hover:border-[#FFC56D]" }
    },
    green: {
      light: { bg: "bg-[#E6F4EA]", text: "text-[#137333]", hover: "hover:border-[#137333]" },
      dark: { bg: "bg-[#1E4C30]", text: "text-[#84D9A6]", hover: "hover:border-[#84D9A6]" }
    }
  };

  const styles = colorStyles[color][isDark ? 'dark' : 'light'];

  const cardContent = (
    <>
      <div className={`
        w-12 h-12 rounded-full 
        flex items-center justify-center mb-4 sm:mb-5
        ${styles.bg} ${styles.text}
        group-hover:scale-110 transition-transform
      `}>
        <Icon size={22} />
      </div>
      <span className={`font-semibold text-lg mb-1 ${isDark ? "text-[#E6E1E5]" : "text-[#202124]"}`}>
        {label}
      </span>
      <span className={`text-sm mb-4 ${isDark ? "text-[#938F99]" : "text-[#5F6368]"}`}>
        {description}
      </span>
      <div className={`mt-auto flex items-center text-sm font-medium ${styles.text}`}>
        {actionText} 
        <ArrowRight size={16} className="ml-1 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
      </div>
    </>
  );

  const cardClassName = `
    group flex flex-col items-start p-5 sm:p-6
    rounded-2xl transition-all text-left w-full
    ${isDark 
      ? `bg-[#1C1B1F] border border-[#49454F] ${styles.hover}` 
      : `bg-white border border-[#DADCE0] ${styles.hover}`
    }
    hover:shadow-md
  `;

  if (href) {
    return (
      <Link href={href} className={cardClassName}>
        {cardContent}
      </Link>
    );
  }

  return (
    <button onClick={onClick} className={cardClassName}>
      {cardContent}
    </button>
  );
}

// M3 Stat Card Component
function StatCard({ label, value, isDark }: { label: string; value: string | number; isDark: boolean }) {
  return (
    <div 
      className={`
        min-w-[140px] sm:min-w-0 flex-1
        rounded-2xl p-5 shadow-sm
        transition-all duration-150
        ${isDark 
          ? "bg-[#1C1B1F] border border-[#49454F]" 
          : "bg-white border border-[#DADCE0]"
        }
      `}
    >
      <p className={`
        text-xs font-semibold uppercase tracking-wider
        ${isDark ? "text-[#938F99]" : "text-[#5F6368]"}
      `}>
        {label}
      </p>
      <p className={`
        mt-3 text-3xl font-semibold
        ${isDark ? "text-[#E6E1E5]" : "text-[#202124]"}
      `}>
        {value}
      </p>
    </div>
  );
}
