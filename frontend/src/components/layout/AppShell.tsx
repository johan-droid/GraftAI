/**
 * Material Design 3 Adaptive App Shell
 * 
 * Responsive layout that adapts navigation based on breakpoint:
 * - Mobile (< 600px): Bottom Navigation
 * - Tablet (600-839px): Navigation Rail
 * - Desktop (840px+): Navigation Drawer
 * 
 * Includes M3 touch targets, spacing, and color tokens.
 */

"use client";

import { useState } from "react";
import { useTheme } from "@/contexts/ThemeContext";
import BottomNav from "@/components/Mobile/BottomNav";
import NavRail from "@/components/navigation/NavRail";
import NavDrawer from "@/components/navigation/NavDrawer";
import { Topbar } from "./Topbar";
import { useBreakpoint, isCompact, isMobile, isTablet } from "@/theme/breakpoints";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const breakpoint = useBreakpoint();
  const { mode } = useTheme();
  const isDark = mode === "dark";
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // Determine navigation type based on breakpoint
  const showBottomNav = isCompact(breakpoint); // Mobile: < 600px
  const showNavRail = breakpoint === "medium"; // Tablet: 600-839px
  const showNavDrawer = !showBottomNav && !showNavRail; // Desktop: 840px+

  // Navigation width offsets for content
  const navOffset = showNavRail ? 80 : showNavDrawer ? 360 : 0;
  const bottomOffset = showBottomNav ? 80 : 0;

  return (
    <div 
      className={`
        flex min-h-dvh overflow-hidden
        ${isDark 
          ? "bg-[#141415] selection:bg-[#1967D2]/30 selection:text-[#AAC7FF]" 
          : "bg-[#F8F9FA] selection:bg-[#D2E3FC] selection:text-[#1967D2]"
        }
      `}
    >
      {/* Mobile: Bottom Navigation */}
      {showBottomNav && <BottomNav />}

      {/* Tablet: Navigation Rail */}
      {showNavRail && (
        <NavRail 
          onMenuClick={() => setIsDrawerOpen(true)}
        />
      )}

      {/* Desktop: Navigation Drawer */}
      {showNavDrawer && (
        <NavDrawer 
          isOpen={true}
          variant="standard"
          showHeader={true}
        />
      )}

      {/* Modal Drawer for mobile menu (when rail is shown) */}
      {showNavRail && (
        <NavDrawer
          isOpen={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
          variant="modal"
          showHeader={true}
        />
      )}

      {/* Main Content Area */}
      <div 
        className={`
          flex flex-col flex-1 min-w-0
          ${isDark ? "bg-[#141415]" : "bg-[#F2F2F4]"}
        `}
        style={{
          // Offset content based on navigation type
          marginLeft: `${navOffset}px`,
          marginBottom: `${bottomOffset}px`,
        }}
      >
        <Topbar 
          showMenuButton={showBottomNav}
          onMenuClick={() => setIsDrawerOpen(true)}
        />
        
        {/* 
          Main content with M3 spacing
          - Mobile: 16px margin
          - Tablet: 24px margin  
          - Desktop: 32px margin
        */}
        <main 
          className={`
            flex-1 overflow-y-auto
            ${isDark ? "bg-[#141415]" : "bg-[#F2F2F4]"}
            ${showBottomNav ? "compact:px-4" : ""}
            ${showNavRail ? "medium:px-6" : ""}
            ${showNavDrawer ? "expanded:px-8" : ""}
            pb-4
          `}
        >
          <div className="max-w-[1200px] mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
