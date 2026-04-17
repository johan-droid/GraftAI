/**
 * Material Design 3 Bottom Navigation
 * 
 * Mobile-first navigation following M3 specification:
 * - 5 destinations max
 * - 80dp height container
 * - 32dp active indicator (pill-shaped)
 * - 12sp label typography
 * - 48dp touch targets minimum
 * 
 * @see https://m3.material.io/components/navigation-bar/overview
 */

'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Home, Calendar, Users, Settings, Plus, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTheme, type ThemeMode } from '@/contexts/ThemeContext';

// Navigation items configuration
const navItems = [
  { 
    id: 'home',
    icon: Home, 
    label: 'Home', 
    href: '/dashboard',
    badge: null 
  },
  { 
    id: 'calendar',
    icon: Calendar, 
    label: 'Calendar', 
    href: '/dashboard/calendar',
    badge: null 
  },
  { 
    id: 'create',
    icon: Plus, 
    label: 'Create', 
    href: '/dashboard/book',
    isAction: true,
    badge: null 
  },
  { 
    id: 'ai',
    icon: Sparkles, 
    label: 'AI', 
    href: '/dashboard/ai',
    badge: null 
  },
  { 
    id: 'settings',
    icon: Settings, 
    label: 'Settings', 
    href: '/dashboard/settings',
    badge: null 
  },
];

// M3 Motion tokens (cubic-bezier format for framer-motion)
const m3Motion = {
  standard: { duration: 0.15, ease: "easeOut" as const },
  emphasized: { duration: 0.3, ease: "easeInOut" as const },
};

export default function BottomNav() {
  const pathname = usePathname();
  const { mode } = useTheme();
  const isDark = mode === 'dark';
  const [pressedItem, setPressedItem] = useState<string | null>(null);

  // Get active item
  const activeItem = navItems.find(item => 
    pathname === item.href || pathname.startsWith(item.href + '/')
  ) || navItems[0];

  return (
    <motion.nav
      initial={{ y: 100 }}
      animate={{ y: 0 }}
      transition={m3Motion.emphasized}
      className="fixed bottom-0 left-0 right-0 z-40 lg:hidden"
      style={{
        // M3 Navigation Bar: 80dp height
        height: '80px',
      }}
    >
      {/* 
        M3 Surface Container Elevation Level 3
        Light: surfaceContainerHigh
        Dark: surfaceContainerHigh (adjusted for contrast)
      */}
      <div 
        className={`
          h-full px-2 pb-safe
          border-t
          ${isDark 
            ? 'bg-[#1C1B1F] border-[#49454F]' 
            : 'bg-[#E6E1E5] border-[#DEDBE0]'
          }
        `}
      >
        <div className="flex items-center justify-around h-full">
          {navItems.map((item) => {
            const isActive = activeItem.id === item.id;
            const isPressed = pressedItem === item.id;
            const Icon = item.icon;

            // M3 Action Button (FAB style) for Create
            if (item.isAction) {
              return (
                <motion.div
                  key={item.id}
                  className="relative -mt-4"
                >
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    onTapStart={() => setPressedItem(item.id)}
                    onTapCancel={() => setPressedItem(null)}
                    onTap={() => setPressedItem(null)}
                    onClick={() => window.location.href = item.href}
                    className={`
                      relative flex flex-col items-center justify-center
                      w-14 h-14 rounded-[16px]
                      shadow-lg
                      transition-shadow duration-150
                      ${isDark
                        ? 'bg-[#1A73E8] shadow-black/30'
                        : 'bg-[#1A73E8] shadow-blue-900/20'
                      }
                      ${isPressed ? 'shadow-md' : 'shadow-lg'}
                    `}
                    style={{
                      // M3 FAB elevation 3
                      boxShadow: isPressed 
                        ? '0 1px 3px 1px rgba(0,0,0,0.15)'
                        : '0 4px 8px 3px rgba(0,0,0,0.15)',
                    }}
                    aria-label={item.label}
                  >
                    <Icon 
                      className="w-6 h-6 text-white" 
                      strokeWidth={2}
                    />
                  </motion.button>
                  
                  {/* M3 Label: 12sp, medium weight */}
                  <span 
                    className={`
                      mt-1 text-[12px] font-medium
                      ${isDark ? 'text-[#C9C5CA]' : 'text-[#49454F]'}
                    `}
                  >
                    {item.label}
                  </span>
                </motion.div>
              );
            }

            return (
              <Link
                key={item.id}
                href={item.href}
                className="relative flex flex-col items-center justify-center flex-1 h-full"
                onTouchStart={() => setPressedItem(item.id)}
                onTouchEnd={() => setPressedItem(null)}
                aria-current={isActive ? 'page' : undefined}
              >
                <div className="relative flex flex-col items-center justify-center w-full h-full">
                  {/* 
                    M3 Active Indicator
                    - Height: 32dp
                    - Shape: Pill (50% radius)
                    - Container: primaryContainer (light) / primaryContainer (dark)
                  */}
                  <AnimatePresence>
                    {isActive && (
                      <motion.div
                        layoutId="bottomNavIndicator"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        transition={{ duration: 0.3, ease: "easeInOut" }}
                        className={`
                          absolute inset-x-4 top-1/2 -translate-y-1/2
                          h-8 rounded-full
                          ${isDark 
                            ? 'bg-[#004878]' // primaryContainer dark
                            : 'bg-[#E8F0FE]' // primaryContainer light
                          }
                        `}
                      />
                    )}
                  </AnimatePresence>

                  {/* Icon Container - 48dp touch target */}
                  <div 
                    className={`
                      relative z-10 flex items-center justify-center
                      w-12 h-12 rounded-full
                      transition-colors duration-150
                      ${isActive
                        ? isDark 
                          ? 'text-[#AAC7FF]' // onPrimaryContainer dark
                          : 'text-[#1967D2]' // onPrimaryContainer light
                        : isDark
                          ? 'text-[#C9C5CA]' // onSurfaceVariant dark
                          : 'text-[#49454F]' // onSurfaceVariant light
                      }
                    `}
                  >
                    <Icon 
                      className="w-6 h-6" 
                      strokeWidth={isActive ? 2 : 1.5}
                    />

                    {/* Badge indicator */}
                    {item.badge && (
                      <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-[#EA4335] text-[10px] font-medium text-white">
                        {item.badge}
                      </span>
                    )}
                  </div>

                  {/* 
                    M3 Label
                    - Font size: 12sp (12px)
                    - Weight: Medium (500)
                    - Active: onSurface
                    - Inactive: onSurfaceVariant
                  */}
                  <span 
                    className={`
                      mt-0.5 text-[12px] font-medium
                      transition-colors duration-150
                      ${isActive
                        ? isDark 
                          ? 'text-[#E6E1E5]' // onSurface dark
                          : 'text-[#1C1B1F]' // onSurface light
                        : isDark
                          ? 'text-[#938F99]' // onSurfaceVariant dark
                          : 'text-[#49454F]' // onSurfaceVariant light
                      }
                    `}
                  >
                    {item.label}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </motion.nav>
  );
}
