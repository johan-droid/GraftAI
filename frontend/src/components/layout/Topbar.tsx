/**
 * Material Design 3 Top App Bar
 * 
 * Responsive header with:
 * - Optional menu button for mobile
 * - Search functionality
 * - Action icons
 * - User profile
 * 
 * @see https://m3.material.io/components/top-app-bar/overview
 */

"use client";

import { useSession, signOut } from "next-auth/react";
import Link from "next/link";
import { Bell, Search, MessageSquare, Menu } from "lucide-react";
import { motion } from "framer-motion";
import { useTheme } from "@/contexts/ThemeContext";

interface TopbarProps {
  showMenuButton?: boolean;
  onMenuClick?: () => void;
}

export function Topbar({ showMenuButton = false, onMenuClick }: TopbarProps) {
  const { data: session } = useSession();
  const { mode } = useTheme();
  const isDark = mode === "dark";
  
  const firstInitial = session?.user?.name?.charAt(0).toUpperCase() || "U";

  return (
    <header 
      className={`
        h-16 border-b flex items-center justify-between px-4 sm:px-6 sticky top-0 z-40
        ${isDark 
          ? "bg-[#1C1B1F] border-[#49454F]" 
          : "bg-[#FFFFFF] border-[#DADCE0]"
        }
      `}
    >
      
      <div className="flex items-center gap-4 flex-1">
        {/* Menu button for mobile */}
        {showMenuButton && onMenuClick && (
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={onMenuClick}
            className={`
              w-10 h-10 rounded-full
              flex items-center justify-center
              transition-colors duration-150
              ${isDark
                ? "hover:bg-[#49454F] text-[#E6E1E5]"
                : "hover:bg-[#F1F3F4] text-[#5F6368]"
              }
            `}
            aria-label="Open menu"
          >
            <Menu size={24} />
          </motion.button>
        )}
        
        {/* Search bar - hidden on mobile */}
        <div className={`
          hidden sm:flex items-center 
          px-4 py-2.5 rounded-full w-full max-w-md 
          transition-all
          ${isDark
            ? "bg-[#49454F] focus-within:bg-[#605D66] focus-within:ring-1 focus-within:ring-[#AAC7FF]"
            : "bg-[#F1F3F4] focus-within:bg-white focus-within:shadow-sm focus-within:ring-1 focus-within:ring-[#1A73E8]"
          }
        `}>
          <Search size={18} className={isDark ? "text-[#C9C5CA]" : "text-[#5F6368]"} />
          <input 
            type="text" 
            placeholder="Search events, bookings, or settings..." 
            className={`
              bg-transparent border-none outline-none text-sm ml-3 w-full
              placeholder:text-sm
              ${isDark 
                ? "text-[#E6E1E5] placeholder:text-[#C9C5CA]" 
                : "text-[#202124] placeholder:text-[#5F6368]"
              }
            `}
          />
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2 sm:gap-4 ml-4">
        {/* AI Copilot button */}
        <Link
          href="/copilot"
          className={`
            inline-flex items-center gap-2 rounded-full border px-3 py-2
            transition-colors
            ${isDark
              ? "border-[#49454F] bg-[#1C1B1F] text-[#C9C5CA] hover:border-[#AAC7FF] hover:text-[#AAC7FF]"
              : "border-[#DADCE0] bg-white text-[#5F6368] hover:border-[#1A73E8] hover:text-[#1A73E8]"
            }
          `}
          aria-label="Open AI Copilot"
          title="Open AI Copilot"
        >
          <MessageSquare size={16} />
          <span className="hidden sm:inline text-[10px] font-bold uppercase tracking-[0.18em]">
            AI Copilot
          </span>
        </Link>

        {/* Notifications button */}
        <button 
          aria-label="Notifications" 
          title="Notifications" 
          className={`
            p-2 rounded-full transition-colors relative
            ${isDark 
              ? "hover:bg-[#49454F] text-[#C9C5CA]" 
              : "hover:bg-[#F1F3F4] text-[#5F6368]"
            }
          `}
        >
          <Bell size={20} />
          <span className="absolute top-2 right-2 w-2 h-2 bg-[#D93025] rounded-full border-2 border-white"></span>
        </button>

        {/* Divider */}
        <div className={`h-6 w-px mx-1 ${isDark ? "bg-[#49454F]" : "bg-[#DADCE0]"}`}></div>

        {/* User profile */}
        <div className="flex items-center gap-3 pl-1">
          <div className="hidden sm:block text-right">
            <p className={`text-sm font-medium leading-tight ${isDark ? "text-[#E6E1E5]" : "text-[#202124]"}`}>
              {session?.user?.name || "Loading..."}
            </p>
            <p className={`text-[11px] ${isDark ? "text-[#938F99]" : "text-[#5F6368]"}`}>
              {session?.user?.email || "Please wait"}
            </p>
          </div>
          
          <button 
            onClick={() => signOut({ callbackUrl: '/login' })}
            title="Sign out"
            className="w-9 h-9 rounded-full bg-[#1A73E8] text-white flex items-center justify-center font-medium text-sm hover:ring-2 hover:ring-offset-2 hover:ring-[#1A73E8] transition-all cursor-pointer shadow-sm"
          >
            {firstInitial}
          </button>
        </div>
      </div>
    </header>
  );
}
